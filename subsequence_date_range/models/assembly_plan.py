# -*- coding: utf-8 -*-
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _


class AssemblyPlan(models.Model):
    _inherit = 'assembly.plan'

    @api.model
    def create(self, values):
        sequence_id = self.env['ir.sequence'].search([('code', '=', 'assembly.plan')])
        if values.get('assembly_id') and sequence_id.use_date_range:
            partner_id = self.env['res.partner'].browse(values.get('partner_id'))
            date_to = self._get_assembly_date(values['date_planned_finished'])
            date_to_string = date_to.strftime('%Y-%m-%d')
            # 2020-01-01
            date_range = self.env['ir.sequence']._find_date_range_seq(sequence_id, date_to_string)
            dt_from, dt_to = self.env['ir.sequence']._format_date_range_seq(date_to)
            if not date_range:
                seq_date = self.env['ir.sequence'].act_create_date_range_seq(dt_from, dt_to, sequence_id)
                seq_prefix = self.env['ir.sequence']._create_sequence_prefix(sequence_id, seq_date)

                values['name'] = self._create_assembly_plan_prefix(partner_id, seq_prefix)
            else:
                seq_prefix = self.env['ir.sequence']._create_sequence_prefix(sequence_id, date_range)
                values['name'] = self._create_assembly_plan_prefix(partner_id, seq_prefix)

        return super(AssemblyPlan, self).create(values)

    @api.multi
    def _create_assembly_plan_prefix(self, partner_id, seq_prefix):
        return ''.join('%s/%s' % (partner_id.partner_cmt_code, seq_prefix))

    def _get_assembly_date(self, date):
        order_date = fields.Datetime.from_string(date)
        return order_date + relativedelta(days=1)

