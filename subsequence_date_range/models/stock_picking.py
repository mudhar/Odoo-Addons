# -*- coding: utf-8 -*-
import calendar
from odoo import fields, models, api


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    @api.model
    def create(self, vals):
        # Cek Apakah Sudah Diceklis Identitas Warehouse
        # Digunakan Untuk Penamaan Internal Transfer SJ, SRB, SMB
        self.check_warehouse_type()
        location_object = self.env['stock.location']
        picking_cmt_consume = self._find_cmt_consume_type()
        picking_cmt_produce = self._find_cmt_produce_type()
        picking_production = self.env.ref('stock.location_production')
        defaults = self.default_get(['name', 'picking_type_id'])

        transit_location = self._find_transit_location()
        operation = self.env['stock.picking.type'].browse(vals.get('picking_type_id'))
        partner_id = self.env['res.partner'].browse(vals.get('partner_id'))

        if vals.get('name', '/') == '/' and defaults.get('name', '/') == '/' and vals.get('picking_type_id',
                                                                                          defaults.get(
                                                                                                  'picking_type_id')):
            if operation.code == 'incoming':
                # purchase order, product materials, vendor non cmt
                # STBN
                if vals.get('purchase_created') and partner_id and not partner_id.is_cmt:
                    sequence_id = self.env['ir.sequence'].search([('code', '=', 'stock.picking.materials_incoming')])
                    if vals.get('product_select_type', 'materials') == 'materials' and sequence_id.use_date_range:
                        new_values = self.create_date_range_picking(vals, sequence_id)
                        vals['name'] = new_values.get('name')
                # purchase order, product goods, vendor cmt
                # STBJ
                elif vals.get('purchase_created') and partner_id and partner_id.is_cmt:
                    sequence_id = self.env['ir.sequence'].search([('code', '=', 'stock.picking.goods_incoming')])
                    if vals.get('product_select_type', 'goods') == 'goods' and sequence_id.use_date_range:
                        new_values = self.create_date_range_picking(vals, sequence_id)
                        vals['name'] = new_values.get('name')
                # Sale Return, Product Goods, Non CMT SR-Customer Code
                elif vals.get('sale_created') and partner_id and not partner_id.is_cmt:
                    sequence_id = self.env['ir.sequence'].search([('code', '=', 'stock.picking.return_customer')])
                    if vals.get('product_select_type', 'goods') == 'goods' and sequence_id.use_date_range:
                        customer_id = self.env['res.partner'].browse(vals.get('partner_id'))
                        new_values = self.create_date_range_picking(vals, sequence_id)
                        customer_code_seq = new_values.get('name')
                        picking_customer_reference = ''.join(
                            'SR-%s/%s' % (customer_id.partner_customer_code, customer_code_seq))
                        vals['name'] = picking_customer_reference

            if operation.code == 'outgoing':
                # purchase return, product materials/product goods, vendor non cmt/cmt
                # SJRB, RTR
                if vals.get('purchase_created') and partner_id and not partner_id.is_cmt:
                    sequence_id = self.env['ir.sequence'].search([('code', '=', 'stock.picking.return_non_cmt')])
                    if vals.get('product_select_type', 'materials') == 'materials' and sequence_id.use_date_range:
                        new_values = self.create_date_range_picking(vals, sequence_id)
                        vals['name'] = new_values.get('name')
                elif vals.get('purchase_created') and partner_id and partner_id.is_cmt:
                    sequence_id = self.env['ir.sequence'].search([('code', '=', 'stock.picking.return_cmt')])
                    if vals.get('product_select_type', 'materials') == 'materials' \
                            or vals.get('product_select_type', 'goods') == 'goods' and sequence_id.use_date_range:
                        new_values = self.create_date_range_picking(vals, sequence_id)
                        vals['name'] = new_values.get('name')

                # sales order, product goods, non customer cmt
                # prefix customer code reference
                elif vals.get('sale_created') and partner_id and not partner_id.is_cmt:
                    sequence_id = self.env['ir.sequence'].search([('code', '=', 'stock.picking.goods_outgoing')])
                    if vals.get('product_select_type', 'goods') == 'goods' and sequence_id.use_date_range:
                        customer_id = self.env['res.partner'].browse(vals.get('partner_id'))
                        new_values = self.create_date_range_picking(vals, sequence_id)
                        customer_code_seq = new_values.get('name')
                        picking_customer_reference = ''.join(
                            '%s/%s' % (customer_id.partner_customer_code, customer_code_seq))
                        vals['name'] = picking_customer_reference
                # product materials, customer cmt
                elif vals.get('sale_created') and partner_id and partner_id.is_cmt:
                    sequence_id = self.env['ir.sequence'].search([('code', '=', 'stock.picking.materials_outgoing')])
                    # SJPB
                    if vals.get('product_select_type', 'materials') == 'materials' and sequence_id.use_date_range:
                        new_values = self.create_date_range_picking(vals, sequence_id)
                        vals['name'] = new_values.get('name')

            if operation.code == 'internal' and operation.id == picking_cmt_consume.id:
                sequence_id_out = self.env['ir.sequence'].search([('code', '=', 'stock.picking.materials_outgoing')])
                sequence_id_in = self.env['ir.sequence'].search([('code', '=', 'stock.picking.return_cmt')])

                # SJPB
                if vals.get('product_select_type', 'materials') == 'materials' \
                        and vals.get('location_dest_id') == picking_production.id and sequence_id_out.use_date_range:
                    new_values = self.create_date_range_picking(vals, sequence_id_out)
                    vals['name'] = new_values.get('name')
                elif vals.get('product_select_type', 'materials') == 'materials' \
                        and vals.get('location_id') == picking_production.id and sequence_id_in.use_date_range:
                    new_values = self.create_date_range_picking(vals, sequence_id_in)
                    vals['name'] = new_values.get('name')

            if operation.code == 'internal' and operation.id == picking_cmt_produce.id:
                sequence_id_in = self.env['ir.sequence'].search([('code', '=', 'stock.picking.goods_incoming')])
                sequence_id_out = self.env['ir.sequence'].search([('code', '=', 'stock.picking.return_cmt')])

                # STBJ
                if vals.get('product_select_type', 'goods') == 'goods' \
                        and vals.get('location_id') == picking_production.id and sequence_id_in.use_date_range:
                    new_values = self.create_date_range_picking(vals, sequence_id_in)
                    vals['name'] = new_values.get('name')
                elif vals.get('product_select_type', 'goods') == 'goods' \
                        and vals.get('location_dest_id') == picking_production.id and sequence_id_out.use_date_range:
                    new_values = self.create_date_range_picking(vals, sequence_id_out)
                    vals['name'] = new_values.get('name')

            # PICKING REFERENCE SRB, SMB, SJ
            if operation.code == 'internal' and operation.id not in [picking_cmt_consume.id, picking_cmt_produce.id]:
                sequence_id_wh_store = self.env['ir.sequence'].search([('code', '=', 'picking.internal.wh.store')])
                sequence_id_store_wh = self.env['ir.sequence'].search([('code', '=', 'picking.internal.store.wh')])
                sequence_id_store_store = self.env['ir.sequence'].search([('code', '=', 'picking.internal.store.store')])

                # SJ
                if location_object.browse(vals.get('location_id')).get_warehouse().is_warehouse and \
                        location_object.browse(vals.get('location_dest_id')).get_warehouse().is_store and \
                        sequence_id_wh_store.use_date_range:
                    new_values = self.create_date_range_picking(vals, sequence_id_wh_store)
                    vals['name'] = new_values.get('name')

                # SRB
                elif location_object.browse(vals.get('location_id')).get_warehouse().is_store and \
                        location_object.browse(vals.get('location_dest_id')).get_warehouse().is_warehouse and \
                        sequence_id_store_wh.use_date_range:
                    new_values = self.create_date_range_picking(vals, sequence_id_store_wh)
                    vals['name'] = new_values.get('name')

                # SMB
                elif location_object.browse(vals.get('location_id')).get_warehouse().is_store and \
                        location_object.browse(vals.get('location_dest_id')).get_warehouse().is_store and \
                        sequence_id_store_store.use_date_range:
                    new_values = self.create_date_range_picking(vals, sequence_id_store_store)
                    vals['name'] = new_values.get('name')

                # PICKING REFERENCE TRANSIT LOCATION
                # SJ
                elif vals.get('location_dest_id') == transit_location.id and \
                        vals.get('location_id') != transit_location.id and sequence_id_wh_store.use_date_range:
                    new_values = self.create_date_range_picking(vals, sequence_id_wh_store)
                    vals['name'] = new_values.get('name')
                # SJ
                elif vals.get('location_id') == transit_location.id and \
                        vals.get('location_dest_id') != transit_location.id and sequence_id_wh_store.use_date_range:
                    new_values = self.create_date_range_picking(vals, sequence_id_wh_store)
                    vals['name'] = self.env['ir.sequence'].next_by_code('picking.internal.wh.store')

        return super(StockPicking, self).create(vals)

    def create_date_range_picking(self, values, sequence_id):
        date_to = fields.Date.from_string(values.get('date'))
        date_to_string = date_to.strftime('%Y-%m-%d')
        dt_from, dt_to = self.env['ir.sequence']._format_date_range_seq(date_to)
        date_range = self.env['ir.sequence']._find_date_range_seq(sequence_id, date_to_string)
        if not date_range:
            new_date_range = self.env['ir.sequence'].act_create_date_range_seq(dt_from, dt_to, sequence_id)
            values['name'] = self.env['ir.sequence']._create_sequence_prefix(sequence_id, new_date_range)
        else:
            values['name'] = self.env['ir.sequence']._create_sequence_prefix(sequence_id, date_range)
        return values



