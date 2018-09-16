from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    location_id = fields.Many2one(comodel_name="stock.location", string="Location", domain=[('usage', '=', 'internal')])
