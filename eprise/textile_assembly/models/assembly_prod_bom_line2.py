from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AssemblyProdBomLine2(models.Model):
    _name = 'assembly.prod.bom.line2'
    _description = 'Assembly bom Line2'
    _order = 'assembly_id, sequence, id'
    _rec_name = 'product_id'

    assembly_id = fields.Many2one(comodel_name="assembly.production", string="Product BOM",
                                  ondelete='cascade', index=True)
    sequence = fields.Integer(string='Sequence', default=1)

    product_id = fields.Many2one(comodel_name="product.product", string="Products", store=True,
                                 track_visibility='onchange', domain="[('type', '!=', 'service')]")
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM")
    product_qty = fields.Float(string="Quantity", digits=dp.get_precision('Product Unit of Measure'),
                               default=1.0, store=True)
    price_unit = fields.Float(string="Cost", digits=dp.get_precision('Product Price'),
                              default=0.0, store=True)
    price_subtotal = fields.Float(string="Sub Total", digits=dp.get_precision('Account'),
                                  compute="_compute_price_subtotal", store=True)
    state = fields.Selection(string="Status", related="assembly_id.state", store=True)


    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            self.product_uom_id = self.product_id.uom_id.id
            self.price_unit = self.product_id.product_tmpl_id.standard_price

    @api.onchange('price_unit')
    def onchange_price_unit(self):
        if self.price_unit != self.product_id.product_tmpl_id.standard_price:
            self.product_id.product_tmpl_id.write({'standard_price': self.price_unit})

    @api.multi
    @api.depends('price_unit', 'product_qty')
    def _compute_price_subtotal(self):
        """
        @api.depends() should contain all fields that will be used in the calculations.
        """
        for line in self:
            line.price_subtotal = line.product_qty * line.price_unit