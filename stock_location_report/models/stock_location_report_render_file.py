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
        company = data['company']
        location_stock_ids = data['location_stock_ids']

        location_lines = []
        location_vendor = self.env['stock.location'].search(
            [('usage', '=', 'supplier'), ('company_id', 'in', [company[0], False])], limit=1)
        location_customer = self.env['stock.location'].search(
            [('usage', '=', 'customer'), ('company_id', 'in', [company[0], False])], limit=1)
        location_loss = self.env['stock.location'].search(
            [('usage', '=', 'inventory'), ('company_id', 'in', [company[0], False])], limit=1)
        # if location_stock_ids:
        #     raise UserError(_("Test"))

        for location in location_stock_ids:
            location_line = {
                'location_id': location,
                'location_name': self.env['stock.location'].browse(location).get_warehouse().display_name,
                'qty_awal': 0.0,
                'qty_sale': 0.0,
                'qty_return_sale': 0.0,
                'qty_purchase': 0.0,
                'qty_return_purchase': 0.0,
                'qty_adjust_plus': 0.0,
                'qty_adjust_minus': 0.0,
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
            if location_line.get('location_id'):
                # qty awal
                for move in self.env['stock.move.line'].search(
                        [('location_dest_id', '=', location_line.get('location_id')),
                         ('date', '<=', from_date),
                         ('state', '=', 'done')], order='date desc'):
                    quantity_awal.append(move.qty_done)

                # delivery order
                for move in self.env['stock.move.line'].search(
                        [('location_id', '=', location_line.get('location_id')),
                         ('location_dest_id', '=', location_customer.id),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', '=', 'done')]):
                    quantity_sale.append(move.qty_done)

                for move in self.env['stock.move.line'].search(
                        [('location_id', '=', location_customer.id),
                         ('location_dest_id', '=', location_line.get('location_id')),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', '=', 'done')]):
                    quantity_return_sale.append(move.qty_done)

                # Receipt
                for move in self.env['stock.move.line'].search(
                        [('location_id', '=', location_vendor.id),
                         ('location_dest_id', '=', location_line.get('location_id')),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', '=', 'done')]):
                    quantity_purchase.append(move.qty_done)

                for move in self.env['stock.move.line'].search(
                        [('location_id', '=', location_line.get('location_id')),
                         ('location_dest_id', '=', location_vendor.id),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', '=', 'done')]):
                    quantity_return_purchase.append(move.qty_done)

                for move in self.env['stock.move.line'].search(
                        [('location_id', '=', location_loss.id),
                         ('location_dest_id', '=', location_line.get('location_id')),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', '=', 'done')]):
                    quantity_adjust_plus.append(move.qty_done)

                for move in self.env['stock.move.line'].search(
                        [('location_id', '=', location_line.get('location_id')),
                         ('location_dest_id', '=', location_loss.id),
                         ('date', '>=', from_date),
                         ('date', '<=', to_date),
                         ('state', '=', 'done')]):
                    quantity_adjust_minus.append(move.qty_done)

                for quant in self.env['stock.quant'].search(
                        [('location_id', '=', location_line.get('location_id'))]):
                    quantity_akhir.append(quant.quantity)
            if len(quantity_awal) <= 0:
                location_line['qty_awal'] += 0.0
            elif len(quantity_awal) >= 1:
                location_line['qty_awal'] += quantity_awal[-1]

            location_line['qty_sale'] += sum(quantity_sale)
            location_line['qty_return_sale'] += sum(quantity_return_sale)
            location_line['qty_purchase'] += sum(quantity_purchase)
            location_line['qty_return_purchase'] += sum(quantity_return_purchase)
            location_line['qty_adjust_plus'] += sum(quantity_adjust_plus)
            location_line['qty_adjust_minus'] += sum(quantity_adjust_minus)
            location_line['qty_akhir'] += sum(quantity_akhir)

            location_lines += [location_line]

        # if location_lines:
        #     print(location_lines)

        return {
            'data': data,
            'location_lines': location_lines,
            'report_date': datetime.datetime.now().strftime("%Y-%m-%d"),
        }
