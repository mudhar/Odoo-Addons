from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AssemblyPlanServices(models.Model):
    _name = 'assembly.plan.services'
    _rec_name = 'product_id'
    _description = 'List Biaya Produksi'

    plan_id = fields.Many2one(comodel_name="assembly.plan", ondelete='cascade', required=True, index=True,
                              string="Order Plan")
    product_id = fields.Many2one(comodel_name="product.product", string="Products", index=True)
    product_qty = fields.Float(string="Quantity", default=0.0, digits=dp.get_precision('Product Unit of Measure'))
    quantity_plan = fields.Float(string="Exp Consu Plan", default=0.0,
                                 digits=dp.get_precision('Product Unit of Measure'), compute="_compute_quantity_consume")
    quantity_actual = fields.Float(string="Exp Consu Revised", default=0.0,
                                   digits=dp.get_precision('Product Unit of Measure'),
                                   compute="_compute_quantity_consume")
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM")
    price_unit = fields.Float(string="Unit Price", digits=dp.get_precision('Product Price'))
    price_subtotal = fields.Float(string="Sub Total", digits=dp.get_precision('Account'),
                                  compute="_compute_price_subtotal")

    sequence = fields.Integer('Seq', default=1)
    state = fields.Selection(related='plan_id.state', store=True)

    @api.multi
    @api.depends('price_unit',
                 'quantity_actual')
    def _compute_price_subtotal(self):
        for service in self:
            service.price_subtotal = service.quantity_actual * service.price_unit
        return True

    @api.multi
    @api.depends('plan_id.produce_ids.quantity_plan',
                 'plan_id.produce_ids.quantity_actual')
    def _compute_quantity_consume(self):
        for order in self:
            produce_plan = sum(order.plan_id.produce_ids.mapped('quantity_plan'))
            produce_actual = sum(order.plan_id.produce_ids.mapped('quantity_actual'))
            order.quantity_plan = produce_plan * order.product_qty
            order.quantity_actual = produce_actual * order.product_qty




