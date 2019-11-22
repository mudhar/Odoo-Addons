from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_description = fields.Char(string="Description")


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    @api.model
    def _prepare_order_line_procurement(self, order, line, group_id=False):
        vals = super(SaleOrder, self)._prepare_order_line_procurement(
            order, line, group_id=group_id)
        vals['product_description'] = line.name
        return vals
