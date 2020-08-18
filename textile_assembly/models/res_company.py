from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    service_categ_id = fields.Many2one(comodel_name="product.category", string="Product Service Category")
    location_reject_id = fields.Many2one(comodel_name="stock.location", string="Stock Location Reject")
