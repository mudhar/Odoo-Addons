from openerp import models, fields, api, _
from openerp.exceptions import Warning as UserError


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    template_inter_company_created = fields.Boolean(string="Product Inter Company Created")
    show_button = fields.Boolean(string="Show Button", compute="_compute_seller_ids")

    @api.multi
    @api.depends('seller_ids',
                 'product_variant_ids')
    def _compute_seller_ids(self):
        for prod in self:
            if prod.seller_ids and prod.product_variant_ids:
                partner_id = prod.seller_ids[0].mapped('name')
                dest_company = self.env['res.company']._find_company_from_partner(
                    partner_id.id)
                product_found = self._check_product_intercompany(prod.name, dest_company)

                if product_found and dest_company:
                    prod.update({'show_button': False})
                if not product_found and dest_company:
                    prod.update({'show_button': True})


    @api.multi
    def action_create_product_inter_company(self):
        if not self.seller_ids:
            raise UserError(_("Tidak Ada Supplier Yang Di input"))
        partner_id = False
        if not partner_id:
            partner_id = self.seller_ids[0].mapped('name')

        dest_company = self.env['res.company']._find_company_from_partner(
            partner_id.id)

        if dest_company:
            check_product = self._check_product_intercompany(self.name, dest_company)
            if check_product:
                raise UserError(_("Product %s Sudah Dibuat Pada Company %s") % (self.name.upper(), dest_company.name))

            product_template_data = self._prepare_product_template(dest_company)

            self.env['product.template'].sudo().with_context(force_company=dest_company.id).create(
                product_template_data)

        self.write({'template_inter_company_created': True})

    @api.multi
    def _prepare_product_template(self, dest_company):
        template = {
            'name': self.name,
            'uom_id': self.uom_id.id,
            'uom_po_id': self.uom_po_id.id,
            'type': self.type,
            'company_id': dest_company.id,
            'categ_id': self.categ_id.id,
            'purchase_ok': False,
        }
        return template

    @api.multi
    def _check_product_intercompany(self, name, dest_company):
        found = self.env['product.product'].sudo().get_related_product(name,
                                                                       dest_company.id)
        return found








