# -*- coding: utf-8 -*-
import datetime
import logging
from odoo import api, models, _
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class ReportRender(models.AbstractModel):
    _name = 'report.stock_location_report.report_stock_location_report'
    _description = 'Product profit Report Render'

    @api.multi
    def get_report_values(self, docid, data):
        # only for pdf report
        model_data = data['form']
        return self.generate_report_values(model_data)

    @api.model
    def generate_report_values(self, data):
        from_date = data['from_date']
        to_date = data['to_date']
        before_date = data['before_date']
        after_date = data['after_date']
        company = data['company']
        location_stock_ids = data['location_stock_ids']
        wh_stock = self.env.ref('stock.stock_location_stock')

        location_lines = []
        location_vendor = self.env['stock.location'].search(
            [('usage', '=', 'supplier'), ('company_id', 'in', [company[0], False])], limit=1)
        location_customer = self.env['stock.location'].search(
            [('usage', '=', 'customer'), ('company_id', 'in', [company[0], False])], limit=1)
        location_loss = self.env['stock.location'].search(
            [('usage', '=', 'inventory'), ('company_id', 'in', [company[0], False])], limit=1)
        location_transit = self.env['stock.location'].search(
            [('usage', '=', 'transit'),
             ('company_id', 'in', [company[0], False]),
             ('id', 'child of', 1)], limit=1)
        # if location_stock_ids:
        #     raise UserError(_("Test"))

        for location in location_stock_ids:
            location_line = {
                'location_id': location,
                'location_name': self.env['stock.location'].browse(location).get_warehouse().display_name,
                'qty_awal': 0.0,
                'qty_sj': 0.0,
                'qty_srb': 0.0,
                'qty_smb': 0.0,
                'qty_return_smb': 0.0,
                'qty_sale': 0.0,
                'qty_return_sale': 0.0,
                'qty_purchase': 0.0,
                'qty_return_purchase': 0.0,
                'qty_adjust_plus': 0.0,
                'qty_adjust_minus': 0.0,
                'qty_transit_in': 0.0,
                'qty_transit_out': 0.0,
                'qty_akhir': 0.0,
            }
            quantity_awal = []
            quantity_sale = []
            quantity_return_sale = []
            quantity_purchase = []
            quantity_return_purchase = []
            quantity_adjust_plus = []
            quantity_adjust_minus = []
            quantity_akhir = []
            quantity_sj = []
            quantity_srb = []
            quantity_smb = []

            quantity_return_smb = []
            quantity_transit_in = []
            quantity_transit_out = []
            if location_line.get('location_id'):
                # qty awal
                for move in self.env['stock.move'].search(
                        [('location_dest_id', '=', location_line.get('location_id')),
                         ('date', '=', before_date),
                         ('state', '=', 'done')], order='date desc'):
                    quantity_awal.append(move.quantity_done)

                for move in self.env['stock.move'].search(
                        [('location_id', '=', wh_stock.id),
                         ('location_dest_id', '=', location_line.get('location_id')),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         # ('internal_transfer_type_name', '=', 'SJ'),
                         ('state', 'not in', ('done', 'cancel'))
                         ]):
                    quantity_sj.append(move.product_uom_qty)

                # SRB
                for move in self.env['stock.move'].search(
                        [('location_id', '=', location_line.get('location_id')),
                         ('location_dest_id', '=', wh_stock.id),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         # ('internal_transfer_type_name', '=', 'Return of SJ'),
                         ('state', 'not in', ('done', 'cancel'))
                         ]):
                    quantity_srb.append(move.product_uom_qty)

                # SMB in
                for move in self.env['stock.move'].search(
                        [('location_dest_id', '=', location_line.get('location_id')),
                         ('location_id', 'in', location_stock_ids),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         # ('internal_transfer_type_name', '=', 'SMB'),
                         ('state', 'not in', ('done', 'cancel'))
                         ]):
                    quantity_smb.append(move.product_uom_qty)

                for move in self.env['stock.move'].search(
                        [('location_id', '=', location_line.get('location_id')),
                         ('location_dest_id', '=', location_stock_ids),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         # ('internal_transfer_type_name', '=', 'Return of SMB'),
                         ('state', 'not in', ('done', 'cancel'))
                         ]):
                    quantity_return_smb.append(move.product_uom_qty)

                # delivery order
                for move in self.env['stock.move'].search(
                        [('location_id', '=', location_line.get('location_id')),
                         ('location_dest_id', '=', location_customer.id),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', '=', 'done')]):
                    quantity_sale.append(move.quantity_done)

                for move in self.env['stock.move'].search(
                        [('location_id', '=', location_customer.id),
                         ('location_dest_id', '=', location_line.get('location_id')),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', '=', 'done')]):
                    quantity_return_sale.append(move.quantity_done)

                # Receipt
                for move in self.env['stock.move'].search(
                        [('location_id', '=', location_vendor.id),
                         ('location_dest_id', '=', location_line.get('location_id')),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', '=', 'done')]):
                    quantity_purchase.append(move.quantity_done)

                for move in self.env['stock.move'].search(
                        [('location_id', '=', location_line.get('location_id')),
                         ('location_dest_id', '=', location_vendor.id),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', '=', 'done')]):
                    quantity_return_purchase.append(move.quantity_done)

                for move in self.env['stock.move'].search(
                        [('location_id', '=', location_loss.id),
                         ('location_dest_id', '=', location_line.get('location_id')),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', '=', 'done')]):
                    quantity_adjust_plus.append(move.quantity_done)

                for move in self.env['stock.move'].search(
                        [('location_id', '=', location_line.get('location_id')),
                         ('location_dest_id', '=', location_loss.id),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', '=', 'done')]):
                    quantity_adjust_minus.append(move.quantity_done)

                for move in self.env['stock.move'].search(
                        [('location_id', '=', location_line.get('location_id')),
                         ('location_dest_id', '=', location_transit.id),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', 'not in', ('done', 'cancel'))]):
                    quantity_transit_out.append(move.product_uom_qty)

                for move in self.env['stock.move'].search(
                        [('location_id', '=', location_transit.id),
                         ('location_dest_id', '=', location_line.get('location_id')),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', 'not in', ('done', 'cancel'))]):
                    quantity_transit_in.append(move.product_uom_qty)

                # for quant in self.env['stock.quant'].search(
                #         [('location_id', 'child of', location_line.get('location_id'))]):
                #     quantity_akhir.append(quant.quantity)

                # quantity_akhir
                for move in self.env['stock.move'].search(
                        [('location_dest_id', '=', location_line.get('location_id')),
                         ('date', '=', after_date),
                         ('state', '=', 'done')], order='date desc'):
                    quantity_akhir.append(move.quantity_done)
            # if len(quantity_awal) <= 0:
            #     location_line['qty_awal'] += 0.0
            # elif len(quantity_awal) >= 1:
            #     location_line['qty_awal'] += quantity_awal[-1]

            location_line['qty_awal'] += sum(quantity_awal)
            location_line['qty_sale'] += sum(quantity_sale)
            location_line['qty_sj'] += sum(quantity_sj)
            location_line['qty_srb'] += sum(quantity_srb)
            location_line['qty_smb'] += sum(quantity_smb)
            location_line['qty_return_smb'] += sum(quantity_return_smb)
            location_line['qty_return_sale'] += sum(quantity_return_sale)
            location_line['qty_purchase'] += sum(quantity_purchase)
            location_line['qty_return_purchase'] += sum(quantity_return_purchase)
            location_line['qty_adjust_plus'] += sum(quantity_adjust_plus)
            location_line['qty_adjust_minus'] += sum(quantity_adjust_minus)
            location_line['qty_transit_in'] += sum(quantity_transit_in)
            location_line['qty_transit_out'] += sum(quantity_transit_out)
            location_line['qty_akhir'] += sum(quantity_akhir)

            location_lines += [location_line]

        # if location_lines:
        #     print(location_lines)

        return {
            'data': data,
            'location_lines': location_lines,
            'report_date': datetime.datetime.now().strftime("%Y-%m-%d"),
        }
