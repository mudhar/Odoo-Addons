# -*- coding: utf-8 -*-

from odoo import models, fields, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.depends('move_lines', 'move_lines.quantity_done')
    def _compute_quantity_received(self):
        for picking in self:
            quantity_done = 0.0
            for line in picking.move_lines:
                quantity_done += line.quantity_done
            picking.update({'total_qty_received': quantity_done})

    @api.depends('move_lines', 'move_lines.product_uom_qty')
    def _compute_quantity_demand(self):
        for picking in self:
            quantity_demand = 0.0
            for line in picking.move_lines:
                quantity_demand += line.product_uom_qty
            picking.update({'total_initial_qty': quantity_demand})

    @api.depends('move_lines',
                 'state',
                 'move_lines.value')
    def _compute_total_values_done(self):
        for picking in self.filtered(lambda p: p.state == 'done'):
            total_values_done = 0.0
            for line in picking.move_lines:
                total_values_done += line.value
            picking.update({'total_values_done': total_values_done})

    @api.depends('move_lines',
                 'move_lines.product_uom_qty',
                 'move_lines.price_unit')
    def _compute_total_values_demand(self):
        for picking in self:
            total_values_demand = 0.0
            for line in picking.move_lines:
                total_values_demand += line.price_unit * line.product_uom_qty
            picking.update({'total_values_demand': total_values_demand})

    total_qty_received = fields.Float(string='Total Quantity Received', store=True, readonly=True,
                                      compute="_compute_quantity_received")
    total_initial_qty = fields.Float(string='Total Quantity Demand', store=True, readonly=True,
                                     compute="_compute_quantity_demand")
    total_values_done = fields.Float(string='Total Values Received', store=True, readonly=True,
                                     compute="_compute_total_values_done")
    total_values_demand = fields.Float(string='Total Values Demand', store=True, readonly=True,
                                       compute="_compute_total_values_demand")
