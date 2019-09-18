# -*- coding: utf-8 -*-

from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.multi
    def update_lot_from_stock_move(self):
        move_ids = self.env['stock.move'].search([('length', '>', 0.0),
                                                  ('width', '>', 0.0),
                                                  ('product_id.track_all', '=', True)])

        for move in move_ids.filtered(lambda x: x.state not in ('done', 'cancel')):
            if move.product_id:
               	lot = self.env['stock.production.lot'].create_automate_lot(move.width, move.length,
                                                                               move.product_id.id)

                if lot:
                    for i in range(0, len(move)):
                        move[i].update({'purchase_serial_number': lot.id})

        return True







