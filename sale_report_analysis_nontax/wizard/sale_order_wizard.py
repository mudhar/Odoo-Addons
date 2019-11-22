from openerp import models, fields, api, _


class SaleOrderLineWizard(models.TransientModel):

    """ Update Field price_reduce"""
    _name = 'sale_order_line.wizard'

    @api.multi
    def action_set_price_reduce(self):
        active_ids = self._context.get('active_ids')
        sale_ids = self.env['sale.order']
        for sale in sale_ids.browse(active_ids):
            for line in sale.order_line:
                line._get_price_reduce()
        return {'type': 'ir.actions.act_window_close'}





