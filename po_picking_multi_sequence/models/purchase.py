# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    product_select_type = fields.Selection(string="Report Type",
                                           selection=[('materials', 'Materials'),
                                                      ('goods', 'Goods'),
                                                      ('subpo', 'Sub PO')], default='materials',
                                           help="Reference Picking Name",
                                           index=True, copy=True,  track_visibility='onchange', required=True)

    @api.multi
    def button_confirm(self):
        for order in self:
            if order.product_select_type and order.product_select_type == 'subpo':
                if any(line.type in ['consu','product'] for line in order.order_line.mapped('product_id')):
                    raise ValidationError(_("Dokumen Picking Untuk Sub PO Tidak Ditemukan\n"
                                            "Cek Tipe Produk, Apakah Sudah Bertipe Service?\n"))
        return super(PurchaseOrder, self).button_confirm()

    @api.model
    def create(self, vals):
        if vals.get('product_select_type', 'materials') == 'materials':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order.materials')
        elif vals.get('product_select_type', 'goods') == 'goods':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order.goods')
        elif vals.get('product_select_type', 'subpo') == 'subpo':
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order.subpo')
        else:
            vals['name'] = self.env['ir.sequence'].next_by_code('purchase.order') or '/'
        return super(PurchaseOrder, self).create(vals)

    @api.model
    def _prepare_picking(self):
        result = super(PurchaseOrder, self)._prepare_picking()
        result.update({'product_select_type': self.product_select_type,
                       'purchase_created': True})
        return result


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    @api.onchange('product_id')
    def onchange_product_id(self):
        result = super(PurchaseOrderLine, self).onchange_product_id()
        if self.order_id.product_select_type:
            if self.order_id.product_select_type == 'materials':
                result['domain'] = {'product_id': [('product_tmpl_id.is_materials', '=', True)]}
            elif self.order_id.product_select_type == 'goods':
                result['domain'] = {'product_id': [('product_tmpl_id.is_goods', '=', True)]}

        return result

    @api.multi
    def _prepare_stock_moves(self, picking):
        res = super(PurchaseOrderLine, self)._prepare_stock_moves(picking)
        if len(res) == 1:
            res[0].update({'product_select_type': self.order_id.product_select_type})
        return res

