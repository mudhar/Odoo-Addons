from odoo import fields, models, api, _
from odoo.exceptions import UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    is_goods = fields.Boolean(string="Is Goods")
    is_materials = fields.Boolean(string="Is Materials", default=True)

    # materials_goods_optional = fields.Boolean(string="Check Select Materials Goods",
    #                                           compute="_compute_goods_materials", store=True)
    #
    # @api.constrains('materials_goods_optional')
    # def _check_materials_goods_optional(self):
    #     if not self.materials_goods_optional:
    #         raise UserError(_("Pilih Opsi Material Atau Good"))
    #     else:
    #         return False

    @api.depends('is_goods', 'is_materials')
    def _compute_goods_materials(self):
        for res in self:
            res.materials_goods_optional = res.is_materials or res.is_goods

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

