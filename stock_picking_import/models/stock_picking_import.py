# -*- coding: utf-8 -*-
import csv
import base64
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class StockPickingImport(models.TransientModel):
    _name = 'stock_picking.import'
    _description = 'Import CSV To Picking Line'

    data_file = fields.Binary(string="CSV File")
    file_name = fields.Char(string='Name')

    def _check_csv_file(self, data_file):
        return data_file.strip().endswith('.csv')

    def _find_product(self, values):
        product_object = self.env['product.product']
        domain = [('barcode', '=', values)]
        product_ids = product_object.search_read(domain=domain)
        return product_ids

    @api.multi
    def _import_stock_move_csv(self):
        picking_id = self._context.get('active_id')
        stock_picking_object = self.env['stock.picking']
        stock_picking_ids = stock_picking_object.search_read(domain=[('id', '=', picking_id)])
        stock_move_object = self.env['stock.move']
        if stock_picking_ids[0].get('state') == 'draft':
            location_id = stock_picking_ids[0].get('location_id')[0]
            location_dest_id = stock_picking_ids[0].get('location_dest_id')[0]
            picking_type_id = stock_picking_ids[0].get('picking_type_id')[0]
            company_id = stock_picking_ids[0].get('company_id')[0]

            bs64 = base64.decodebytes(self.data_file).decode('utf-8')
            reader = csv.DictReader(bs64.split('\n'), delimiter=',')

            for row in reader:
                formatted_dict = dict(row)

                product_ids = self._find_product(formatted_dict.get('Product'))
                if not product_ids:
                    raise ValidationError(_("Product With Barcode %s Not Found") % formatted_dict.get('Product'))

                if product_ids:
                    line_items = dict()
                    line_items['date_expected'] = stock_picking_ids[0].get('scheduled_date')
                    line_items['product_id'] = product_ids[0].get('id')
                    line_items['product_uom'] = product_ids[0].get('uom_id')[0]
                    line_items['product_uom_qty'] = formatted_dict.get('quantity')
                    line_items['price_unit'] = product_ids[0].get('standard_price')
                    line_items['origin'] = ''.join('%s:%s' % (
                        stock_picking_ids[0].get('name'), stock_picking_ids[0].get('origin')))
                    line_items['location_id'] = location_id
                    line_items['location_dest_id'] = location_dest_id
                    line_items['company_id'] = company_id
                    line_items['picking_type_id'] = picking_type_id
                    line_items['picking_id'] = picking_id
                    line_items['name'] = stock_picking_ids[0].get('name')
                    line_items['procure_method'] = 'make_to_stock'

                    stock_move_object.create(line_items)

            return True

    @api.multi
    def import_file(self):
        if self.file_name:
            if not self._check_csv_file(self.file_name):
                raise ValidationError(_("Unsupported File Format, Import Only Supports CSV"))
            return self._import_stock_move_csv()
        else:
            raise ValidationError(_("Please Select The CSV File"))