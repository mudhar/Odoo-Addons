# -*- coding: utf-8 -*-
from odoo import fields, models, api, _


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_goods = fields.Boolean(string="Is Goods", help="Tick Jika Produk Finish Goods")
    is_materials = fields.Boolean(string="Is Materials", default=True, help="Tick Jika Produk Material")

    @api.multi
    def write(self, vals):
        result = super(ProductTemplate, self).write(vals)
        if vals.get('is_materials') and vals.get('is_goods'):
            self._set_product_material_goods(vals)
        return result

    def _set_product_material_goods(self, vals):
        for res in self.env['product.product'].search([('product_tmpl_id', '=', self.id)]):
            res.update({'is_materials': vals['is_materials'],
                        'is_goods': vals['is_goods']})

