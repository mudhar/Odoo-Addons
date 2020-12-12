# -*- coding: utf-8 -*-
from odoo import api, models


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    @api.multi
    def update_sequence_assembly(self):
        try:
            seq_ids = self.env['ir.sequence'].search([
                '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|', '|',
                ('code', '=', 'assembly.plan'),
                ('code', '=', 'stock.picking.materials_incoming'),
                ('code', '=', 'stock.picking.return_cmt'),
                ('code', '=', 'stock.picking.return_non_cmt'),
                ('code', '=', 'stock.picking.materials_outgoing'),
                ('code', '=', 'stock.picking.goods_incoming'),
                ('code', '=', 'stock.picking.goods_outgoing'),
                ('code', '=', 'stock.picking.return_customer'),
                ('code', '=', 'picking.internal.store.wh'),
                ('code', '=', 'picking.internal.wh.store'),
                ('code', '=', 'picking.internal.store.store'),
                ('code', '=', 'purchase.order.materials'),
                ('code', '=', 'purchase.order.goods'),
                ('code', '=', 'purchase.order.subpo'),
            ])
            if seq_ids:
                seq_to_do = seq_ids.filtered(lambda x: not x.use_date_range)
                seq_to_do.write({'use_date_range': True, 'implementation': 'no_gap'})
        except Exception as e:
            pass
        return True

















