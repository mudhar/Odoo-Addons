from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.one
    @api.depends('price_subtotal',
                 'product_uom_qty',
                 'tax_id',
                 'price_unit')
    def _get_price_reduce(self):
        if self.price_subtotal > 0.0:
            self.price_reduce = self.price_subtotal / self.product_uom_qty
        else:
            self.price_reduce = 0.0

    price_reduce = fields.Float(old_name="price_reduce", string="Price Reduce", store=True,
                                digits_compute=dp.get_precision('Product Price'), compute="_get_price_reduce")







