# -*- coding: utf-8 -*-
import csv
import io
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
        product_ids = product_object.search([('barcode', '=', values)])
        return product_ids

    @api.multi
    def import_file_check(self):
        keys = ['product', 'quantity', 'price', 'tax', 'date']
        csv_data = base64.b64decode(self.data_file)
        data_file = io.StringIO(csv_data.decode("utf-8"))
        data_file.seek(0)
        file_reader = []
        csv_reader = csv.reader(data_file, delimiter=',')
        try:
            file_reader.extend(csv_reader)
        except Exception:
            raise ValidationError(_("Invalid File"))
        for i in range(len(file_reader)):
            field = list(map(str, file_reader[i]))
            values = dict(zip(keys, field))
            if values:
                if i == 0:
                    continue
                else:
                    self.create_order_line(values)
        return True

    @api.multi
    def create_order_line(self, values):
        purchase_id = self.env['purchase.order'].browse(self._context.get('active_id'))
        purchase_lines = self.env['purchase.order.line']
        product_id = self._find_product(values.get('product'))
        tax_id_lst = list()
        if values.get('tax'):
            if ';' in values.get('tax'):
                tax_names = values.get('tax').split(';')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise ValidationError(_('"%s" Tax not in your system') % name)
                    tax_id_lst.append(tax.id)

            elif ',' in values.get('tax'):
                tax_names = values.get('tax').split(',')
                for name in tax_names:
                    tax = self.env['account.tax'].search([('name', '=', name), ('type_tax_use', '=', 'purchase')])
                    if not tax:
                        raise ValidationError(_('"%s" Tax not in your system') % name)
                    tax_id_lst.append(tax.id)
            else:
                tax_names = values.get('tax').split(',')
                tax = self.env['account.tax'].search([('name', '=', tax_names), ('type_tax_use', '=', 'purchase')])
                if not tax:
                    raise ValidationError(_('"%s" Tax not in your system') % tax_names)
                tax_id_lst.append(tax.id)

        if purchase_id.order_line and purchase_id.state in ['draft', 'sent']:
            for line in purchase_id.order_line.filtered(
                    lambda l: l.product_id == product_id and l.product_uom == product_id.uom_po_id):
                new_values = self._update_order_line(values, line)
                line.write(new_values)
            if product_id not in purchase_id.order_line.mapped('product_id'):
                line_data = self._create_order_line(purchase_id, product_id, values)
                purchase_lines |= self.env['purchase.order.line'].create(line_data)

        if not purchase_id.order_line:
            if purchase_id.state == 'draft' and product_id:
                line_data = self._create_order_line(purchase_id, product_id, values)
                purchase_lines |= self.env['purchase.order.line'].create(line_data)

            elif purchase_id.state == 'sent' and product_id:
                line_data = self._create_order_line(purchase_id, product_id, values)
                purchase_lines |= self.env['purchase.order.line'].create(line_data)

        if tax_id_lst:
            purchase_lines.write({'taxes_id': ([(6, 0, tax_id_lst)])})
        else:
            purchase_lines.write({'taxes_id': [(6, 0, product_id.supplier_taxes_id.ids)]})

        return True

    def _update_order_line(self, values, line):
        return {
            'product_qty': float(values.get('quantity')) + line.product_qty
        }

    def _create_order_line(self, purchase_id, product_id, values):
        date = purchase_id.date_planned
        if values.get('date'):
            date = values.get('date')
        if not date:
            date = purchase_id.date_order

        return {
            'order_id': purchase_id.id,
            'date_planned': date,
            'name': product_id.name,
            'product_id': product_id.id,
            'product_uom': product_id.uom_po_id.id,
            'product_qty': values.get('quantity'),
            'price_unit': values.get('price') if values.get('price') else product_id.lst_price,
        }

    @api.multi
    def import_file(self):
        if self.file_name:
            if not self._check_csv_file(self.file_name):
                raise ValidationError(_("Unsupported File Format, Import Only Supports CSV"))
            return self.import_file_check()
        else:
            raise ValidationError(_("Please Select The CSV File"))
