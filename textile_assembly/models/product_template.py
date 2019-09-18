from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    template_code = fields.Char(string="Code")
    is_roll = fields.Boolean(string="Is Roll?")
