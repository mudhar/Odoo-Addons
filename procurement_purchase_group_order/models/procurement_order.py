# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from datetime import datetime
from openerp import models, api, _
from openerp.tools import DEFAULT_SERVER_DATETIME_FORMAT
from openerp.exceptions import Warning as UserError


class ProcurementOrder(models.Model):
    _inherit = 'procurement.order'

    @api.multi
    def make_po(self):
        obj = self.with_context(group_id=self.group_id.id)
        return super(ProcurementOrder, obj).make_po()

    @api.model
    def _get_po_line_values_from_proc(self, procurement, partner, company, schedule_date):
        result = super(ProcurementOrder, self)._get_po_line_values_from_proc(procurement, partner, company, schedule_date)
        if result.get('date_planned'):
            date_planned = datetime.strptime(procurement.date_planned, DEFAULT_SERVER_DATETIME_FORMAT)
            result['date_planned'] = date_planned
        return result

    @api.model
    def create_procurement_purchase_order(self, procurement, po_vals, line_vals):
        if 'group_id' not in po_vals:
            po_vals.update({'group_id': procurement.group_id.id})
        return super(ProcurementOrder, self).create_procurement_purchase_order(procurement, po_vals, line_vals)
