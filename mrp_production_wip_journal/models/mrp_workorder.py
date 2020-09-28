from odoo import fields, models, api
from odoo.addons import decimal_precision as dp


class MrpWorkOrder(models.Model):
    _inherit = 'mrp.workorder'

    amount_wip_invoiced = fields.Float(string="Amount Invoiced", digits=dp.get_precision('Account'),
                                       compute="_compute_wip_invoiced",
                                       help="Total Biaya Product Jasa Dari Jumlah Quantity Yang Ditagih")

    @api.multi
    @api.depends('po_ids',
                 'po_ids.state')
    def _compute_wip_invoiced(self):
        for work_order in self:
            amount_purchase = work_order.po_ids.filtered(lambda x: x.state != 'cancel')
            work_order.amount_wip_invoiced = sum(amount_purchase.mapped('amount_untaxed'))

    


