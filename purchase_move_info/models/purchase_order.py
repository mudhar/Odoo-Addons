# -*- coding: utf-8 -*-

from odoo import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.depends('order_line.qty_received')
    def _compute_quantity_received(self):
        for order in self:
            total_received = 0.0
            for line in order.order_line:
                total_received += line.qty_received
            order.update({
                'total_qty_received': total_received
            })

    total_qty_received = fields.Float(string='Total Quantity Received', store=True, readonly=True,
                                      compute="_compute_quantity_received")