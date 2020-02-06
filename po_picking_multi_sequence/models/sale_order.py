from odoo import api, fields, models


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    product_select_type = fields.Selection(string="Report Type",
                                           selection=[('materials', 'Materials'),
                                                      ('goods', 'Goods'), ], default='goods',
                                           help="Reference Picking Name",
                                           index=True, copy=True, track_visibility='onchange', required=True)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.multi
    def _prepare_procurement_values(self, group_id=False):
        values = super(SaleOrderLine, self)._prepare_procurement_values(group_id)
        values.update({'product_select_type': self.order_id.product_select_type})
        return values

    @api.multi
    @api.onchange('product_id')
    def product_id_change(self):
        result = super(SaleOrderLine, self).product_id_change()
        if self.order_id.product_select_type:
            if self.order_id.product_select_type == 'materials':
                result['domain'] = {'product_id': [('product_tmpl_id.is_materials', '=', True)]}
            elif self.order_id.product_select_type == 'goods':
                result['domain'] = {'product_id': [('product_tmpl_id.is_goods', '=', True)]}
        return result

