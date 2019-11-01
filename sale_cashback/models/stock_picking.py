from openerp import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        result = super(StockPicking, self)._get_invoice_vals(key, inv_type, journal_id, move)
        if move.group_id:
            sale_id = self.env['sale.order'].search([('procurement_group_id', '=', move.group_id.id)])
            result.update({'cash_back': sum(sale_id.mapped('cash_back'))})
        return result

