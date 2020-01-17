from odoo import api, fields, models, _
from odoo.exceptions import UserError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'

    is_warehouse = fields.Boolean(string="Is Warehouse?")
    is_store = fields.Boolean(string="Is Store?")

    @api.constrains('is_warehouse', 'is_store')
    def _check_wh_store(self):
        for wh in self:
            if wh.is_warehouse and not wh.is_store:
                return True
            elif not wh.is_warehouse and wh.is_store:
                return True
            elif not wh.is_warehouse and not wh.is_store:
                raise UserError(_("Apakah Ini Warehouse Atau Store"))


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    product_select_type = fields.Selection(string="Jenis Produk",
                                           selection=[('materials', 'Materials'),
                                                      ('goods', 'Goods'), ],
                                           index=True, copy=True, track_visibility='onchange')

    picking_report_type = fields.Char(string="Internal Transfer Type",
                                      compute="_compute_picking_report_type")

    @api.depends('picking_type_code')
    def _compute_picking_report_type(self):
        for picking in self:
            picking_name = picking.name.split(sep='/')
            if picking_name[0] == 'SJ':
                picking.picking_report_type = 'SJ'
            elif picking_name[0] == 'SMB':
                picking.picking_report_type = 'SMB'
            elif picking_name[0] == 'SRB':
                picking.picking_report_type = 'SRB'
            elif picking_name[0] == 'STBJ':
                picking.picking_report_type = 'STBJ'
            elif picking_name[0] == 'STBN':
                picking.picking_report_type = 'STBN'
            elif picking_name[0] == 'SJPB':
                picking.picking_report_type = 'SJPB'
            else:
                return False

        return True

    @api.model
    def check_warehouse_type(self):
        wh_object = self.env['stock.warehouse']
        for wh in wh_object.search([]):
            if wh.is_warehouse and not wh.is_store:
                return True
            elif not wh.is_warehouse and wh.is_store:
                return True
            else:
                raise UserError(_("Warehouse %s Belum Dikonfigurasi Sebagai Gudang Atau Toko\n"
                                  "Harap Anda MengKonfigurasi Terlebih Dahulu Agar Memudahkan\n"
                                  "Penaman SJ, SRB, SMB\n")
                                % wh.display_name)
                
    @api.model
    def create(self, vals):
        # Cek Apakah Sudah Diceklis Identitas Warehouse
        # Digunakan Untuk Penamaan Internal Transfer SJ, SRB, SMB
        self.check_warehouse_type()
        location_object = self.env['stock.location']
        picking_cmt_consume = self.env.ref('textile_assembly.picking_cmt_consume')
        picking_cmt_produce = self.env.ref('textile_assembly.picking_cmt_produce')

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

        # PICKING REFERENCE SRB, SMB, SJ
        if operation.code == 'internal' and operation.id not in [picking_cmt_consume.id, picking_cmt_produce.id]:

            if location_object.browse(vals.get('location_id')).get_warehouse().is_warehouse and \
                    location_object.browse(vals.get('location_dest_id')).get_warehouse().is_store:
                vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.wh.store')

            elif location_object.browse(vals.get('location_id')).get_warehouse().is_store and \
                    location_object.browse(vals.get('location_dest_id')).get_warehouse().is_warehouse:
                vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.store.wh')

            elif location_object.browse(vals.get('location_id')).get_warehouse().is_store and \
                    location_object.browse(vals.get('location_dest_id')).get_warehouse().is_store:
                vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.store.store')

            # PICKING REFERENCE TRANSIT LOCATION
            elif vals.get('location_dest_id') == transit_location.id and \
                    vals.get('location_id') != transit_location.id:
                vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.wh.store')
            elif vals.get('location_id') == transit_location.id and \
                    vals.get('location_dest_id') != transit_location.id:
                vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.wh.store')

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



