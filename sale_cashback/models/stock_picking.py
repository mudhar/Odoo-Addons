from openerp import models, fields, api, _


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def _get_invoice_vals(self, key, inv_type, journal_id, move):
        result = super(StockPicking, self)._get_invoice_vals(key, inv_type, journal_id, move)
        context = self.env.context
        picking_ids = self.env['stock.picking'].browse(context['active_ids'])
        group_ids = picking_ids.mapped('group_id')

        partner, currency_id, company_id, user_id = key
        if move.group_id and partner:
            sale_ids = self.env['sale.order'].search(
                [('procurement_group_id', 'in', group_ids.ids),
                 ('partner_id', '=', partner.id),
                 ('company_id', '=', company_id)])
            result.update({'cash_back': sum(sale_ids.mapped('cash_back'))})

        return result

