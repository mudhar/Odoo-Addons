from odoo import fields, models, api, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_cmt = fields.Boolean(string="CMT")
    capacity_cmt = fields.Float(string="Capacity", digits=dp.get_precision('Product Unit of Measure'))
    partner_code = fields.Char(string="Code", required=True, size=3, default=123)

    # cek partner yang sudah dibuat datanya ketika action save
    @api.constrains('partner_code')
    def _partner_code_unique(self):
        for res in self:
            vendor_cmt_ids = self.env['res.partner'].search(
                    [('partner_code', '=', res.partner_code),
                     ('id', '!=', res.id),
                     ('supplier', '=', 'True'),
                     ('is_cmt', '=', 'True')])
            if vendor_cmt_ids:
                raise UserError(_("Partner Code Harus Uniq"))
        return True




