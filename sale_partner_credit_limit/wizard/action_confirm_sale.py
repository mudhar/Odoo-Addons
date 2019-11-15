from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError


class SaleOrderConfirm(models.TransientModel):

    """ Confirm All Draft Sale Order"""
    _name = 'sale_order_confirm.wizard'

    @api.multi
    def action_confirm_sale_order(self):
        active_ids = self._context.get('active_ids')
        sale_ids = self.env['sale.order']
        for sale in sale_ids.browse(active_ids):
            self._check_product_supplier(sale)
            if sale.state == 'draft':
                sale.action_button_confirm()
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def _check_product_supplier(self, sale):
        for line in sale.order_line:
            if line.product_id and line.product_id.seller_ids:
                raise UserError(_("Sale Order %s Ada Supplier Dalam Produk") % sale.name)
        return True





