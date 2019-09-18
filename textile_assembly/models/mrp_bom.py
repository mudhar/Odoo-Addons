# -*- coding: utf-8 -*-

from odoo import api, fields, models
from odoo.tools import float_round


class MrpBom(models.Model):
    _inherit = 'mrp.bom'

    assembly_prod_id = fields.Many2one(comodel_name="assembly.production",
                                       string="Assembly Production", readonly=True, copy=False, index=True)
    cmt_service_ids = fields.One2many(comodel_name="assembly.cmt.product.service", inverse_name="bom_id",
                                      string="CMT Service")

    @api.model
    def bom_find_assembly(self, product_tmpl=None, picking_type=None, company_id=False, assembly=None):
        if product_tmpl:
            domain = [('product_tmpl_id', '=', product_tmpl.id)]
        else:
            # neither product nor template, makes no sense to search
            return False
        if picking_type:
            domain += ['|', ('picking_type_id', '=', picking_type.id), ('picking_type_id', '=', False)]
        if company_id or self.env.context.get('company_id'):
            domain = domain + [('company_id', '=', company_id or self.env.context.get('company_id'))]
        if assembly:
            domain = domain + [('assembly_prod_id', '=', assembly.id)]

        return self.search(domain, order='sequence, product_tmpl_id, assembly_prod_id', limit=1)

    def explode_template(self, product, quantity):

        boms_done = [(self, {'product': product, 'quantity': quantity, 'parent_line': False})]
        lines_done = []

        bom_lines = [(bom_line, product, bom_line.product_qty, False) for bom_line in self.bom_line_ids]
        while bom_lines:
            current_line, current_product, current_qty, parent_line = bom_lines[0]
            bom_lines = bom_lines[1:]

            rounding = current_line.product_uom_id.rounding
            line_quantity = float_round(current_qty, precision_rounding=rounding, rounding_method='UP')
            lines_done.append((current_line,
                               {'quantity': line_quantity,
                                'product': current_product,
                                'original_qty': quantity,
                                'parent_line': parent_line}))

        return boms_done, lines_done
