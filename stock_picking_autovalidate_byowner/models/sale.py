from odoo import models, fields, api
from odoo.tools import float_is_zero


class SaleOrder(models.Model):
    """
    inherit sale order
    """
    _inherit = 'sale.order'

    def action_confirm(self):
        """
        check if there is a picking. validate stock move which have a owner id
        :return: True
        """
        result = super(SaleOrder, self).action_confirm()
        for order in self:
            if order.picking_ids:
                move_to_do = order.picking_ids.mapped('move_lines')
                for move_line in move_to_do.mapped('move_line_ids').filtered(
                        lambda x: x.state == 'assigned' and x.owner_id):
                    # check if quantity is empty
                    if float_is_zero(move_line.qty_done, precision_rounding=move_line.product_uom_id.rounding):
                        move_line.qty_done = move_line.product_uom_qty
                move_to_do._action_done()
        return result


class SaleOrderLine(models.Model):
    """
    inherit sale order line and add a new field
    """
    _inherit = 'sale.order.line'

    owner_id = fields.Many2one(comodel_name='res.partner', string='Owner')

    @api.onchange('product_id')
    def product_id_change(self):
        """
        if vendor exist on product then update the value of owner
        :return:
        """
        if self.product_id and self.product_id.seller_ids:
            self.update({'owner_id': self.product_id.seller_ids[0].name.id})
        return super(SaleOrderLine, self).product_id_change()


