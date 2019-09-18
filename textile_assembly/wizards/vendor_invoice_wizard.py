from odoo import api, fields, models, _
from odoo.addons import decimal_precision as dp
from odoo.exceptions import UserError


class VendorInvoiceWizard(models.TransientModel):
    _name = 'vendor.invoice.wizard'
    _description = 'Wizard Buat Invoice Dari Quantity Good'

    @api.model
    def _get_default_picking_type_id(self):
        return self.env['stock.picking.type'].search([('code', '=', 'incoming'),
                                                      ('warehouse_id.company_id', 'in',
                                                       [self.env.context.get('company_id', self.env.user.company_id.id), False])], limit=1).id

    work_order_id = fields.Many2one(comodel_name="mrp.workorder", string="Work Order")

    partner_id = fields.Many2one(comodel_name="res.partner", string="Vendor")
    product_id = fields.Many2one(comodel_name="product.product", string="Products", domain="[('type','=','service')]")
    product_qty = fields.Float(string="Quantity Good", digits=dp.get_precision('Product Unit of Measure'),
                               compute="_get_quantity_good")
    product_uom_id = fields.Many2one(
        'product.uom', 'Product Unit of Measure', related="product_id.uom_id")
    price_unit = fields.Float(string="Unit Price", digits=dp.get_precision('Product Price'),
                              default=0.0, help="Estimasi Biaya Produksi Produk Per Unit")
    date_order = fields.Datetime('Date', copy=False, default=fields.Datetime.now, index=True,
                                         required=True)

    @api.model
    def default_get(self, fields_list):
        res = super(VendorInvoiceWizard, self).default_get(fields_list)
        if 'work_order_id' in fields_list and not res.get('work_order_id') and self._context.get(
                'active_model') == 'mrp.workorder' and self._context.get('active_id'):
            res['work_order_id'] = self._context['active_id']

        if 'partner_id' in fields_list and not res.get('partner_id') and res.get('work_order_id'):
            res['partner_id'] = self.env['mrp.workorder'].browse(res['work_order_id']).partner_id.id

        return res

    @api.multi
    @api.depends('work_order_id',
                 'work_order_id.qc_ids',
                 'work_order_id.qc_ids.state')
    def _get_quantity_good(self):
        quantity_good = sum(self.work_order_id.qc_ids.filtered(
            lambda x: x.qc_good and x.state == 'done').mapped('qc_good'))
        self.product_qty = quantity_good

    @api.onchange('product_id')
    def onchange_product_id(self):
        if self.product_id:
            price_unit = self.work_order_id.product_service_ids.filtered(lambda x: x.product_id.id == self.product_id.id).mapped('price_unit')
            self.price_unit = sum(price_unit)

    # @api.model
    # def _default_journal(self):
    #     if self._context.get('default_journal_id', False):
    #         return self.env['account.journal'].browse(self._context.get('default_journal_id'))
    #     domain = [
    #         ('type', '=', 'purchase'),
    #         ('company_id', '=', self.work_order_id.company_id.id),
    #     ]
    #     return self.env['account.journal'].search(domain, limit=1)

    @api.multi
    def action_confirm(self):
        self.action_create_purchase_order()
        self.work_order_id.write({'purchase_created': True})
        return {'type': 'ir.actions.act_window_close'}

    # @api.multi
    # def create_invoice(self):
    #     invoice_obj = self.env['account.invoice']
    #     for record in self:
    #         journal_id = self._default_journal()
    #         account_id = record.partner_id.property_account_payable_id.id
    #         partner_id = record.partner_id
    #
    #         invoice_domain = invoice_obj.search([('work_order_id', '=', record.work_order_id.id),
    #                                              ('state', 'not in', ('paid', 'open', 'cancel'))])
    #
    #         if not invoice_domain:
    #             invoice_data = {'type': 'in_invoice',
    #                             'partner_id': partner_id.id,
    #                             'account_id': account_id,
    #                             'currency_id': record.work_order_id.currency_id.id,
    #                             'journal_id': journal_id.id,
    #                             'company_id': record.work_order_id.company_id.id,
    #                             'work_order_id': record.work_order_id.id,
    #                             'origin': record.work_order_id.production_id.name,
    #                             }
    #             invoice_id = invoice_obj.create(invoice_data)
    #
    #             invoice_lines = []
    #             inv_line_data = record._prepare_invoice_line(invoice_id, journal_id, partner_id)
    #             invoice_lines.append((0, 0, inv_line_data))
    #
    #             invoice_id.write({'invoice_line_ids': invoice_lines})
    #             view_id = self.env.ref('account.invoice_supplier_form')
    #             return {'name': _("New Invoice"),
    #                     'view_mode': 'form',
    #                     'view_id': view_id.ids,
    #                     'view_type': 'form',
    #                     'res_model': 'account.invoice',
    #                     'type': 'ir.actions.act_window',
    #                     'nodestroy': True,
    #                     'res_id': invoice_id.id,
    #                     'target': 'current',
    #                     'context': {'default_type': 'in_invoice'}
    #                     }

    @api.multi
    def action_create_purchase_order(self):
        self.ensure_one()
        po_obj = self.env['purchase.order']
        for order in self:
            po_domain = po_obj.search([('work_order_id', '=', order.work_order_id.id),
                                       ('state', '=', 'draft')])
            if not po_domain:
                production_reference = order.work_order_id.production_id.name
                workorder_reference = order.work_order_id.name
                picking_type_id = order._get_default_picking_type_id()

                po_data = {
                    'work_order_id': order.work_order_id.id,
                    'name': 'New',
                    'state': 'draft',
                    'picking_type_id': picking_type_id,
                    'partner_id': order.partner_id.id,
                    'company_id': order.work_order_id.company_id.id,
                    'currency_id': order.work_order_id.currency_id.id,
                    'date_order': order.date_order,
                    'origin': production_reference + '->' + workorder_reference,
                    'product_select_type': 'subpo',
                }
                po_id = self.env['purchase.order'].create(po_data)
            else:
                po_id = po_domain[0]
            order._prepare_purchase_order_line(po_id)

    def _prepare_purchase_order_line(self, po_id):
        for wiz in self:
            po_uom_qty = wiz.product_uom_id._compute_quantity(wiz.product_qty, wiz.product_id.uom_po_id)

            seller = wiz.product_id._select_seller(
                partner_id=wiz.partner_id,
                quantity=po_uom_qty,
                date=wiz.date_order,
                uom_id=wiz.product_id.uom_po_id
            )
            taxes = wiz.product_id.supplier_taxes_id
            fpos = wiz.partner_id.property_account_position_id
            taxes_id = fpos.map_tax(taxes) if fpos else taxes
            if taxes_id:
                taxes_id = taxes_id.filtered(lambda x: x.company_id.id == wiz.work_order_id.company_id.id)

            price_unit = self.env['account.tax']._fix_tax_included_price_company(seller.price,
                                                                                 wiz.product_id.supplier_taxes_id,
                                                                                 taxes_id,
                                                                                 wiz.work_order_id.company_id) if seller else 0.0
            if price_unit and seller and po_id.currency_id and seller.currency_id != po_id.currency_id:
                price_unit = seller.currency_id.compute(price_unit, po_id.currency_id)

            product_lang = wiz.product_id.with_context({
                'lang': wiz.partner_id.lang,
                'partner_id': wiz.partner_id.id,
            })
            name = product_lang.display_name
            if product_lang.description_purchase:
                name += '\n' + product_lang.description_purchase

            lines_data = {
                'name': name,
                'product_qty': po_uom_qty,
                'product_id': wiz.product_id.id,
                'product_uom': wiz.product_id.uom_po_id.id,
                'price_unit': price_unit or wiz.price_unit,
                'date_planned': wiz.date_order,
                'taxes_id': [(6, 0, taxes_id.ids)],
                'order_id': po_id.id
            }
            return self.env['purchase.order.line'].create(lines_data)







    # def _prepare_invoice_line(self, invoice_id, journal_id, partner_id):
    #
    #     invoice_line = self.env['account.invoice.line']
    #     taxes = self.product_id.supplier_taxes_id
    #     fpos = partner_id.property_account_position_id
    #     taxes_id = fpos.map_tax(taxes) if fpos else taxes
    #     if taxes_id:
    #         taxes_id = taxes_id.filtered(lambda x: x.company_id.id == self.work_order_id.company_id.id)
    #     invoice_data = {
    #         'product_id': self.product_id.id or False,
    #         'name': self.product_id.display_name,
    #         'quantity': self.product_qty,
    #         'uom_id': self.product_uom_id.id,
    #         'invoice_id': invoice_id.id,
    #         'account_id': invoice_line.with_context({'journal_id': journal_id.id,
    #                                                  'type': 'in_invoice'})._default_account(),
    #         'price_unit': self.work_order_id.currency_id.compute(self.price_unit, invoice_line.currency_id,
    #                                                      round=False),
    #         'invoice_line_tax_ids': [(6, 0, taxes_id.ids)]
    #     }
    #     return invoice_data





