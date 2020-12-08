# -*- coding: utf-8 -*-
import calendar
from odoo import fields, models, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    @api.model
    def create(self, vals):
        sequence_object = self.env['ir.sequence']
        if vals.get('product_select_type', 'materials') == 'materials':
            sequence_id = sequence_object.search([('code', '=', 'purchase.order.materials')])
            if sequence_id.use_date_range and vals.get('date_order'):
                # 2020-01-10
                date_to = fields.Date.from_string(vals.get('date_order'))
                dt_from, dt_to = sequence_object._format_date_range_seq(date_to)
                date_to_string = date_to.strftime('%Y-%m-%d')
                date_range = sequence_object._find_date_range_seq(date_to_string, sequence_id)
                if not date_range:
                    seq_date = sequence_object.act_create_date_range_seq(dt_from, dt_to, sequence_id)
                    # seq_prefix
                    vals['name'] = sequence_object._create_sequence_prefix(sequence_id, seq_date)
                else:
                    # seq_prefix
                    vals['name'] = sequence_object._create_sequence_prefix(sequence_id, date_range)

        if vals.get('product_select_type', 'goods') == 'goods':
            sequence_id = sequence_object.search([('code', '=', 'purchase.order.goods')])
            if sequence_id.use_date_range and vals.get('date_order'):
                # 2020-01-10
                date_to = fields.Date.from_string(vals.get('date_order'))
                dt_from, dt_to = sequence_object._format_date_range_seq(date_to)
                date_to_string = date_to.strftime('%Y-%m-%d')
                date_range = sequence_object._find_date_range_seq(date_to_string, sequence_id)
                if not date_range:
                    seq_date = sequence_object.act_create_date_range_seq(dt_from, dt_to, sequence_id)
                    # seq_prefix
                    vals['name'] = sequence_object._create_sequence_prefix(sequence_id, seq_date)
                else:
                    # seq_prefix
                    vals['name'] = sequence_object._create_sequence_prefix(sequence_id, date_range)

        return super(PurchaseOrder, self).create(vals)


