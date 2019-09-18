from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    # product_select_type = fields.Selection(string="Jenis Produk", related="move_lines.product_select_type")

    product_select_type = fields.Selection(string="Jenis Produk",
                                           selection=[('materials', 'Materials'),
                                                      ('goods', 'Goods'), ],
                                           index=True, copy=True, track_visibility='onchange')

    @api.model
    def create(self, vals):
        operation = self.env['stock.picking.type'].browse(vals.get('picking_type_id'))
        if operation.code == 'incoming':
            if vals.get('product_select_type', 'materials') == 'materials':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.picking.materials_incoming')
            elif vals.get('product_select_type', 'goods') == 'goods':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.picking.goods_incoming')
        if operation.code == 'outgoing':
            if vals.get('product_select_type', 'materials') == 'materials':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.picking.materials_outgoing')
            elif vals.get('product_select_type', 'goods') == 'goods':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.picking.goods_outgoing')
        if operation.code == 'internal':
            if vals.get('product_select_type', 'materials') == 'materials':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.picking.materials_outgoing')
            elif vals.get('product_select_type', 'goods') == 'goods':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.picking.goods_incoming')

        return super(StockPicking, self).create(vals)


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_select_type = fields.Selection(string="Jenis Produk",
                                           selection=[('materials', 'Materials'),
                                                      ('goods', 'Goods'), ],
                                           index=True, copy=True, track_visibility='onchange')

    def _get_new_picking_values(self):
        res = super(StockMove, self)._get_new_picking_values()
        if self.sale_line_id and self.product_select_type:
            res.update({'product_select_type': self.product_select_type})
        return res


class ProcurementRule(models.Model):
    _inherit = 'procurement.rule'

    def _get_stock_move_values(self, product_id, product_qty, product_uom, location_id, name, origin, values, group_id):
        result = super(ProcurementRule, self)._get_stock_move_values(product_id, product_qty, product_uom, location_id, name, origin, values, group_id)
        if values.get('product_select_type', False) and values.get('sale_line_id', False):
            result['product_select_type'] = values['product_select_type']
        return result



