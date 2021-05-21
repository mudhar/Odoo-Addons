from odoo import models, fields


class ResConfigSettings(models.TransientModel):
    """
    The fields are used as reference on column report payable
    """
    _inherit = 'res.config.settings'

    period_manual_report = fields.Boolean(
        string='Custom Periodic Report', config_parameter='aging_payable_period.period_manual_report')

    column1_from = fields.Integer(
        'Column 1 - From', related='company_id.column1_from', readonly=False)
    column1_to = fields.Integer(
        'Column 1 - To', related='company_id.column1_to', readonly=False)
    column2_from = fields.Integer(
        'Column 2 - From', related='company_id.column2_from', readonly=False)
    column2_to = fields.Integer(
        'Column 2 - To', related='company_id.column2_to', readonly=False)
    column3_from = fields.Integer(
        'Column 3 - From', related='company_id.column3_from', readonly=False)
    column3_to = fields.Integer(
        'Column 3 - To', related='company_id.column3_to', readonly=False)
    column4_from = fields.Integer(
        'Column 4 - From', related='company_id.column4_from', readonly=False)
    column4_to = fields.Integer(
        'Column 4 - To', related='company_id.column4_to', readonly=False)






