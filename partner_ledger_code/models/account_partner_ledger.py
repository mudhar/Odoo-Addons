from odoo import models, api


class ReportPartnerLedger(models.AbstractModel):
    """
    Update Value column move line
    """
    _inherit = 'account.partner.ledger'

    @api.model
    def _get_report_line_move_line(self, options, partner, aml, cumulated_init_balance, cumulated_balance):
        result = super(ReportPartnerLedger, self)._get_report_line_move_line(options, partner, aml,
                                                                             cumulated_init_balance, cumulated_balance)
        # check length
        # update dict['columns']
        # value aml['account_code'] + aml['account_name']
        if len(result):
            for col in result['columns']:
                if col['name'] == aml['account_code']:
                    col['name'] = aml['account_code'] + ' ' + aml['account_name']
        return result
