# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError


class StockPicking(models.Model):
    _inherit = 'stock.picking'

    final_location_dest_id = fields.Many2one(comodel_name="stock.location", string="Final Destination Location", copy=False)
    check_final_location = fields.Boolean(string="Final Destination Location?", copy=False,
                                          help="Tick Jika Ingin Transfer Dengan Lokasi Transit")
    has_transit_location = fields.Boolean(string="Transit Location?", copy=False,
                                          help="Tick Jika Ingin Mengembalikan Lokasi Tujuan awal")

    @api.onchange('check_final_location')
    def _onchange_final_location(self):
        location_transit_id = self._default_location_dest_transit_id()
        if self.check_final_location:
            self.update({'location_dest_id': location_transit_id.id})

    @api.onchange('has_transit_location')
    def _onchange_transit_location(self):
        if self.has_transit_location and self.check_final_location:
            self.update({'location_dest_id': self.picking_type_id.default_location_src_id.id,
                         'check_final_location': False})

    @api.multi
    def button_validate(self):
        result = super(StockPicking, self).button_validate()
        if self.final_location_dest_id and self.check_final_location:
            self._create_backorder_inter_transfer()
        return result

    @api.model
    def _default_location_dest_transit_id(self):
        location_obj = self.env['stock.location']
        locations = location_obj.search([('company_id', '=', self.env.user.company_id.id),
                                         ('usage', '=', 'transit')])
        return locations[:1]

    @api.model
    def _default_picking_type_internal_dest_id(self):
        warehouse_id = self.final_location_dest_id.get_warehouse()
        type_obj = self.env['stock.picking.type']
        types = type_obj.search([('code', '=', 'internal'),
                                 ('warehouse_id', '=', warehouse_id.id)])
        return types[:1]

    @api.multi
    def _create_backorder_inter_transfer(self):
        backorders = self.env['stock.picking']
        for picking in self:
            location_src_id = picking.location_dest_id
            location_dest_id = picking.final_location_dest_id
            picking_type_id = self._default_picking_type_internal_dest_id()
            for move in picking.move_lines:
                backorder_picking = picking.copy({
                    'name': '/',
                    'location_id': location_src_id.id,
                    'location_dest_id': location_dest_id.id,
                    'picking_type_id': picking_type_id.id,
                    'move_lines': [],
                    'move_line_ids': [],
                    'backorder_id': picking.id,
                })
                # if backorder_picking:
                #     raise UserError(_("Test"))
                moves_to_backorder = self.env['stock.move'].create({
                    'name': _('New Move:') + move.product_id.display_name,
                    'product_id': move.product_id.id,
                    'product_uom_qty': move.quantity_done,
                    'product_uom': move.product_uom.id,
                    'location_id': location_src_id.id,
                    'location_dest_id': location_dest_id.id,
                    'picking_type_id': picking_type_id.id,
                })
                moves_to_backorder.write({'picking_id': backorder_picking.id})
                moves_to_backorder.mapped('move_line_ids').write({'picking_id': backorder_picking.id})
                backorder_picking.action_assign()
                backorders |= backorder_picking
        return backorders

