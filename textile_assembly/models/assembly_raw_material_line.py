from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class AssemblyRawMaterialLine(models.Model):
    _name = 'assembly.raw.material.line'
    _description = 'Assembly Raw Material Line'
    _rec_name = 'product_id'
    _order = 'assembly_id, sequence, id'

    assembly_id = fields.Many2one(comodel_name="assembly.production", string="Assembly Order", ondelete='cascade', index=True)
    product_qty = fields.Float(string="Quantity Per Pcs", digits=dp.get_precision('Product Unit of Measure'), default=1.0)
    price_unit = fields.Float(string="Unit Price", digits=dp.get_precision('Product Price'), required=True)
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM", required=True,)
    sequence = fields.Integer(string='Sequence', default=1)
    product_id = fields.Many2one(comodel_name="product.product", string="Products", track_visibility='onchange',
                                 required=True,
                                 domain=[('type', 'in', ['product', 'consu'])])
    attribute_id = fields.Many2one(comodel_name="product.attribute.value", string="Attributes", index=True,
                                   required=True)
    ratio = fields.Float(string="Total Ratio")
    price_subtotal = fields.Float(string="Sub Total", digits=dp.get_precision('Account'),
                                  compute="compute_price_subtotal")
    state = fields.Selection(string="Status", related="assembly_id.state")

    @api.constrains('product_id')
    def _check_duplicate_product(self):
        raw_ids = self.env['assembly.raw.material.line'].search_count(
            [('product_id', '=', self.product_id.id), ('assembly_id', '=', self.assembly_id.id)])
        if raw_ids and raw_ids > 1:
            raise UserError(_('Duplicate Product\t%s\t Total Duplicate: %s')
                            % (self.product_id.display_name.upper(), str(raw_ids)))
        else:
            return False

    @api.onchange('attribute_id')
    def _onchange_attribute_id(self):
        if not self.product_id:
            self.attribute_id = False
        attribute_ids = self.assembly_id.variant_line_ids.mapped('attribute_value_ids')
        domain = {'attribute_id': [('id', 'in', attribute_ids.ids)]}
        result = {}
        if attribute_ids:
            result = {'domain': domain}
        return result

    @api.onchange('product_id')
    def onchange_product_id(self):
        name = self.product_id.name
        if self.product_id.code:
            name = '[%s] %s' % (self.product_id.code, name)
        if self.product_id.description_purchase:
            name += '\n' + self.product_id.description_purchase
        self.product_uom_id = self.product_id.uom_id.id
        self.price_unit = self.product_id.standard_price if self.product_id.standard_price else 0.0
        return {'domain': {'product_uom_id': [('category_id', '=', self.product_id.uom_id.category_id.id)]}}

    @api.onchange('product_id')
    def onchange_product_id_warning(self):
        if self.product_id and self.product_id.attribute_line_ids:
            attribute_id = self.product_id.attribute_line_ids.mapped('attribute_id')
            raise UserError(_("Anda Tidak Dapat Menambahkan Attribute Pada Produk %s\n "
                              "Yang Memiliki Attribute %s Didalamnya")
                            % (self.product_id.display_name.upper(), attribute_id.name.upper()))

    @api.onchange('product_uom_id')
    def onchange_product_uom_id(self):
        if self.product_uom_id.category_id.id != self.product_id.uom_id.category_id.id:
            raise UserError(_("Kategori UoM Tidak Sama Dengan Kategori UoM Produk"))

    @api.constrains('price_unit')
    def warning_maximum_price_unit(self):
        if self.price_unit == 0.0:
            raise UserError(_("Jumlah Harga Tidak Boleh Sama Dengan Nol"))

    def prepare_assembly_plan_material(self, plan_id):
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        values = {
            'plan_id': plan_id.id,
            'product_uom_id': self.product_uom_id.id,
            'product_id': self.product_id.id,
            'product_qty': self.product_qty,
            'price_unit': self.price_unit,
            'sequence': self.sequence,
            'attribute_id': self.attribute_id.id,
            'total_ratio': self.ratio
        }
        res.append(values)
        return res

    def generate_assembly_plan_raw_material(self, plan_id):
        plan_raw_materials = self.env['assembly.plan.raw.material']
        done = self.env['assembly.plan.raw.material'].browse()
        for line in self:
            for val in line.prepare_assembly_plan_material(plan_id):
                done += plan_raw_materials.create(val)
        return done

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

    @api.multi
    @api.depends('price_unit', 'product_qty')
    def compute_price_subtotal(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        for line in self:
            line.price_subtotal = line.product_qty * line.price_unit



