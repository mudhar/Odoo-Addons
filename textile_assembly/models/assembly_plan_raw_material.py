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
                               digits=dp.get_precision('Product Unit of Measure'),
                               help="Total Yang Diharapkan Untuk Kebutuhan Material Yang Akan Diproduksi")
    qty_to_actual = fields.Float('Exp Consu Actual',
                                 digits=dp.get_precision('Product Unit of Measure'))

    qty_final = fields.Float(string="To Be Produce Qty", default=0.0, digits=dp.get_precision('Product Unit of Measure'),
                             help="Berapa Unit Produk Yang Jadi DiProduksi, Maksimum Kapasitas")

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
    date_planned_start = fields.Datetime('Deadline Start', copy=False, index=True,
                                         related="plan_id.date_planned_start")

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
    @api.depends('product_qty', 'total_qty_to_plan', 'total_ratio')
    def _compute_amount_qty(self):
        for material in self:
            if material.total_qty_to_plan:
                result_qty = (material.product_qty / material.total_ratio) * material.total_qty_to_plan
                material.qty_to_plan = float_round(result_qty, precision_rounding=material.product_id.uom_id.rounding,
                                                   rounding_method='UP')
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






