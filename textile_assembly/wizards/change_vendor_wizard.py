# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ChangeVendor(models.TransientModel):
    _name = 'change.vendor.wizard'
    _description = 'Change Vendor CMT'

    work_order_id = fields.Many2one(comodel_name="mrp.workorder", string="Work Order", required=True)
    partner_id = fields.Many2one(comodel_name="res.partner", string="CMT Vendor")

    @api.model
    def default_get(self, fields_list):
        res = super(ChangeVendor, self).default_get(fields_list)
        if 'work_order_id' in fields_list and not res.get('work_order_id') and self._context.get(
                'active_model') == 'mrp.workorder' and self._context.get('active_id'):
            res['work_order_id'] = self._context['active_id']

        if 'partner_id' in fields_list and not res.get('partner_id') and res.get('work_order_id'):
            res['partner_id'] = self.env['mrp.workorder'].browse(res['work_order_id']).partner_id.id
        return res

    @api.multi
    def action_confirm(self):
        for wizard in self:
            wizard.work_order_id.write({
                'partner_id': wizard.partner_id.id,
                'is_change_vendor': True,
            })
        return {'type': 'ir.actions.act_window_close'}
