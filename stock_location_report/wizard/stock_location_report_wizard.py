# -*- coding: utf-8 -*-
import datetime
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
        return self.env['stock.location'].search(
            [('usage', '=', 'internal'), ('company_id', 'in', [self.env.user.company_id.id, False])]).ids

    from_date = fields.Date(string='From Date', default=_get_from_date, required=True)
    to_date = fields.Date(string='To Date', default=fields.Date.context_today, required=True)
    company = fields.Many2one('res.company', string='Company', required=True,
                              default=lambda self: self.env.user.company_id.id)
    location_stock_ids = fields.Many2many(comodel_name="stock.location",
                                          string="Location Stock", default=_get_default_location_stock)

    def print_pdf_report(self, data):
        data = {}
        data['form'] = {}
        data['form'].update(self.read([])[0])
        return self.env.ref('stock_location_report.action_stock_location_report_pdf').with_context(
            landscape=True).report_action(self, data=data)
