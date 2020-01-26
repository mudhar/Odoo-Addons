from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PurchaseCreatedMessage(models.TransientModel):
    _name = 'purchase_created_message.wizard'
    _description = 'Menampilkan Pesan Bila Belum Membuat PO'

    work_order_id = fields.Many2one(comodel_name="mrp.workorder", string="Work Order Referencce")
    name = fields.Char(related="work_order_id.name")
    choice = fields.Selection(string="Your Choice",
                              selection=[('yes', 'Yes'),
                                         ('no', 'No'), ], default='no')

    @api.model
    def default_get(self, fields_list):
        res = super(PurchaseCreatedMessage, self).default_get(fields_list)
        if 'work_order_id' in fields_list and not res.get('work_order_id') and self._context.get(
                'active_model') == 'mrp.workorder' and self._context.get('active_id'):
            res['work_order_id'] = self._context['active_id']
        return res

    @api.multi
    def action_confirm(self):
        for wizard in self:
            close = {'type': 'ir.actions.act_window_close'}
            if not wizard.choice:
                raise UserError(_("Anda Wajib Memilih Choice"))
            if wizard.choice == 'no':
                return wizard.work_order_id._set_record_production()
            elif wizard.choice == 'yes':
                return close
