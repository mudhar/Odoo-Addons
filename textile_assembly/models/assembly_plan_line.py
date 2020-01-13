import logging
from odoo import api, fields, models, _
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

    # Tambahan Untuk Report
    # qty_produced = fields.Float(string="Qty Produced",
    #                             digits=dp.get_precision(
    #                                 'Product Unit of Measure'),
    #                             readonly=True)
    # qty_sample = fields.Float(string="Qty Sample", digits=dp.get_precision('Product Unit of Measure'),
    #                           readonly=True)

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

