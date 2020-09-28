from odoo import api, fields, models, _


class PurchaseCreatedMessage(models.TransientModel):
    _name = 'purchase_created_message.wizard'
    _description = 'Menampilkan Pesan Bila Belum Membuat PO'

    work_order_id = fields.Many2one(comodel_name="mrp.workorder", string="Work Order Referencce")
    name = fields.Char(related="work_order_id.name")

    @api.model
    def default_get(self, fields_list):
        res = super(PurchaseCreatedMessage, self).default_get(fields_list)
        if 'work_order_id' in fields_list and not res.get('work_order_id') and self._context.get(
                'active_model') == 'mrp.workorder' and self._context.get('active_id'):
            res['work_order_id'] = self._context['active_id']
        return res

    @api.multi
    def action_confirm_yes(self):
        return {
            'name': _('Create Purchase Order'),
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'vendor.invoice.wizard',
            'view_id': self.env.ref('textile_assembly.vendor_invoice_wizard_view_form').id,
            'type': 'ir.actions.act_window',
            'context': {
                'product_ids': self.work_order_id.product_service_ids.filtered(
                    lambda x: not x.has_po).mapped('product_id').ids,
                'active_model': self._context['active_model'],
                'active_id': self._context['active_id'],
            },
            'target': 'new',
        }

    @api.multi
    def action_confirm_no(self):
        return self.work_order_id._set_record_production()
