# -*- coding: utf-8 -*-
import calendar
from odoo import models, api, fields


class IrSequence(models.Model):
    _inherit = 'ir.sequence'

    @api.multi
    def _create_sequence_prefix(self, sequence_id, seq_date):
        return sequence_id.with_context(ir_sequence_date=seq_date.date_to)._next()

    @api.multi
    def _format_date_range_seq(self, date_to):
        date_format = fields.Date.from_string(date_to)
        year = date_format.year
        month = date_format.month
        days = calendar.monthrange(year, month)
        date_from = '{}-{}-01'.format(year, month)
        date_to = '{}-{}-{}'.format(year, month, days[1])
        return date_from, date_to

    @api.multi
    def _find_date_range_seq(self, sequence_id, date):
        return self.env['ir.sequence.date_range'].search(
            [('sequence_id', '=', sequence_id.id), ('date_from', '<=', date), ('date_to', '>=', date)],
            order='date_to desc', limit=1)

    @api.multi
    def act_create_date_range_seq(self, dt_from, dt_to, sequence_id):
        return self.env['ir.sequence.date_range'].create({
            'sequence_id': sequence_id.id,
            'date_from': dt_from,
            'date_to': dt_to
        })
