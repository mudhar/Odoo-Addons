from openerp import models, fields


class ResCompany(models.Model):
    _inherit = 'res.company'

    custom_header = fields.Boolean(string="Custom Header")
    x_custom_header = fields.Binary(string="Sub Header")
    x_letter_foot = fields.Binary(string="Letter Foot")
