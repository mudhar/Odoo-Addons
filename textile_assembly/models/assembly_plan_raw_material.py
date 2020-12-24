# -*- coding: utf-8 -*-
import math

from odoo import api, fields, models
from odoo.addons import decimal_precision as dp
from odoo.tools import float_round


class AssemblyPlanRawMaterial(models.Model):
    _name = 'assembly.plan.raw.material'
    _rec_name = 'product_id'
    _description = 'Assembly Plan Material'

    plan_id = fields.Many2one(comodel_name="assembly.plan", string="Plan Order",
                              ondelete='cascade', index=True)
    sequence = fields.Integer('Sequence', default=1)
    product_id = fields.Many2one(comodel_name="product.product", string="Products", index=True)
    product_qty = fields.Float('Quantity', default=0.0, digits=dp.get_precision('Product Unit of Measure'))
    product_uom_id = fields.Many2one(comodel_name="product.uom", string="UoM")
    qty_available = fields.Float('OnHand', digits=dp.get_precision('Product Unit of Measure'))
    total_ratio = fields.Float('Total Ratio', help="Jumlah Berdasarkan Ratio")
    qty_to_plan = fields.Float('Exp Consu Plan',
                               digits=dp.get_precision('Product Unit of Measure'), compute="_compute_quantity_consume",
                               readonly=True, store=True,
                               help="Total Yang Diharapkan Untuk Kebutuhan Material Yang Akan Diproduksi")
    qty_to_actual = fields.Float('Exp Consu Actual',
                                 digits=dp.get_precision('Product Unit of Measure'),
                                 compute="_compute_quantity_actual", readonly=True, store=True)

    total_actual_quantity = fields.Float(string="Maximum Potensial", default=0.0,
                                         digits=dp.get_precision('Product Unit of Measure'),
                                         compute="_compute_total_actual_quantity", store=True)
    price_unit = fields.Float('Unit Price', digits=dp.get_precision('Product Price'))
    price_subtotal = fields.Float('Subtotal', digits=dp.get_precision('Account'),
                                  compute="_compute_price_subtotal")
    price_subtotal_actual = fields.Float(string="Sub Total", digits=dp.get_precision('Account'),
                                         compute="_compute_price_subtotal")

    attribute_id = fields.Many2one(comodel_name="product.attribute.value", string="Variants")

    needs_lots = fields.Boolean('Tracking', compute='_compute_needs_lots')
    state = fields.Selection(related='plan_id.state')

    need_procurement = fields.Boolean(string="Need Procurment", readonly=True, compute="_compute_need_procurement")

    @api.multi
    @api.depends('plan_id.plan_line_ids.new_qty')
    def _compute_quantity_consume(self):
        for raw in self:
            if raw.product_id and raw.attribute_id:
                quantity_plan = sum(raw.plan_id.plan_line_ids.filtered(
                    lambda x: x.attribute_value_ids[0].id == raw.attribute_id.id
                    or x.attribute_value_ids[1].id == raw.attribute_id.id).mapped('new_qty'))
                raw.update({'qty_to_plan': float_round(
                    raw.product_qty * quantity_plan,
                    precision_rounding=raw.product_uom_id.rounding,
                    rounding_method='UP')})

    @api.multi
    @api.depends('plan_id.plan_line_actual_ids.actual_quantity')
    def _compute_quantity_actual(self):
        for raw in self:
            if raw.product_id and raw.attribute_id:
                quantity_actual = sum(raw.plan_id.plan_line_actual_ids.filtered(
                    lambda x: x.attribute_value_ids[0].id == raw.attribute_id.id
                    or x.attribute_value_ids[1].id == raw.attribute_id.id).mapped('actual_quantity'))
                raw.update({'qty_to_actual': float_round(
                    raw.product_qty * quantity_actual,
                    precision_rounding=raw.product_uom_id.rounding,
                    rounding_method='UP')})

    # hitung maximum product yang bisa diproduksi
    @api.multi
    @api.depends('qty_available', 'product_qty',
                 'total_ratio')
    def _compute_total_actual_quantity(self):
        for material in self:
            if material.qty_available:
                result_qty = material.qty_available / material.product_qty
                material.total_actual_quantity = math.ceil(result_qty)

        return True

    @api.multi
    @api.depends('price_unit',
                 'qty_to_actual',
                 'product_qty')
    def _compute_price_subtotal(self):
        for material in self:
            material.price_subtotal = material.product_qty * material.price_unit
            material.price_subtotal_actual = material.qty_to_actual * material.price_unit

        return True

    @api.multi
    @api.depends('qty_available', 'qty_to_plan')
    def _compute_need_procurement(self):
        for material in self:
            if material.qty_to_plan > material.qty_available:
                material.need_procurement = True
            else:
                material.need_procurement = False

    @api.depends('product_id.tracking')
    def _compute_needs_lots(self):
        for move in self:
            move.needs_lots = move.product_id.tracking != 'none'
