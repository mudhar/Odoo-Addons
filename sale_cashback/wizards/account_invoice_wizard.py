from openerp import models, fields, api, _


class AccountInvoiceWizard(models.TransientModel):

    """Update Cash Back On Account Invoice"""
    _name = 'account_invoice.wizard'

    @api.multi
    def action_set_cash_back(self):
        active_ids = self._context.get('active_ids')
        invoice_ids = self.env['account.invoice']
        for invoice in invoice_ids.browse(active_ids):
            move_id = invoice.invoice_line.mapped('move_id')
            assert len(move_id) == 1
            sale_id = self.env['sale.order'].search([('procurement_group_id', '=', move_id.group_id.id)])
            invoice.update({'cash_back': sum(sale_id.mapped('cash_back'))})
        return {'type': 'ir.actions.act_window_close'}





