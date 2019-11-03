from openerp import models, fields, api, _


class AccountInvoiceWizard(models.TransientModel):

    """Update Cash Back On Account Invoice"""
    _name = 'account_invoice.wizard'

    @api.multi
    def action_set_cash_back(self):
        active_ids = self._context.get('active_ids')
        invoice_ids = self.env['account.invoice']
        for invoice in invoice_ids.browse(active_ids):
            move_ids = invoice.invoice_line.mapped('move_id')
            group_ids = move_ids.mapped('group_id')
            sale_ids = self.env['sale.order'].search(
                [('procurement_group_id', 'in', group_ids.ids),
                 ('partner_id', '=', invoice.partner_id.id),
                 ('company_id', '=', invoice.company_id.id),
                 ('state', 'not in', ('cancel', 'draft'))])

            invoice.update({'cash_back': sum(sale_ids.mapped('cash_back'))})
        return {'type': 'ir.actions.act_window_close'}





