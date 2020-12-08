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
                dt_from, dt_to = self._format_date_range_seq(date_to)
                date_to_string = date_to.strftime('%Y-%m-%d')
                date_range = self._find_date_range_seq(date_to_string, sequence_id)
                if not date_range:
                    seq_date = self._create_date_range_seq(dt_from, dt_to, sequence_id)
                    # seq_prefix
                    vals['name'] = self.env['assembly.plan']._create_sequence_prefix(sequence_id, seq_date)
                else:
                    # seq_prefix
                    vals['name'] = self.env['assembly.plan']._create_sequence_prefix(sequence_id, date_range)

        return super(PurchaseOrder, self).create(vals)

    def _format_date_range_seq(self, date_to):
        year = date_to.year
        month = date_to.month
        days = calendar.monthrange(year, month)
        date_from = '{}-{}-01'.format(year, month)
        date_to = '{}-{}-{}'.format(year, month, days[1])
        return date_from, date_to

    def _create_date_range_seq(self, dt_from, dt_to, sequence_id):
        return self.env['ir.sequence.date_range'].create({
            'sequence_id': sequence_id.id,
            'date_from': dt_from,
            'date_to': dt_to
        })

    def _find_date_range_seq(self, date_to_string, sequence_id):
        return self.env['ir.sequence.date_range'].search(
            [('sequence_id', '=', sequence_id.id), ('date_from', '<=', date_to_string),
             ('date_to', '>=', date_to_string)], order='date_to desc', limit=1)


