# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    assembly_code_ref = fields.Char(string="Reference Assembly Code", copy=False)

    @api.multi
    @api.onchange('template_code')
    def _onchange_template_code(self):
        for template in self:
            if not template.template_code:
                template.assembly_code_ref = False
            template_reference = template.assembly_code_name_get()
            if template_reference:
                template.update({'assembly_code_ref': template_reference})

    @api.multi
    def assembly_code_name_get(self):
        assembly_code_unique = False
        for res in self:
            if res.template_code and res.is_goods and not assembly_code_unique:
                res_name_strip = res.template_code.strip()
                res_name_split = res_name_strip.split(sep=" ")
                assembly_code_unique = ''.join(code.lower() for code in res_name_split)
        return assembly_code_unique

    @api.multi
    @api.constrains('assembly_code_ref', 'company_id')
    def _check_assembly_code(self):
        for template in self:
            if template.assembly_code_ref and template.template_code:
                domain = [
                    ('id', '!=', template.id),
                    ('assembly_code_ref', '=', template.assembly_code_ref),
                    ('company_id', '=', template.company_id.id)
                ]
                found = self.search(domain)
                if found and self.env.context.get('active_test', True):
                    raise ValidationError(_("Product %s Memiliki Code Assembly Yang Sama\n"
                                            "Dengan Product %s") % (template.display_name, found[0].display_name))

    @api.multi
    def _set_assembly_code_ref(self):
        for template in self:
            if template.template_code:
                template_reference = template.assembly_code_name_get()
                template.update({'assembly_code_ref': template_reference})
        return True

    @api.multi
    def action_generate_internal_reference(self):
        self.ensure_one()
        if not self.assembly_code_ref and self.template_code:
            self._set_assembly_code_ref()

        if self.assembly_code_ref and not self.attribute_line_ids:
            raise ValidationError(_("Untuk Mengenerate Internal Reference\n"
                                    "Dan Attribute Untu Produk Juga Harus Diisi"))
        if self.assembly_code_ref and self.is_product_variant and self.product_variant_ids:
            for variant in self.product_variant_ids.filtered(lambda x: not x.internal_reference_generated \
                                                             and x.product_tmpl_id.id == self.id):
                internal_reference = ''.join(ref.name + " " for ref in variant.mapped('attribute_value_ids'))
                variant.write({'default_code': variant.template_code + " " + internal_reference,
                               'internal_reference_generated': True})
        if self.assembly_code_ref and not self.is_product_variant:
            if len(self.product_variant_ids) == 1:
                for variant in self.product_variant_ids.filtered(lambda x: not x.internal_reference_generated
                                                                 and x.product_tmpl_id.id == self.id):
                    internal_reference = ''.join(ref.name + " " for ref in variant.mapped('attribute_value_ids'))
                    variant.write({'default_code': variant.template_code + " " + internal_reference})
            if len(self.product_variant_ids) > 1:
                for variant in self.product_variant_ids.filtered(lambda x: not x.internal_reference_generated \
                                                                 and x.product_tmpl_id.id == self.id):
                    internal_reference = ''.join(ref.name + " " for ref in variant.mapped('attribute_value_ids'))
                    variant.write({'default_code': variant.template_code + " " + internal_reference,
                                   'internal_reference_generated': True})

        return True


class ProductProduct(models.Model):
    _inherit = 'product.product'

    internal_reference_generated = fields.Boolean(string='Internal_reference_generated')
