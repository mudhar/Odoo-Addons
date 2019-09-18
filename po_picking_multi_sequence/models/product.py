from odoo import fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_goods = fields.Boolean(string="Is Goods")
    is_materials = fields.Boolean(string="Is Materials")


