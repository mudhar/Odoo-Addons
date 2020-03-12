from odoo import api, fields, models, _
from odoo.exceptions import UserError


class JournalMessageWizard(models.TransientModel):
    _name = 'journal_wip.message_wizard'
    _description = 'Message Only'

    production_id = fields.Many2one(comodel_name="mrp.production", string="Manufacturing Order", required=True)

    @api.model
    def default_get(self, fields_list):
        res = super(JournalMessageWizard, self).default_get(fields_list)
        if 'production_id' in fields_list and not res.get('production_id') and self._context.get(
                'active_model') == 'mrp.production' and self._context.get('active_id'):
            res['production_id'] = self._context['active_id']
        return res

    @api.multi
    def action_confirm_yes(self):
        return {'type': 'ir.actions.act_window_close'}

    @api.multi
    def action_confirm_no(self):
        self.production_id.action_adjust_wip()
