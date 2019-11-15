from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError


class SaleOrder(models.Model):

    """ Remove Duplicate Line On MRP BOM"""
    _inherit = 'sale.order'

    @api.multi
    def action_button_confirm(self):
        result = super(SaleOrder, self).action_button_confirm()
        if self.partner_id.id != 1:
            if self.partner_id.credit + self.amount_total > self.partner_id.credit_limit:
                raise UserError(_("Partner %s Credit Limitnya Sudah Mencapai Batas %s")
                                % (self.partner_id.name, str(self.partner_id.credit_limit)))
        return result

    # @api.multi
    # def action_remove_duplicate(self):
    #     active_ids = self._context.get('active_ids')
    #     bom_ids = self.env['mrp.bom']
    #     for bom in bom_ids.browse(active_ids):
    #         for line in bom.bom_line_ids:
    #             lines = self.env['mrp.bom.line'].search_count(
    #                 [('product_id', '=', line.product_id.id),
    #                  ('bom_id', '=', line.bom_id.id)])
    #             if lines > 1:
    #                 line.unlink()
    #     return {'type': 'ir.actions.act_window_close'}
    #
    #



