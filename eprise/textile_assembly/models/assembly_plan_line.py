from odoo import api, fields, models
from odoo.addons import decimal_precision as dp


class AssemblyPlanLine(models.Model):
    _name = 'assembly.plan.line'
    _description = 'Assembly Plan Line'
    _order = 'plan_id, sequence, id'

    plan_id = fields.Many2one(comodel_name="assembly.plan", string="Assembly Plan", ondelete='cascade', readonly=True)
    plan_line_ids = fields.Many2many(
        'assembly.prod.variant.line',
        'assembly_prod_variant_line_plan_rel',
        'plan_line_id', 'order_line_id',
        string='Assembly Plan Lines', readonly=True, copy=False)
    sequence = fields.Integer('Sequence', default=1)
    new_qty = fields.Float('Quantity', default=0.0, digits=dp.get_precision('Product Unit of Measure'),
                           store=True)
    product_variant_id = fields.Many2one(comodel_name="product.product", string="Products")
    ratio = fields.Float('Ratio')
    attribute_value_ids = fields.Many2many(comodel_name="product.attribute.value", string="Variants")

    state = fields.Selection(related='plan_id.state', store=True)
    cancelled = fields.Boolean(
        string="Cancelled", readonly=True, default=False, copy=False)

    @api.multi
    def do_cancel(self):
        """Actions to perform when cancelling a purchase request line."""
        self.write({'cancelled': True})

    @api.multi
    def do_uncancel(self):
        """Actions to perform when uncancelling a purchase request line."""
        self.write({'cancelled': False})
