# -*- coding: utf-8 -*-
from datetime import datetime, timedelta
import calendar
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class AssemblyPlan(models.Model):
    _inherit = 'assembly.plan'

    @api.model
    def create(self, values):
        sequence_id = self.env['ir.sequence'].search([('code', '=', 'assembly.plan')])
        if values.get('assembly_id') and sequence_id.use_date_range:
            partner_id = self.env['res.partner'].browse(values.get('partner_id'))
            date_from = fields.Date.from_string(values.get('date_planned_start'))
            # 2019-12-01
            date_to = fields.Date.from_string(values.get('date_planned_finished'))
            # 2020-01-01
            year = date_to.year
            month = date_to.month
            # value range month
            days = calendar.monthrange(year, month)
            date_range = self._find_date_range_seq(sequence_id, date_to)
            if not date_range:
                date_from = '{}-{}-01'.format(year, month)
                date_to = '{}-{}-{}'.format(year, month, days[1])
                seq_date = self.env['ir.sequence.date_range'].create({
                    'sequence_id': sequence_id.id,
                    'date_from': date_from,
                    'date_to': date_to
                })
                seq_prefix = self._create_sequence_prefix(sequence_id, seq_date)

                values['name'] = self._create_assembly_plan_prefix(partner_id, seq_prefix)
            else:
                seq_prefix = self._create_sequence_prefix(sequence_id, date_range)
                values['name'] = self._create_assembly_plan_prefix(partner_id, seq_prefix)

        return super(AssemblyPlan, self).create(values)

    @api.multi
    def _create_sequence_prefix(self, sequence_id, seq_date):
        return sequence_id.with_context(ir_sequence_date=seq_date.date_to)._next()

    @api.multi
    def _create_assembly_plan_prefix(self, partner_id, seq_prefix):
        return ''.join('%s/%s' % (partner_id.partner_cmt_code, seq_prefix))

    @api.multi
    def _format_date_range_seq(self, date):
        year = date.year
        month = date.month
        # value range month
        days = calendar.monthrange(year, month)
        date_from = '{}-{}-01'.format(year, month)
        date_to = '{}-{}-{}'.format(year, month, days[1])
        return date_to, date_from

    @api.multi
    def _find_date_range_seq(self, sequence_id, date):
        return self.env['ir.sequence.date_range'].search(
            [('sequence_id', '=', sequence_id.id), ('date_from', '>=', date), ('date_to', '<=', date)],
            order='date_to desc', limit=1)
