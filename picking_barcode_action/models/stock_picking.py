import json

from odoo import models, _
from odoo.tools.safe_eval import safe_eval


class StockPicking(models.Model):
    """
    inherit model to create a method that used to find picking with barcode domain
    """
    _inherit = 'stock.picking'
    _description = 'Stock Picking'

    def picking_type_warning(self, barcode):
        """
        if barcode cannot found return warning message
        :param barcode:
        :return: context
        """
        action = self.env.ref('picking_barcode_action.stock_picking_find_action')
        result = action.read()[0]
        context = safe_eval(result['context'])
        context.update({
            'default_state': 'warning',
            'default_status': _("Picking with barcode %s cannot be found ") % barcode
        })
        result['context'] = json.dumps(context)
        return result

    def find_picking_by_barcode(self, barcode):
        """
        find picking type which has barcode
        :param barcode:
        :return: list
        """
        picking_type = self.env['stock.picking.type'].search([('barcode', '=', barcode)])
        if not picking_type:
            return self.picking_type_warning(barcode)
        picking_id = self.search(
            [('picking_type_id', '=', picking_type.id),
             ('state', '=', 'assigned')])
        action = self.env.ref('stock.action_picking_tree_ready')
        result = action.read()[0]
        result['views'] = [(False, 'tree'), (False, 'form')]
        result['domain'] = str([('id', 'in', picking_id.ids)])
        return result
