# -*- coding: utf-8 -*-
from odoo import api, fields, models


class PlanChangeVendor(models.TransientModel):
    _name = 'assembly_plan.change_vendor.wizard'
    _description = 'Update No Reference'

    plan_id = fields.Many2one(comodel_name="assembly.plan", string="Plan Order")
    assembly_id = fields.Many2one(comodel_name="assembly.production", string="Assembly Order")

    partner_id = fields.Many2one(comodel_name="res.partner", string="CMT Vendor", domain="[('is_cmt','=',True)]")

    @api.model
    def default_get(self, fields_list):
        res = super(PlanChangeVendor, self).default_get(fields_list)
        if 'plan_id' in fields_list and not res.get('plan_id') and self._context.get(
                'active_model') == 'assembly.plan' and self._context.get('active_id'):
            res['plan_id'] = self._context['active_id']

        if 'assembly_id' in fields_list and not res.get('assembly_id') and res.get('plan_id'):
            res['assembly_id'] = self.env['assembly.plan'].browse(res['plan_id']).assembly_id.id

        return res

    @api.multi
    def action_confirm(self):
        for order in self:
            if order.partner_id:
                new_partner_code = order.partner_id.partner_cmt_code
                plan_reference = order.plan_id.name
                copy_reference = plan_reference[plan_reference.index('/'):]

                order.plan_id.write({'partner_id': order.partner_id.id,
                                     'name': new_partner_code + copy_reference})
                order.assembly_id.write({'partner_id': order.partner_id.id})
        return True
