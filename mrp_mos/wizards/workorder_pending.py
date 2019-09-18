from openerp import models, fields, api, _


class MrpProductionWorkcenterPending(models.Model):
    _name = 'mrp.production.workcenter.pending'
    _description = '__doc__'

    reason = fields.Text(string="Reason", required=True)
    # workcenter_id = fields.Many2one(comodel_name="mrp.production.workcenter.line", string="Production ID")

    @api.one
    def confirm_pending(self):
        act_close = {'type': 'ir.actions.act_window_close'}
        line_ids = self._context.get('active_ids')
        if line_ids is None:
            return act_close
        assert len(line_ids) == 1, "Only 1 sale ID expected"
        line = self.env['mrp.production.workcenter.line'].browse(line_ids)
        line.note_pending = self.reason
        # in the official addons, they call the signal on quotations
        # but directly call action_cancel on sales orders
        if line.state == 'startworking':
            line.signal_workflow('button_pause')

        return act_close
