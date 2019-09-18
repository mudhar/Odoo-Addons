from odoo import fields, models
from odoo.addons import decimal_precision as dp


class ResPartner(models.Model):
    _inherit = 'res.partner'

    is_cmt = fields.Boolean(string="CMT")
    capacity_cmt = fields.Float(string="Capacity", digits=dp.get_precision('Product Unit of Measure'))
    partner_code = fields.Char(string="Code", required=True, size=3, default='123')
