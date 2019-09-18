from odoo import api, fields, models


class MrpSelectReport(models.TransientModel):
    _name = 'mrp_production.select_report'
    _description = 'Wizard Untuk Menampilkan View Report Yang Diingingkan'

    report_type = fields.Selection(string="Jenis Report",
                                   selection=[('workorder report', 'Work Order Report'),
                                              ('work in process', 'Work In Process'), ])

    @api.multi
    def open_workorder_view_pivot(self):
        self.ensure_one()
        action = self.env.ref('mrp_daily_report.action_mrp_workorder_view_report').read()[0]
        return action

    @api.multi
    def open_wip_view_pivot(self):
        self.ensure_one()
        action = self.env.ref('mrp_daily_report.action_mrp_wip_view_report').read()[0]
        return action

    @api.multi
    def action_confirm(self):
        self.ensure_one()
        if self.report_type == 'workorder report':
            return self.open_workorder_view_pivot()
        if self.report_type == 'work in process':
            return self.open_wip_view_pivot()
        # return {'type': 'ir.actions.act_window_close'}