# -*- coding: utf-8 -*-
from odoo import fields, models, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    template_code = fields.Char(string="Assembly Code", copy=False,
                                help="Code Produk Digunakan Pada Assembly Untuk Penamanaan Dokumen Assembly")
    pattern_code = fields.Char(string="Code Pola", copy=False)
    is_roll = fields.Boolean(string="Is Roll?",
                             help="Digunakan Untuk Penamaan Lot Pada Produk Yang Membutuhkan")
    has_goods = fields.Boolean(compute="_has_goods")

    @api.depends('is_goods', 'sale_ok', 'purchase_ok')
    def _has_goods(self):
        for product in self:
            product.has_goods = (product.is_goods and product.sale_ok and not product.purchase_ok)

    @api.constrains('is_roll')
    def _check_lot_option(self):
        for res in self:
            if res.is_roll and res.tracking != 'lot':
                raise ValidationError(_("Anda Menceklis Opsi Roll\n"
                                        "Pada Tab Inventory/Tracking\n"
                                        "Anda Wajib Mimilih Opsi BY LOTS"))
        return True