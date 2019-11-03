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
        # defaults = self.default_get(['name', 'picking_type_id'])
        picking_cmt_consume = self.env.ref('textile_assembly.picking_cmt_consume')
        picking_cmt_produce = self.env.ref('textile_assembly.picking_cmt_produce')
        wh_stock = self.env.ref('stock.stock_location_stock')
        store_stock = self.env['stock.location'].search([('usage', '=', 'internal'),
                                                         ('company_id', '=', [self.env.user.company_id.id, False]),
                                                         ('id', '!=', wh_stock.id)])
        transit_location = self.env['stock.location'].search(
            [('usage', '=', 'transit'),
             ('company_id', '=', [self.env.user.company_id.id, False]),
             ('location_id', '=', self.env.ref('stock.stock_location_locations').id)
             ])
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
        if operation.code == 'internal' and operation.id == picking_cmt_consume.id:
            if vals.get('product_select_type', 'materials') == 'materials':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.picking.materials_outgoing')
        if operation.code == 'internal' and operation.id == picking_cmt_produce.id:
            if vals.get('product_select_type', 'goods') == 'goods':
                vals['name'] = self.env['ir.sequence'].next_by_code('stock.picking.goods_incoming')
        if operation.code == 'internal' and operation.id not in [picking_cmt_consume.id, picking_cmt_produce.id]:
            if operation.warehouse_id.id == 1 and \
                    vals.get('location_id') == wh_stock.id and \
                    vals.get('location_dest_id') in store_stock.ids:
                vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.wh.store')
            elif operation.warehouse_id.id != 1 \
                    and vals.get('location_id') in store_stock.ids \
                    and vals.get('location_dest_id') == wh_stock.id:
                vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.store.wh')
            elif operation.warehouse_id.id == 1 \
                    and vals.get('location_id') in store_stock.ids \
                    and vals.get('location_dest_id') == wh_stock.id:
                vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.store.wh')
            elif operation.warehouse_id.id != 1 \
                    and vals.get('location_id') in store_stock.ids \
                    and vals.get('location_dest_id') in store_stock.ids:
                vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.store.store')
            elif operation.warehouse_id.id == 1 \
                    and vals.get('location_id') == wh_stock.id \
                    and vals.get('location_dest_id') == transit_location.id:
                vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.transit.out')
            elif operation.warehouse_id.id == 1 \
                    and vals.get('location_id') == transit_location.id \
                    and vals.get('location_dest_id') == wh_stock.id:
                vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.transit.in')
            elif operation.warehouse_id.id != 1 \
                    and vals.get('location_id') in store_stock.ids \
                    and vals.get('location_dest_id') == transit_location.id:
                vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.transit.out')
            elif operation.warehouse_id.id != 1 \
                    and vals.get('location_id') == transit_location.id \
                    and vals.get('location_dest_id') == store_stock.ids:
                vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.transit.in')

        return super(StockPicking, self).create(vals)


class StockMove(models.Model):
    _inherit = 'stock.move'

    product_select_type = fields.Selection(string="Jenis Produk",
                                           selection=[('materials', 'Materials'),
                                                      ('goods', 'Goods'), ],
                                           index=True, copy=True, track_visibility='onchange')

    internal_transfer_type_name = fields.Char(string="Internal Transfer Type",
                                              compute="_compute_internal_transfer_name")

    @api.depends('picking_id')
    def _compute_internal_transfer_name(self):
        for move in self:
            picking_name = move.picking_id.name.split(sep='/')
            origin = move.picking_id.origin.split(sep='/')
            if move.picking_id and move.picking_id.picking_type_code == 'internal':
                if picking_name[0] == 'SJ':
                    move.internal_transfer_type_name = 'SJ'
                elif picking_name[0] == 'SMB':
                    move.internal_transfer_type_name = 'SMB'
                elif picking_name[0] == 'SRB':
                    move.internal_transfer_type_name = 'SRB'
                elif origin:
                    move.internal_transfer_type_name = origin[0].strip()

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



