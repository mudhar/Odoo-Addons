from openerp import models, fields, api, _


class MrpRequestReject(models.TransientModel):

    """ Ask a reason for the MRP Request Reject."""
    _name = 'mrp.request.reject'
    _description = __doc__

    reason_id = fields.Text(string="Reason", required=True)

    @api.one
    def confirm_reject(self):
        act_close = {'type': 'ir.actions.act_window_close'}
        request_ids = self._context.get('active_ids')
        if request_ids is None:
            return act_close
        assert len(request_ids) == 1, "Only 1 Request ID expected"
        request = self.env['mrp.request.product'].browse(request_ids)
        request.reject_reason_id = self.reason_id

        request.button_reject()

        return act_close