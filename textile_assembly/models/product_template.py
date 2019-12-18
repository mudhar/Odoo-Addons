from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    template_code = fields.Char(string="Code")
    code_pola = fields.Char(string="Code Pola")
    is_roll = fields.Boolean(string="Is Roll?")

    @api.constrains('is_roll')
    def _check_lot_option(self):
        for res in self:
            if res.is_roll and res.tracking != 'lot':
                raise ValidationError(_("Anda Menceklis Opsi Roll\n"
                                        "Pada Tab Inventory/Tracking\n"
                                        "Anda Wajib Mimilih Opsi BY LOTS"))
        return True
