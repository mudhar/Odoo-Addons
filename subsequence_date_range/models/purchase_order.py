# -*- coding: utf-8 -*-
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo import fields, models, api
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        if vals.get('product_select_type', 'materials') == 'materials':
            sequence_id = self.env['ir.sequence'].search([('code', '=', 'purchase.order.materials')])
            if sequence_id.use_date_range and vals.get('date_order'):
                # 2020-01-10
                date_to = self._get_purchase_date_order(vals['date_order'])
                dt_from, dt_to = self.env['ir.sequence']._format_date_range_seq(date_to)
                # date_to_string = date_to.strftime('%Y-%m-%d')
                date_range = self.env['ir.sequence']._find_date_range_seq(sequence_id, date_to)
                if not date_range:
                    seq_date = self.env['ir.sequence'].act_create_date_range_seq(dt_from, dt_to, sequence_id)
                    # seq_prefix
                    vals['name'] = self.env['ir.sequence']._create_sequence_prefix(sequence_id, seq_date)
                else:
                    # seq_prefix
                    vals['name'] = self.env['ir.sequence']._create_sequence_prefix(sequence_id, date_range)

        if vals.get('product_select_type', 'goods') == 'goods':
            sequence_id = self.env['ir.sequence'].search([('code', '=', 'purchase.order.goods')])
            if sequence_id.use_date_range and vals.get('date_order'):
                # 2020-01-10
                date_to = self._get_purchase_date_order(vals['date_order'])
                dt_from, dt_to = self.env['ir.sequence']._format_date_range_seq(date_to)
                # date_to_string = date_to.strftime('%Y-%m-%d')
                date_range = self.env['ir.sequence']._find_date_range_seq(sequence_id, date_to)
                if not date_range:
                    seq_date = self.env['ir.sequence'].act_create_date_range_seq(dt_from, dt_to, sequence_id)
                    # seq_prefix
                    vals['name'] = self.env['ir.sequence']._create_sequence_prefix(sequence_id, seq_date)
                else:
                    # seq_prefix
                    vals['name'] = self.env['ir.sequence']._create_sequence_prefix(sequence_id, date_range)

        return super(PurchaseOrder, self).create(vals)

    def _get_purchase_date_order(self, date):
        purchase_date = fields.Date.from_string(date)
        if purchase_date:
            date_order = purchase_date + relativedelta(days=1)
            return date_order.strftime(DEFAULT_SERVER_DATE_FORMAT)



