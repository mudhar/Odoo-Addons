# -*- coding: utf-8 -*-
import csv
import base64
from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class PurchaseOrderImport(models.TransientModel):
    _name = 'purchase_order.import'
    _description = 'Import CSV To Purchase Line'

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
    def _import_purchase_line_import(self):
        purchase_id = self._context.get('active_id')
        purchase_order_object = self.env['purchase.order']
        purchase_ids = purchase_order_object.search_read(domain=[('id', '=', purchase_id)])
        order_line = self.env['purchase.order.line']
        if purchase_ids[0].get('state') == 'draft':
            bs64 = base64.decodebytes(self.data_file).decode('utf-8')
            reader = csv.DictReader(bs64.split('\n'), delimiter=',')

            for row in reader:
                formatted_dict = dict(row)
                product_id = self._find_product(formatted_dict.get('Product'))
                if not product_id:
                    raise ValidationError(_("Product With Barcode %s Not Found") % formatted_dict.get('Product'))

                if product_id:
                    line_items = dict()

                    name = product_id[0].get('partner_ref')
                    if product_id[0].get('description_purchase'):
                        name += '\n' + product_id[0].get('description_purchase')

                    line_items['name'] = name
                    line_items['product_id'] = product_id[0].get('id')
                    line_items['product_qty'] = formatted_dict.get('quantity')
                    line_items['product_uom'] = product_id[0].get('uom_po_id')[0]
                    line_items['price_unit'] = formatted_dict.get('Price')
                    line_items['taxes_id'] = [(6, 0, product_id[0].get('supplier_taxes_id'))]
                    line_items['date_planned'] = purchase_ids[0].get('date_planned')
                    line_items['order_id'] = purchase_id

                    order_line.create(line_items)
            return True

    @api.multi
    def import_file(self):
        if self.file_name:
            if not self._check_csv_file(self.file_name):
                raise ValidationError(_("Unsupported File Format, Import Only Supports CSV"))
            return self._import_purchase_line_import()
        else:
            raise ValidationError(_("Please Select The CSV File"))
