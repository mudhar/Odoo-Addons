from odoo import fields, models


class StockMove(models.Model):
    """
    inherit stock move
    """
    _inherit = 'stock.move'

    def _prepare_move_line_vals(self, quantity=None, reserved_quant=None):
        """
        check if sale and quants exist. if both of them exists update value owner of quant
        :param quantity: quantity reserved
        :param reserved_quant: object quant
        :return: values dict
        """
        if self.sale_line_id and reserved_quant:
            reserved_quant.update({'owner_id': self.sale_line_id.owner_id.id})
        result = super(StockMove, self)._prepare_move_line_vals(quantity=quantity, reserved_quant=reserved_quant)
        if self.sale_line_id and not result.get('owner_id'):
            result.update({'owner_id': self.sale_line_id.owner_id.id})
        return result


class StockMoveLine(models.Model):
    """
    inherit stock_move_line and add attribute default to field owner_id
    """
    _inherit = 'stock.move.line'

    def _default_owner_id(self):
        """
        if move_id and sale_line_id exist then link sale_line_id owner_id
        :return: id
        """
        if self.env.context.get('active_model') == 'stock.move':
            move_id = self.env['stock.move'].browse(self.env.context.get('default_move_id'))
            if move_id and move_id.sale_line_id:
                return move_id.sale_line_id.owner_id

    owner_id = fields.Many2one(default=_default_owner_id)


