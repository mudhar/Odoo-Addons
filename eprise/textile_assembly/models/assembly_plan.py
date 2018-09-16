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
from datetime import datetime
from dateutil.relativedelta import relativedelta
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo.addons import decimal_precision as dp
from odoo import api, fields, models, _
from odoo.exceptions import Warning as UserError


_logger = logging.getLogger(__name__)


class AssemblyPlan(models.Model):
    _name = 'assembly.plan'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _rec_name = 'name'
    _description = 'Assembly Plan'
    _order = 'id'

    @api.model
    def _get_default_name(self):
        return self.env['ir.sequence'].next_by_code('assembly.plan')

    @api.model
    def _default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'),
                                 ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'),
                                     ('warehouse_id', '=', False)])
        return types[:1]

    @api.multi
    @api.constrains('picking_type_id')
    def _check_picking_type_id(self):
        for rec in self:
            if rec.picking_type_id.code != 'incoming':
                raise UserError(_(
                    "Picking type operation must be 'Suppliers'."))

    name = fields.Char('Plan Reference', size=32, required=True,
                       default=_get_default_name,
                       track_visibility='onchange')
    location_id = fields.Many2one(comodel_name="stock.location", string="Location", domain=[('usage', '=', 'internal')],
                                  track_visibility='always', default=lambda self: self.env.user.company_id.location_id)
    date_start = fields.Date('Creation date',
                             help="Date when the user initiated the "
                                  "Plan.",
                             default=fields.Date.context_today)

    origin = fields.Char(string="Source Document", size=32)
    plan_line_ids = fields.One2many('assembly.plan.line', 'plan_id', string="Plan Lines")
    raw_line_ids = fields.One2many('assembly.plan.material', 'plan_id', string="Material Lines")
    active = fields.Boolean('Active', default=True, index=True,
                            help="If unchecked, it will allow you to hide the Assembly Production without removing it.")
    total_quantity = fields.Float(string="Total Quantity", default=0.0, digits=dp.get_precision('Product Unit of Measure'),
                                  store=True, required=True)
    sisa_qty = fields.Float(string='Sisa Quantity', default=0.0, digits=dp.get_precision('Product Unit of Measure'),
                            compute="compute_sisa_qty", store=True)
    product_template_id = fields.Many2one(comodel_name="product.template", string="Product", index=True)

    state = fields.Selection([
        ('draft', 'Draft'),
        ('to approve', 'To Approve'),
        ('procurement', 'Procurement'),
        ('approve', 'Approve'),
        ('cancel', 'Cancelled')
    ], string='Status', readonly=True, index=True, copy=False, default='draft', track_visibility='onchange')

    @api.multi
    def check_qty(self):
        quantity = self.env['assembly.plan.material'].compute_qty_available()
        return quantity

    @api.multi
    def default_picking_type(self):
        type_obj = self.env['stock.picking.type']
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        types = type_obj.search([('code', '=', 'incoming'),
                                 ('warehouse_id.company_id', '=', company_id)])
        if not types:
            types = type_obj.search([('code', '=', 'incoming'),
                                     ('warehouse_id', '=', False)])
        return types[:1]

    @api.multi
    def get_supplier_id(self, supplier):

        return supplier[0]

    @api.multi
    def create_purchase_order(self):
        for order in self:
            po_ids = []
            picking_type_id = order.default_picking_type()
            # _logger.debug("Get Picking Type", str(picking_type_id.name))

            for line in order.raw_line_ids:
                company_id = self.env.user.company_id
                partner = False
                if line.product_id:
                    suppliers = line.product_id.seller_ids \
                        .filtered(lambda r: (not r.company_id or r.company_id == company_id) and (
                                not r.product_id or r.product_id == line.product_id))
                    supplier = self.get_supplier_id(suppliers)
                    partner = supplier.name
                po_id = order.action_create_purchase_order(line.product_id, line.qty_to_po,
                                                           line.product_uom_id, picking_type_id, line.product_id.name,
                                                           order.origin, order, partner)
                po_ids.append(po_id)
                # _logger.debug("Purchase Order", po_ids)
            return po_ids

    def action_create_purchase_order(self, product_id, product_qty, product_uom, picking_type_id,
                                     name, origin, order, partner):
        # contek fungsi _run_buy
        cache = {}
        domain = order.get_domain(partner, picking_type_id)
        _logger.debug("Get Domain", str(domain))

        if domain in cache:
            po = cache[domain]
        else:
            po = self.env['purchase.order'].sudo().search([dom for dom in domain])
            po = po[0] if po else False
            cache[domain] = po
        _logger.debug("Get Cache", str(po))
        if not po:
            value = self.prepare_purchase_order(product_id, product_qty, product_uom, picking_type_id, origin, order, partner)
            company = self.env.context.get('company_id') or self.env.user.company_id.id
            po = self.env['purchase.order'].with_context(force_company=company).sudo().create(value)
            cache[domain] = po
        elif not po.origin or origin not in po.origin.split(', '):
            if po.origin:
                if origin:
                    po.write({'origin': po.origin + ', ' + origin})
                else:
                    po.write({'origin': po.origin})
            else:
                po.write({'origin': origin})

        # Create Line
        po_line = False
        for line in po.order_line:
            if line.product_id == product_id and line.product_uom == product_id.uom_po_id:
                if line._merge_in_existing_line(product_id, product_qty, product_uom, picking_type_id, name,
                                               origin, order):
                    vals = self.update_purchase_order_line(product_id, product_qty, product_uom, order,
                                                            line, partner)
                    po_line = line.write(vals)
                    break
        if not po_line:
            vals = self.prepare_purchase_order_line(product_id, product_qty, product_uom, order, po, partner)
            self.env['purchase.order.line'].sudo().create(vals)

    def update_purchase_order_line(self, product_id, product_qty, product_uom, order, line, partner):
        new_qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id)
        seller = product_id._select_seller(
            partner_id=partner,
            quantity=line.product_qty + new_qty,
            date=line.order_id.date_order and line.order_id.date_order[:10],
            uom_id=product_id.uom_po_id
        )
        company_id = self.env.context.get('company_id')
        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                             line.product_id.supplier_taxes_id,
                                                                             line.taxes_id, company_id) if seller else 0.0
        if price_unit and seller and line.order_id.currency_id and seller.currency_id != line.order_id.currency_id:
            price_unit = seller.currency_id.compute(price_unit, line.order_id.currency_id)

        return {
            'product_qty': line.product_qty + new_qty,
            'price_unit': price_unit
        }

    @api.multi
    def prepare_purchase_order_line(self, product_id, product_qty, product_uom, order, po, partner):
        new_po_qty = product_uom._compute_quantity(product_qty, product_id.uom_po_id)
        seller = product_id._select_seller(
            partner_id=partner,
            quantity=new_po_qty,
            date=po.date_order and po.date_order[:10],
            uom_id=product_id.uom_po_id
        )
        taxes = product_id.supplier_taxes_id
        fpos = po.fiscal_position_id
        taxes_id = fpos.map_tax(taxes) if fpos else taxes
        company_id = self.env.context.get('company_id')
        if taxes_id:
            taxes_id = taxes_id.filtered(lambda x: x.company_id.id == company_id.id)

        price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price, product_id.supplier_taxes_id, taxes_id, company_id) if seller else 0.0
        product_lang = product_id.with_context({
            'lang': partner.lang,
            'partner_id': partner.id,
        })
        name = product_lang.display_name
        if product_lang.description_purchase:
            name += '\n' + product_lang.description_purchase

        date_planned = \
            self.env['purchase.order.line']._get_date_planned(seller, po=po).strftime(DEFAULT_SERVER_DATETIME_FORMAT)
        return {
            'name': name,
            'product_qty': new_po_qty,
            'product_id': product_id.id,
            'product_uom': product_id.uom_po_id.id,
            'price_unit': price_unit,
            'date_planned': date_planned,
            'taxes_id': [(6, 0, taxes_id.ids)],
            'order_id': po.id,

        }

    def get_purchase_schedule_date(self, order):
        """Return the datetime value to use as Schedule Date (``date_planned``) for the
           Purchase Order Lines created to satisfy the given procurement. """
        procurement_date_planned = fields.Datetime.from_string(order.date_start)
        schedule_date = (procurement_date_planned - relativedelta(days=self.env['res.company'].po_lead))
        return schedule_date

    def get_purchase_order_date(self, product_id, product_qty, product_uom, values, partner, schedule_date):
        """Return the datetime value to use as Order Date (``date_order``) for the
           Purchase Order created to satisfy the given procurement. """
        seller = product_id._select_seller(
            partner_id=partner,
            quantity=product_qty,
            date=fields.Date.to_string(schedule_date),
            uom_id=product_uom)

        return schedule_date - relativedelta(days=int(seller.delay))

    def prepare_purchase_order(self, product_id, product_qty, product_uom, picking_type_id, origin, order, partner):
        schedule_date = self.get_purchase_schedule_date(order)
        purchase_date = self.get_purchase_order_date(product_id, product_qty, product_uom,
                                                     order, partner, schedule_date)
        company_id = self.env.context.get('company_id') or self.env.user.company_id.id
        fpos = self.env['account.fiscal.position'].with_context(force_company=company_id).get_fiscal_position(partner.id)
        return {
            'partner_id': partner.id,
            'picking_type_id': picking_type_id.id,
            'company_id': company_id,
            'currency_id': partner.with_context(force_company=company_id).property_purchase_currency_id.id or self.env.user.company_id.currency_id.id,
            'origin': origin,
            'payment_term_id': partner.with_context(force_company=company_id).property_supplier_payment_term_id.id,
            'date_order': purchase_date.strftime(DEFAULT_SERVER_DATETIME_FORMAT),
            'fiscal_position_id': fpos,
        }

    def get_domain(self, partner, picking_type_id):
        domain = ()
        domain += (
            ('partner_id', '=', partner.id),
            ('state', '=', 'draft'),
            ('picking_type_id', '=', picking_type_id.id),
            ('company_id', '=', self.env.context.get('company_id') or self.env.user.company_id.id)
        )
        return domain

    @api.multi
    def button_draft(self):
        for rec in self:
            rec.state = 'draft'
            rec.raw_line_ids.do_uncancel()
            rec.plan_line_ids.do_uncancel()
        return True

    @api.multi
    def cek_sisa_qty(self):
        for record in self:
            if record.sisa_qty != 0.0:
                raise UserError(_("Sisa Quantity Harus sama dengan nol"))
            else:
                return True

    @api.multi
    def copy(self, default=None):
        default = dict(default or {})
        self.ensure_one()
        default.update({
            'state': 'draft',
            'name': self._get_default_name(),
        })
        return super(AssemblyPlan, self).copy(default)

    @api.multi
    def unlink(self):
        if self.state not in ('draft', 'cancel'):
            raise UserError(_('Invalid Action!'))
        return super(AssemblyPlan, self).unlink()

    @api.multi
    def button_to_approve(self):
        for record in self:
            if record.sisa_qty:
                record.cek_sisa_qty()
            record.write({'state': 'to approve'})
        return True

    @api.multi
    def button_procurement(self):
        for record in self:
            record.create_purchase_order()
            record.write({'state': 'procurement'})
        return True


    @api.depends('plan_line_ids.new_qty', 'total_quantity')
    def compute_sisa_qty(self):
        for record in self:
            total_sisa = 0.0
            for sisa in record.plan_line_ids:
                total_sisa += sisa.new_qty
            self.sisa_qty = total_sisa - self.total_quantity

    @api.multi
    def button_done(self):
        for record in self.raw_line_ids:
            if record.amount_qty > record.qty_available:
                raise UserError (_("Not Enough Stock, process to Purchase Order"))
            else:
                self.write({'state': 'approve'})
        return True

    @api.multi
    def action_cancel(self):
        self.write({'state': 'cancel'})
        return True

    @api.multi
    def update_qty(self):
        for record in self:
            ratio_list = [line.ratio for line in record.plan_line_ids]
            total_ratio = sum(ratio_list)

            for key in record.plan_line_ids:
                new_quantity = round(record.total_quantity * key.ratio / total_ratio)
                key.update({
                    'new_qty': new_quantity
                })

            count = len(record.raw_line_ids)
            if count:
                for prod in record.raw_line_ids:
                    prod.update({
                        'total_quantity': record.total_quantity / count
                    })























