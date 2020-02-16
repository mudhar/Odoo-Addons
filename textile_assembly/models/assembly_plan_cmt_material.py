import logging
from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.tools import float_round
from odoo.exceptions import UserError
_logger = logging.getLogger(__name__)


class AssemblyPlanCmtMaterial(models.Model):
    _name = 'assembly.plan.cmt.material'
    _rec_name = 'product_id'
    _description = 'CMT Material Plan'

    plan_id = fields.Many2one(comodel_name="assembly.plan", string="Plan Order",
                              ondelete='cascade', index=True)

    product_id = fields.Many2one(comodel_name="product.product", string="Products", index=True)
    product_qty = fields.Float(string="Quantity", default=0.0, digits=dp.get_precision('Product Unit of Measure'))
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM")
    ratio = fields.Float(string="Ratio Of")
    qty_to_plan = fields.Float(string="Expected Consume Qty",
                               digits=dp.get_precision('Product Unit of Measure'),
                               compute="_compute_quantity_consume", store=True)
    quantity_to_actual = fields.Float(string="Expected Consume Revised",
                                      digits=dp.get_precision('Product Unit of Measure'),
                                      compute="_compute_quantity_actual", store=True)
    price_unit = fields.Float(string="Unit Price", digits=dp.get_precision('Product Price'))
    price_subtotal_plan = fields.Float(string="Sub Total", digits=dp.get_precision('Account'),
                                       compute="_compute_price_subtotal")
    price_subtotal_actual = fields.Float(string="Sub Total", digits=dp.get_precision('Account'),
                                         compute="_compute_price_subtotal")

    sequence = fields.Integer('Seq', default=1)
    state = fields.Selection(related='plan_id.state', store=True)
    qty_available = fields.Float(string="On Hand",
                                 digits=dp.get_precision('Product Unit of Measure'))
    need_procurement = fields.Boolean(string="Need Procurment", readonly=True, compute="_compute_need_procurement")
    date_planned_start = fields.Datetime('Deadline Start', copy=False, index=True,
                                         related="plan_id.date_planned_start")

    @api.multi
    @api.depends('price_unit',
                 'qty_to_plan',
                 'quantity_to_actual')
    def _compute_price_subtotal(self):
        for cmt in self:
            cmt.price_subtotal_plan = cmt.qty_to_plan * cmt.price_unit
            cmt.price_subtotal_actual = cmt.quantity_to_actual * cmt.price_unit
        return True

    # @api.multi
    # @api.depends('qty_consumed',
    #              'qty_used')
    # def _compute_qty_differ(self):
    #     for order in self:
    #         if order.qty_used != order.qty_consumed:
    #             order.qty_differ = order.qty_consumed - order.qty_used

    @api.multi
    @api.depends('product_id',
                 'product_id.attribute_value_ids',
                 'plan_id.plan_line_ids.new_qty',
                 'plan_id.produce_ids.quantity_plan')
    def _compute_quantity_consume(self):
        for cmt in self:
            if cmt.product_id and cmt.product_id.attribute_value_ids:
                quantity_plan = sum(cmt.plan_id.plan_line_ids.filtered(
                    lambda x: (x.attribute_value_ids[0].id == cmt.product_id.attribute_value_ids[0].id)
                              or (x.attribute_value_ids[1].id == cmt.product_id.attribute_value_ids[0].id)
                ).mapped('new_qty'))
                cmt.update({'qty_to_plan': quantity_plan})
            if cmt.product_id and not cmt.product_id.attribute_value_ids:
                quantity_to_plan = sum(cmt.plan_id.produce_ids.mapped('quantity_plan'))
                cmt.update({'qty_to_plan': float_round((cmt.product_qty * quantity_to_plan),
                                                       precision_rounding=cmt.product_uom_id.rounding,
                                                       rounding_method='UP')})
        return True

    @api.multi
    @api.depends('product_id',
                 'product_id.attribute_value_ids',
                 'plan_id.plan_line_actual_ids.actual_quantity',
                 'plan_id.produce_ids.quantity_actual')
    def _compute_quantity_actual(self):
        for cmt in self:
            if cmt.product_id and cmt.product_id.attribute_value_ids:
                quantity_actual = sum(cmt.plan_id.plan_line_ids.filtered(
                    lambda x: (x.attribute_value_ids[0].id == cmt.product_id.attribute_value_ids[0].id)
                              or (x.attribute_value_ids[1].id == cmt.product_id.attribute_value_ids[0].id)
                ).mapped('actual_quantity'))
                cmt.update({'quantity_to_actual': quantity_actual})
            if cmt.product_id and not cmt.product_id.attribute_value_ids:
                quantity_actual = sum(cmt.plan_id.produce_ids.mapped('quantity_actual'))
                cmt.update({'quantity_to_actual': float_round((cmt.product_qty * quantity_actual),
                                                              precision_rounding=cmt.product_uom_id.rounding,
                                                              rounding_method='UP')})
        return True

    @api.multi
    @api.depends('qty_available', 'qty_to_plan')
    def _compute_need_procurement(self):
        for cmt in self:
            if cmt.product_id.type == 'product':
                if cmt.qty_to_plan > cmt.qty_available:
                    cmt.need_procurement = True
                else:
                    cmt.need_procurement = False
            elif cmt.product_id.type == 'consu':
                cmt.need_procurement = True


