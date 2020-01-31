from odoo import api, fields, models, _
from odoo.exceptions import UserError


class JournalMessageWizard(models.TransientModel):
    _name = 'journal_wip.message_wizard'
    _description = 'Message Only'

    production_id = fields.Many2one(comodel_name="mrp.production", string="Manufacturing Order", required=True)
    choice = fields.Selection(selection=[('yes', 'Yes'), ('no', 'No'), ],default='no')

    @api.model
    def default_get(self, fields_list):
        res = super(JournalMessageWizard, self).default_get(fields_list)
        if 'production_id' in fields_list and not res.get('production_id') and self._context.get(
                'active_model') == 'mrp.production' and self._context.get('active_id'):
            res['production_id'] = self._context['active_id']
        return res

    @api.multi
    def action_confirm(self):
        for wiz in self:
            if not wiz.choice:
                raise UserError(_("Silahkan Pilih Jawaban Anda"))

            if wiz.choice == 'yes':
                return {'type': 'ir.actions.act_window_close'}
            else:
                return {
                    'name': _('Adjust WIP Differ'),
                    'view_type': 'form',
                    'view_mode': 'form',
                    'res_model': 'production_journal.wip_wizard',
                    'view_id': self.env.ref('mrp_production_wip_journal.production_journal_wip_wizard_view_form').id,
                    'type': 'ir.actions.act_window',
                    'context': self.env.context,
                    'target': 'new',
                }