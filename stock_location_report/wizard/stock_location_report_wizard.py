# -*- coding: utf-8 -*-
import datetime
from _datetime import datetime as datetimes
from dateutil.relativedelta import relativedelta
from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockLocationReport(models.TransientModel):
    _name = "stock_location_report.report"
    _description = 'Stock Location Report'

    @api.model
    def _get_from_date(self):
        company = self.env.user.company_id
        current_date = datetime.date.today()
        from_date = company.compute_fiscalyear_dates(current_date)['date_from']
        return from_date

    @api.model
    def _get_default_location_stock(self):
        wh_stock = self.env.ref('stock.stock_location_stock')
        return self.env['stock.location'].search(
            [('usage', '=', 'internal'),
             ('company_id', 'in', [self.env.user.company_id.id, False]),
             ('id', '!=', wh_stock.id)]).ids

    before_date = fields.Date(string="Before Date")
    after_date = fields.Date(string="Before Date")
    from_date = fields.Date(string='From Date', default=_get_from_date, required=True)
    to_date = fields.Date(string='To Date', default=fields.Date.context_today, required=True)
    company = fields.Many2one('res.company', string='Company', required=True,
                              default=lambda self: self.env.user.company_id.id)
    location_stock_ids = fields.Many2many(comodel_name="stock.location",
                                          string="Location Stock", default=_get_default_location_stock)

    @api.onchange('from_date')
    def _onchange_from_date(self):
        before_date = self._get_default_date_from_date()
        self.update({'before_date': before_date})

    @api.onchange('to_date')
    def _onchange_to_date(self):
        after_date = self._get_default_date_to_date()
        self.update({'after_date': after_date})

    def _get_default_date_from_date(self):
        from_date = fields.Datetime.from_string(self.from_date)
        before_date = (from_date - relativedelta(days=1))
        to_string = fields.Date.to_string(before_date)
        return to_string

    def _get_default_date_to_date(self):
        to_date = fields.Datetime.from_string(self.to_date)
        after_date = (to_date + relativedelta(days=1))
        to_string = fields.Date.to_string(after_date)
        return to_string

    def print_pdf_report(self, data):
        data = dict()
        data['form'] = {}
        data['form'].update(self.read([])[0])
        return self.env.ref('stock_location_report.action_stock_location_report_pdf').with_context(
            landscape=True).report_action(self, data=data)
