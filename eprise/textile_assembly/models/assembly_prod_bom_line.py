from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AssemblyProdBomLine(models.Model):
    _name = 'assembly.prod.bom.line'
    _description = 'Assembly bom Line'
    _order = 'assembly_id, sequence, id'

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            name = self.product_id.name
            if self.product_id.code:
                name = '[%s] %s' % (self.product_id.code, name)
            if self.product_id.description_purchase:
                name += '\n' + self.product_id.description_purchase
            self.product_uom_id = self.product_id.uom_id.id
            self.price_unit = self.product_id.product_tmpl_id.standard_price
            self.name = name

    name = fields.Char('Description', size=256,
                       track_visibility='onchange')
    # product_qty = fields.Float(string="Quantity", digits=dp.get_precision('Product Unit of Measure'),
    #                            default=1.0, store=True)
    price_unit = fields.Float(string="Cost", digits=dp.get_precision('Product Price'),
                              default=0.0, store=True)
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM")

    assembly_id = fields.Many2one(comodel_name="assembly.production", string="Product BOM",
                                  ondelete='cascade', index=True)
    sequence = fields.Integer(string='Sequence', default=1)

    product_id = fields.Many2one(comodel_name="product.product", string="Products",
                                 domain=[('purchase_ok', '=', True)], track_visibility='onchange')

    attribute_value_ids = fields.Many2many(comodel_name="product.attribute.value", string="Variants", store=True,
                                           index=True)
    ratio = fields.Float(string="Total Ratio")

    price_subtotal = fields.Float(string="Sub Total", digits=dp.get_precision('Account'),
                                  compute="_compute_price_subtotal", store=True)
    state = fields.Selection(string="Status", related="assembly_id.state", store=True)

    @api.multi
    def write(self, values):
        # Add code here
        product = self.env['product.product']
        if values.get('price_unit'):
            product_ids = product.search([('name', '=', self.product_id.name)])
            product_ids.write({'standard_price': values['price_unit']})
        return super(AssemblyProdBomLine, self).write(values)

    @api.multi
    def prepare_assembly_plan_material(self, ratio):
        self.ensure_one()
        res = {
            'product_uom_id': self.product_uom_id.id,
            'product_id': self.product_id.id,
            'sequence': self.sequence,
            'total_ratio': ratio
        }
        return res

    @api.multi
    def assembly_plan_material_create(self, bom_id, ratio):
        bom_lines = self.env['assembly.plan.material']
        for line in self:
            vals = line.prepare_assembly_plan_material(ratio=ratio)
            vals.update({'plan_id': bom_id, 'plan_material_ids': [(6, 0, [line.id])]})
            bom_lines |= self.env['assembly.plan.material'].create(vals)
        return bom_lines

    @api.multi
    @api.depends('price_unit')
    def _compute_price_subtotal(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        for line in self:
            line.price_subtotal = line.price_unit