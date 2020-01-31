from odoo import api, fields, models


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    purchase_note = fields.Text(string="Note", states={'done': [('readonly', True)]})

    @api.model
    def _prepare_picking(self):
        result = super(PurchaseOrder, self)._prepare_picking()
        if self.purchase_note and result:
            result.update({'note': self.purchase_note})
        return result
