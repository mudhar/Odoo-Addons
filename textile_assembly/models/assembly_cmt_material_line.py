from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError
from odoo.tools import profile


class AssemblyCmtMaterialLine(models.Model):
    _name = 'assembly.cmt.material.line'
    _description = 'Assembly CMT Material Line'
    _order = 'assembly_id, sequence, id'
    _rec_name = 'product_id'

    assembly_id = fields.Many2one(comodel_name="assembly.production", string="Assembly Order",
                                  ondelete='cascade', index=True)
    sequence = fields.Integer(string='Seq', default=1)

    product_id = fields.Many2one(comodel_name="product.product", string="Products",
                                 track_visibility='onchange',  domain=[('type', 'in', ['product', 'consu'])])
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM", required=True)
    product_qty = fields.Float(string="Quantity Per Pcs", digits=dp.get_precision('Product Unit of Measure'),
                               default=1.0)
    qty_final = fields.Float(string="Quantity", digits=dp.get_precision('Product Unit of Measure'),
                             compute="_compute_qty_final")
    price_unit = fields.Float(string="Unit Price", digits=dp.get_precision('Product Price'),
                              default=0.0)
    price_subtotal = fields.Float(string="Sub Total", digits=dp.get_precision('Account'),
                                  compute="_compute_price_subtotal")
    total_ratio = fields.Float(string="Amount Ratio", compute="_compute_ratio")
    ratio = fields.Float(string="Ratio Of")
    state = fields.Selection(string="Status", related="assembly_id.state")

    @api.multi
    @api.depends('product_qty',
                 'ratio')
    def _compute_qty_final(self):
        for cmt in self:
            cmt.qty_final = cmt.product_qty * cmt.ratio

    @api.depends('assembly_id.variant_line_ids',
                 'assembly_id.variant_line_ids.ratio')
    def _compute_ratio(self):
        for order in self:
            variant = order.assembly_id
            variants = variant.variant_line_ids.mapped('ratio')
            total = sum(variants)
            order.total_ratio = total
        return True

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.product_uom_id = self.product_id.uom_id.id
        self.price_unit = self.product_id.product_tmpl_id.standard_price

        return {'domain': {'product_uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}

    @api.onchange('product_uom_id')
    def onchange_product_uom_id(self):
        if self.product_uom_id.category_id.id != self.product_id.uom_id.category_id.id:
            raise UserError(_("Kategori UoM Tidak Sama Dengan Kategori UoM Produk"))

    @api.multi
    @api.depends('price_unit', 'qty_final')
    def _compute_price_subtotal(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        for line in self:
            line.price_subtotal = line.qty_final * line.price_unit

    def generate_assembly_plan_cmt_material(self, plan_id):
        plan_cmt_materials = self.env['assembly.plan.cmt.material']
        done = self.env['assembly.plan.cmt.material'].browse()
        for line in self:
            for val in line.prepare_assembly_plan_cmt_material(plan_id):
                done += plan_cmt_materials.create(val)
        return done

    @api.multi
    def prepare_assembly_plan_cmt_material(self, plan_id):
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        values = {
            'plan_id': plan_id.id,
            'product_id': self.product_id.id,
            'product_qty': self.product_qty,
            'product_uom_id': self.product_uom_id.id,
            'price_unit': self.price_unit,
            'ratio': self.total_ratio
        }
        res.append(values)
        return res

    def action_create_bom_line(self, bom_id):
        bom_lines = self.env['mrp.bom.line']
        done = self.env['mrp.bom.line'].browse()
        for line in self:
            for val in line.prepare_bom_line(bom_id):
                done += bom_lines.create(val)
        return done

    @api.multi
    def prepare_bom_line(self, bom_id):
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        values = {
            'bom_id': bom_id.id,
            'product_uom_id': self.product_uom_id.id,
            'product_id': self.product_id.id,
            'product_qty': self.product_qty,
            'sequence': self.sequence,
        }
        res.append(values)
        return res


class AssemblyCmtProductTemplate(models.Model):
    _name = 'assembly.cmt.product.template'
    _rec_name = 'product_id'
    _order = 'assembly_id, sequence, id'
    _description = 'Assembly Template Product Aksesoris'

    assembly_id = fields.Many2one(comodel_name="assembly.production", string="Assembly Order",
                                  ondelete='cascade', index=True)
    sequence = fields.Integer(string='Seq', default=1)
    product_id = fields.Many2one(comodel_name="product.template", string="Products", index=True,
                                 track_visibility='onchange', domain=[('type', 'in', ['product', 'consu'])], required=True)
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM", required=True)
    product_qty = fields.Float(string="Quantity Per Pcs", digits=dp.get_precision('Product Unit of Measure'),
                               default=1.0)
    price_unit = fields.Float(string="Unit Price", digits=dp.get_precision('Product Price'),
                              default=0.0, required=True)
    price_subtotal = fields.Float(string="Sub Total", digits=dp.get_precision('Account'),
                                  compute="_compute_price_subtotal")
    state = fields.Selection(string="Status", related="assembly_id.state")

    po_price_unit = fields.Float(string="Unit Price PO", digits=dp.get_precision('Product Price'),
                                 compute="_compute_price_unit_po", inverse="_inverse_price_unit_po", copy=False)

    @api.depends('assembly_id',
                 'assembly_id.cmt_material_line_ids',
                 'assembly_id.cmt_material_line_ids.price_unit')
    def _compute_price_unit_po(self):
        """
        Update Price Unit Jika Ada Perubahan Harga
        :return: float
        """
        for cmt in self:
            cmt_ids = cmt.assembly_id.cmt_material_line_ids
            price_list = [line.price_unit for line in cmt_ids.filtered(
                lambda x: x.product_id.product_tmpl_id.id == cmt.product_id.id)]
            if price_list:
                cmt.price_unit = max(price_list)

    def _inverse_price_unit_po(self):
        for cmt in self:
            if cmt.po_price_unit:
                cmt.write({'price_unit': cmt.po_price_unit})

    @api.constrains('price_unit')
    def warning_maximum_price_unit(self):
        if self.price_unit == 0.0:
            raise UserError(_("Jumlah Harga Tidak Boleh Sama Dengan Nol"))

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.product_uom_id = self.product_id.uom_id.id

        return {'domain': {'product_uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}

    @api.onchange('product_uom_id')
    def onchange_product_uom_id(self):
        if self.product_uom_id.category_id.id != self.product_id.uom_id.category_id.id:
            raise UserError(_("Kategori UoM Tidak Sama Dengan Kategori UoM Produk"))

    @api.multi
    @api.depends('price_unit', 'product_qty')
    def _compute_price_subtotal(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        for line in self:
            line.price_subtotal = line.product_qty * line.price_unit


class AssemblyCmtProductService(models.Model):
    _name = 'assembly.cmt.product.service'
    _rec_name = 'product_id'
    _order = 'assembly_id, sequence, id'
    _description = 'Template Product Aksesoris'

    assembly_id = fields.Many2one(comodel_name="assembly.production", string="Assembly Order",
                                  ondelete='cascade', index=True)
    bom_id = fields.Many2one(comodel_name="mrp.bom", string="Bom Order", copy=False)
    sequence = fields.Integer(string='Seq', default=1)
    product_id = fields.Many2one(comodel_name="product.product", string="Products",
                                 track_visibility='onchange', domain=[('type', '=', 'service')], required=True)
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM", readonly=True,
                                     related="product_id.uom_id")
    product_qty = fields.Float(string="Quantity Per Pcs", digits=dp.get_precision('Product Unit of Measure'),
                               default=1.0, required=True)

    price_unit = fields.Float(string="Unit Price", digits=dp.get_precision('Product Price'),
                              default=0.0, required=True)
    price_subtotal = fields.Float(string="Sub Total", digits=dp.get_precision('Account'),
                                  compute="_compute_price_subtotal")
    state = fields.Selection(string="Status", related="assembly_id.state")

    @api.onchange('product_id')
    def onchange_product_id(self):
        self.product_uom_id = self.product_id.uom_id.id
        self.price_unit = self.product_id.product_tmpl_id.standard_price

    @api.multi
    @api.depends('price_unit', 'product_qty')
    def _compute_price_subtotal(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        for line in self:
            line.price_subtotal = line.product_qty * line.price_unit

    @api.constrains('price_unit')
    def warning_maximum_price_unit(self):
        if self.price_unit == 0.0:
            raise UserError(_("Jumlah Harga Tidak Boleh Sama Dengan Nol"))

    @api.multi
    def prepare_workorder_service_ids(self, workorder):
        self.ensure_one()
        res = []
        template = {
            'work_order_id': workorder.id,
            'product_id': self.product_id.id,
            'product_qty': self.product_qty,
            'product_uom_id': self.product_uom_id.id,
            'price_unit': self.price_unit

        }
        res.append(template)
        return res

    @api.multi
    def prepare_assembly_plan_services(self, plan_id):
        self.ensure_one()
        res = []
        if self.product_id.type not in ['consu', 'service']:
            return res
        values = {
            'plan_id': plan_id.id,
            'product_uom_id': self.product_uom_id.id,
            'product_id': self.product_id.id,
            'product_qty': self.product_qty,
            'price_unit': self.price_unit,
            'sequence': self.sequence,
        }
        res.append(values)
        return res

    def generate_assembly_plan_services(self, plan_id):
        plan_services = self.env['assembly.plan.services']
        done = self.env['assembly.plan.services'].browse()
        for line in self:
            for val in line.prepare_assembly_plan_services(plan_id):
                done += plan_services.create(val)
        return done






