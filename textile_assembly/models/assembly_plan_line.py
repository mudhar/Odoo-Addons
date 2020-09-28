import logging

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp

_logger = logging.getLogger(__name__)


class AssemblyPlanLine(models.Model):
    _name = 'assembly.plan.line'
    _description = 'Assembly Plan Line'
    _order = 'sequence'

    plan_id = fields.Many2one(comodel_name="assembly.plan", string="Assembly Plan",
                              ondelete='cascade', index=True)
    sequence = fields.Integer('Sequence', default=1)
    product_id = fields.Many2one(
        comodel_name="product.product", string="Products")
    product_uom_id = fields.Many2one(
        'product.uom', 'Product Unit of Measure', related="product_id.uom_id")
    new_qty = fields.Float('Plan', default=0.0,
                           digits=dp.get_precision('Product Unit of Measure'))
    actual_quantity = fields.Float('On Hand', default=0.0, digits=dp.get_precision('Product Unit of Measure'))

    ratio = fields.Float(
        'Ratio', digits=dp.get_precision('Product Unit of Measure'))
    attribute_value_ids = fields.Many2many(
        comodel_name="product.attribute.value", string="Variants")
    date_planned_start = fields.Datetime('Schedule Date', copy=False, index=True,
                                         related="plan_id.date_planned_start")

    state = fields.Selection(related='plan_id.state', store=True)

    unit_cost = fields.Float(string='Unit Cost', digits=dp.get_precision('Product Price'), compute="_compute_unit_cost")

    @api.multi
    def _compute_unit_cost(self):
        for plan in self:
            if plan.plan_id and plan.plan_id.amount_total:
                amount_total = plan.plan_id.amount_total
                quantity_to_produce = plan.amount_quantity_to_produce()
                plan.unit_cost = amount_total / sum(quantity_to_produce)

    @api.multi
    def amount_quantity_to_produce(self):
        quantity = []
        for plan in self:
            for produce in self.env['assembly.plan.produce'].search(
                    [
                        ('plan_id', '=', plan.plan_id.id)
                    ]).filtered(lambda x: x.attribute_id.id == plan.attribute_value_ids[0].id \
                                          or x.attribute_id.id == plan.attribute_value_ids[1].id):
                quantity.append(produce.quantity_actual)
        return quantity

    def generate_production_variant(self, production_id):
        mo_variants = self.env['mrp.production.variant']
        done = self.env['mrp.production.variant'].browse()
        for line in self:
            for val in line.prepare_production_variant(production_id):
                done += mo_variants.create(val)
        return done

    def prepare_production_variant(self, production_id):
        self.ensure_one()
        res = []
        if self.product_id.type not in ['product', 'consu']:
            return res
        value = {
            'production_id': production_id.id,
            'product_id': self.product_id.id,
            'product_uom_id': self.product_uom_id.id,
            'ratio': self.ratio,
            'product_qty': self.actual_quantity,
            'sequence': self.sequence,
        }
        res.append(value)
        return res

