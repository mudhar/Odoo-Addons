# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################
import logging
from odoo.addons import decimal_precision as dp
from collections import defaultdict
from odoo import models, fields, api, _


_logger = logging.getLogger(__name__)


class AssemblyProd(models.Model):
    _name = 'assembly.production'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _description = 'Assembly Production'
    _order = "create_date desc, id desc"

    @api.model
    def name_search(self, name='', args=None, operator='ilike', limit=100):
        args = args or []
        domain = []
        if name:
            domain = ['|', ('name', operator, name), ('product_tmpl_id.name', operator, name)]
        pos = self.search(domain + args, limit=limit)
        return pos.name_get()

    state = fields.Selection([
        ('draft', 'Draft'),
        ('process', 'On Process'),
        ('approve', 'Approve'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')

    name = fields.Char('Assembly Reference', required=True, index=True, copy=False,
                       states={'draft': [('readonly', False)]},
                       default=lambda self: _('New'))
    version = fields.Integer(string="Version", default=1, index=True)
    active = fields.Boolean('Active', default=True, index=True,
                            help="If unchecked, it will allow you to hide the Assembly Production without removing it.")

    product_tmpl_id = fields.Many2one(comodel_name="product.template", string="Product",
                                      index=True, track_visibility='onchange', ondelete='cascade')
    product_categ_id = fields.Many2one(comodel_name="product.category",
                                       related="product_tmpl_id.categ_id", string="Category", index=True, readonly=True)
    variant_line_ids = fields.One2many(comodel_name="assembly.prod.variant.line", inverse_name="assembly_id",
                                       string="Product Components", states={'cancel': [('readonly', True)],
                                                                            'approve': [('readonly', True)]}, copy=True)
    bom_line_ids = fields.One2many(comodel_name="assembly.prod.bom.line", inverse_name="assembly_id",
                                   string="Raw Materials", states={'cancel': [('readonly', True)],
                                                                   'approve': [('readonly', True)]}, copy=True)
    bom_line_ids2 = fields.One2many(comodel_name="assembly.prod.bom.line2", inverse_name="assembly_id",
                                    string="CMT Materials", states={'cancel': [('readonly', True)],
                                                                    'approve': [('readonly', True)]}, copy=True)

    amount_total = fields.Float(string="Total", digits=dp.get_precision('Account'),
                                compute="_compute_amount_total")
    currency_id = fields.Many2one('res.currency', 'Currency', required=True,
                                  states={'cancel': [('readonly', True)], 'approve': [('readonly', True)]},

                                  default=lambda self: self.env.user.company_id.currency_id.id)
    # di invisible di xml buat ambil data di model mrp.bom
    product_uom_id = fields.Many2one(
        'product.uom', 'Product Unit of Measure', related="product_tmpl_id.uom_id")

    @api.multi
    @api.depends('name', 'product_tmpl_id.name')
    def name_get(self):
        result = []
        for assembly in self:
            name = assembly.name
            if assembly.product_tmpl_id:
                name += ' (' + assembly.product_tmpl_id.name + ')'
            result.append((assembly.id, name))
        return result

    # create Data assembly plan
    @api.multi
    def prepare_assembly_plan(self):
        self.ensure_one()
        assemblyplan_vals = {
            'origin': self.name,
            'product_template_id': self.product_tmpl_id.id,
        }
        return assemblyplan_vals

    @api.multi
    def action_assembly_plan_create(self, grouped=False):
        # contek fungsi action_invoice_create()
        plan_obj = self.env['assembly.plan']
        plans = {}
        references = {}
        plans_origin = {}

        for order in self:
            group_key = order.id if grouped else (order.product_tmpl_id.id, order.currency_id.id)
            for line in order.variant_line_ids.sorted(key=lambda l: l.product_id.id < 0):
                if group_key not in plans:
                    plan_data = order.prepare_assembly_plan()
                    plan = plan_obj.create(plan_data)
                    references[plan] = order
                    plans[group_key] = plan
                    plans_origin[group_key] = [plan.origin]
                elif group_key not in plans:
                    if order.name not in plans_origin[group_key]:
                        plans_origin[group_key].append(order.name)

                if line.product_id.id > 0:
                    line.assembly_plan_line_create(plans[group_key].id, line.product_id.id)

            for line2 in order.bom_line_ids.sorted(key=lambda l: l.ratio < 0):
                if line2.ratio > 0:
                    line2.assembly_plan_material_create(plans[group_key].id, line2.ratio)

            if references.get(plans.get(group_key)):
                if order not in references[plans[group_key]]:
                    references[plans[group_key]] |= order

        for group_key in plans:
            plans[group_key].write({'origin': ', '.join(plans_origin[group_key])})

        return [pl.id for pl in plans.values()]

    @api.multi
    @api.depends('bom_line_ids.price_subtotal')
    def _compute_amount_total(self):
        for bom in self:
            price_list = [line.price_subtotal for line in bom.bom_line_ids if line.price_subtotal]
            price_list2 = [line.price_subtotal for line in bom.bom_line_ids2]
            total = sum(price_list2)
            price_max = 0
            for record in bom.bom_line_ids:
                if not record.price_subtotal:
                    return {}
                else:
                    price_max = max(price_list)

            bom.update({
                'amount_total': total + price_max})

    @api.multi
    def onchange_product_id(self):
        if self.product_tmpl_id:
            variant_lines = []
            for variant in self.product_tmpl_id.product_variant_ids:
                variant_lines.append([0, 0, {
                    'product_id': variant.id,
                    'attribute_value_ids': variant.attribute_value_ids

                }])
            self.update({
                'variant_line_ids': variant_lines
            })

    @api.multi
    def button_process(self):
        self.write({'state': 'process'})
        self.action_process(self)
        return True

    @api.multi
    def action_process(self, assembly_id):
        name, new_version = self.create_name(assembly_id)
        assembly_id.write({'name': name,
                           'version': new_version})

    @api.multi
    def create_name(self, assembly_id):
        obj = self.env['assembly.production']
        active_ids = obj.search(
            [('product_tmpl_id', '=', assembly_id.product_tmpl_id.id), ('id', '!=', self.id), ('active', '=', True)])
        inactive_ids = obj.search(
            [('product_tmpl_id', '=', assembly_id.product_tmpl_id.id), ('id', '!=', self.id), ('active', '=', False)])
        if active_ids:
            for line in active_ids:
                line.active = False
        count = len(active_ids) + len(inactive_ids)
        version = count + 1
        new_name = assembly_id.product_tmpl_id.template_code + " v" + str(version)
        return new_name, version

    @api.multi
    def compare_ratio(self):
        for record in self:
            # [color][size]
            variants = [variant.attribute_value_ids[0] for variant in record.variant_line_ids]
            # print("VARIANTS", variants)
            ratios = [r.ratio for r in record.variant_line_ids]
            data_dict = defaultdict(list)
            # data_dic = { 'variants':[ratios]}
            for k, v in zip(variants, ratios):
                data_dict[k].append(v)

            for bom in record.bom_line_ids:
                if data_dict.get(bom.attribute_value_ids):
                    hitung = sum(data_dict.get(bom.attribute_value_ids))
                    bom.update({'ratio': hitung})

    # fungsi membuat record model mrp bom
    @api.multi
    def get_product_qty_vals(self):
        # data product_qty di model mrp.bom
        res = 0
        for order in self:
            total_qty = [variant.ratio for variant in order.variant_line_ids]
            res += sum(total_qty)
        return res

    @api.multi
    def create_bom(self):
        bom_object = self.env['mrp.bom']

        product_qty = self.get_product_qty_vals()
        bom_line_data = self.get_mrp_bom_line_vals()
        bom_object.create({
            'product_tmpl_id': self.product_tmpl_id.id,
            'product_qty': product_qty,
            'product_uom_id': self.product_uom_id.id,
            'bom_line_ids': bom_line_data
        })

    @api.multi
    def get_mrp_bom_line_vals(self):
        product_variant_vals = self.get_variant_vals()
        product_bom_vals = self.get_product_bom_vals()
        product_vals = []

        # test key value dalam list(dict) type class list
        for variant in product_variant_vals:
            for bom in product_bom_vals:
                _logger.debug("PRODUCT DICT", (variant.keys(), bom.keys()))

        # cek 2 record (variant_line_ids, bom_line_ids)
        # apabila ada value dari attribute_value_ids di record variant_line_ids
        # append value tsb ke list
        # data di list digunakan untuk buat record di model mrp.bom.line
        for variant_key in product_variant_vals:
            for bom_key in product_bom_vals:
                if bom_key['attribute_value_ids'][0] in variant_key['attribute_value_ids'][0]:
                    product_vals.append({
                        'product_id': bom_key['product_id'],
                        'attribute_value_ids': variant_key['attribute_value_ids'],
                        'ratio': variant_key['ratio'],
                        'product_uom_id': bom_key['product_uom_id']

                    })
        # cek data apakah sesuai dengan output yang diharapkan
        _logger.debug("PRODUCT VALS", (product_vals, type(product_vals)))

        # [(0, 0))] buat record baru dari data yang sudah dibuat
        bom_line_data = []
        for bom_id in product_vals:
            bom_line_data.append([0, 0, {
                'product_id': bom_id.get('product_id'),
                'product_qty': bom_id.get('ratio'),
                'product_uom_id': bom_id.get('product_uom_id'),
                'attribute_value_ids': [(6, 0, bom_id['attribute_value_ids'].ids)]
            }])
        return bom_line_data

    @api.model
    def get_variant_vals(self):
        if not self.variant_line_ids:
            return []
        variant_vals = []
        for variant in self.variant_line_ids:
            variant_vals.append({
                'product_id': variant.product_id.id,
                'attribute_value_ids': variant.attribute_value_ids,
                'ratio': variant.ratio
            })
        return variant_vals

    @api.model
    def get_product_bom_vals(self):
        if not self.bom_line_ids:
            return []
        bom_vals = []
        for bom in self.bom_line_ids:
            bom_vals.append({
                'product_id': bom.product_id.id,
                'attribute_value_ids': bom.attribute_value_ids,
                'product_uom_id': bom.product_uom_id.id
            })
        return bom_vals

    @api.multi
    def button_approve(self):
        self.write({'state': 'approve'})
        self.compare_ratio()
        self.action_assembly_plan_create()
        self.create_bom()
        return True

    @api.multi
    def button_cancel(self):
        self.write({'state': 'cancel'})
        return True
































































