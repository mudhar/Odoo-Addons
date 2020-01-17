from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    template_code = fields.Char(string="Assembly Code", copy=False)
    code_pola = fields.Char(string="Code Pola", copy=False)
    is_roll = fields.Boolean(string="Is Roll?")

    @api.constrains('is_roll')
    def _check_lot_option(self):
        for res in self:
            if res.is_roll and res.tracking != 'lot':
                raise ValidationError(_("Anda Menceklis Opsi Roll\n"
                                        "Pada Tab Inventory/Tracking\n"
                                        "Anda Wajib Mimilih Opsi BY LOTS"))
        return True

    # @api.depends('template_code')
    # def _compute_template_code(self):
    #     for res in self:
    #         template_code = res.template_code.strip().split(sep=" ")
    #         code_join = ''.join(code.lower() for code in template_code)
    #         if code_join:
    #             res.assembly_code |= code_join

