# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_cmt = fields.Boolean(string="CMT")
    partner_cmt_code = fields.Char(string="CMT Code", size=3)
    reference_cmt_code = fields.Char(string='CMT Code Reference', size=3, oldname='cmt_code_reference')

    partner_customer_code = fields.Char(string='Customer Code', size=5)
    reference_customer_code = fields.Char(string='Customer Code Reference', size=5)

    @api.multi
    @api.onchange('partner_customer_code')
    def _onchange_partner_customer_code(self):
        for res in self:
            if res.partner_customer_code:
                reference_customer_code = res.partner_customer_code.lower()
                res.update({'reference_customer_code': reference_customer_code})

    @api.multi
    @api.constrains('reference_customer_code', 'company_id', 'customer')
    def _check_partner_customer_code(self):
        for partner in self:
            if partner.reference_customer_code and partner.customer:
                domain = [
                    ('id', '!=', partner.id),
                    ('reference_customer_code', '=', partner.reference_customer_code),
                    ('customer', '=', partner.customer),
                    ('company_id', '=', partner.company_id.id)
                ]
                found = self.search(domain)
                if found and self.env.context.get('active_test', True):
                    raise ValidationError(_("Customer %s Memiliki Code Yang Sama\n"
                                            "Dengan Customer %s") % (found[0].display_name, partner.display_name))

    @api.multi
    @api.onchange('partner_cmt_code')
    def _onchange_partner_cmt_code(self):
        for partner in self:
            if partner.partner_cmt_code:
                reference_cmt_code = partner.partner_cmt_code.lower()
                partner.update({'reference_cmt_code': reference_cmt_code})

    @api.multi
    @api.constrains('reference_cmt_code',
                    'supplier',
                    'company_id',
                    'is_cmt')
    def _check_reference_cmt_code(self):
        for partner in self:
            if partner.reference_cmt_code and \
                    partner.supplier and \
                    partner.is_cmt:
                domain = [
                    ('id', '!=', partner.id),
                    ('reference_cmt_code', '=', partner.reference_cmt_code),
                    ('supplier', '=', partner.supplier),
                    ('is_cmt', '=', partner.is_cmt),
                    ('company_id', '=', partner.company_id.id)
                ]
                found = self.search(domain)
                if found and self.env.context.get('active_test', True):
                    raise ValidationError(_("CMT %s Memiliki Code Yang Sama\n"
                                            "Dengan CMT %s") % (found[0].display_name, partner.display_name))








