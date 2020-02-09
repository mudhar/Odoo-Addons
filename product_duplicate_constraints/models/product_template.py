# -*- coding: utf-8 -*-
import itertools
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    assembly_code_ref = fields.Char(string="Reference Assembly Code", copy=False)

    _sql_constraints = [('assembly_code_ref_unique', 'unique (assembly_code_ref, company_id)',
                         "The Assembly Code must be unique per Company.")]

    # Perlu Revisi Untuk Override Fungsi Write
    # @api.model
    # def create(self, values):
    #     template = super(ProductTemplate, self).create(values)
    #     related_values = {}
    #     if values.get('assembly_code_ref'):
    #         related_values['assembly_code_ref'] = values['assembly_code_ref']
    #     if related_values:
    #         template.write(related_values)
    #     return template

    @api.onchange('template_code')
    def _onchange_assembly_code(self):
        for product in self:
            if product.template_code and product.is_goods:
                code_ref = product.assembly_code_name_get()
                product.update({'assembly_code_ref': code_ref})

    @api.model
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
    def action_generate_internal_reference(self):
        self.ensure_one()
        if self.assembly_code_ref and not self.attribute_line_ids:
            raise ValidationError(_("Untuk Mengenerate Internal Reference\n"
                                    "Dan Attribute Untu Produk Juga Harus Diisi"))
        if self.assembly_code_ref and self.is_product_variant and self.product_variant_ids:
            for variant in self.product_variant_ids.filtered(lambda x: not x.internal_reference_generated \
                                                             and x.product_tmpl_id.id == self.id):
                internal_reference = ''.join(ref.name + " " for ref in variant.mapped('attribute_value_ids'))
                variant.write({'default_code': variant.assembly_code_ref + internal_reference,
                               'internal_reference_generated': True})
        if self.assembly_code_ref and not self.is_product_variant:
            for variant in self.product_variant_ids.filtered(lambda x: not x.internal_reference_generated \
                                                             and x.product_tmpl_id.id == self.id):
                internal_reference = ''.join(ref.name + " " for ref in variant.mapped('attribute_value_ids'))
                variant.write({'default_code': variant.assembly_code_ref + " " + internal_reference})
        return True


class ProductProduct(models.Model):
    _inherit = 'product.product'

    internal_reference_generated = fields.Boolean(string='Internal_reference_generated')
