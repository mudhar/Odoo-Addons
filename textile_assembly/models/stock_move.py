# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = 'stock.move'

    show_generate_lot = fields.Boolean(string="Show Button Generate Lot Name", compute="compute_picking_code")
    # is_qc_done = fields.Boolean(string="Check QC Done", compute="compute_qc_done")

    # Digunakan Untuk Memudahkan Listing Informasi Quantity Return Pada Report Yang Terbentuk Dari Pivot View
    returned_picking = fields.Boolean(string="Returned Picking")
    quantity_reject = fields.Float(string="Quantity Reject", compute="_compute_quantity_reject")

    @api.depends('production_id',
                 'picking_id')
    def _compute_quantity_reject(self):
        for move in self:
            picking_object = self.env['stock.picking']
            quantity = []
            if move.production_id and move.picking_id:
                move_lines = picking_object.search(
                    [('backorder_id', '=', move.picking_id.id),
                     ('is_rejected', '=', True)])

                for line in move_lines.move_line_ids.filtered(lambda x: x.product_id.id == move.product_id.id):
                    quantity.append(line.product_qty)
            if quantity:
                move.quantity_reject = sum(quantity)
        return True

    # Menampilkan Button Generate Lot Pada Terima Barang Jika Produk Tsb Teridentifikasi Roll
    @api.depends('picking_type_id')
    def compute_picking_code(self):
        for order in self:
            if order and order.product_id.is_roll:
                if order.picking_type_id.code == 'internal':
                    order.show_generate_lot = False
                elif order.picking_type_id.code == 'outgoing':
                    order.show_generate_lot = False
                else:
                    order.show_generate_lot = True

    # Generate Nama Lot Secara Masal Yang Diambil Dari Referensi Picking dan Seq Serial Lot
    @api.multi
    def action_generate_lot_id(self):
        for order in self:
            if order and order.product_id:
                if order.product_id.is_roll:
                    for move_line in order.move_line_ids.filtered(
                            lambda x: x.product_id.id == order.product_id.id and x.move_id.id == order.id):
                        if move_line and move_line.product_id and not move_line.lot_id:
                            picking_name = order.picking_id.name
                            count_index = picking_name.index('/')
                            lot_id = self.env['stock.production.lot'].create({
                                'product_id': move_line.product_id.id,
                                'name': ''.join('%s - %s' % (picking_name[count_index:],
                                                             self.env['ir.sequence'].next_by_code('stock.lot.serial')))
                            })
                            move_line.write({'lot_name': lot_id.name,
                                             'lot_id': lot_id.id})
        return True
