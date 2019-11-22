# -*- coding: utf-8 -*-
##############################################################################
# For copyright and license notices, see __openerp__.py file in root directory
##############################################################################
from openerp import models, fields, api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    group_id = fields.Many2one(comodel_name="procurement.group", string="Procurement Group", copy=False)

    def search(self, cr, uid, args, offset=0, limit=None, order=None,
               context=None, count=False):
        if context and context.get('group_id'):
            args += [('group_id', '=', context['group_id'])]
        return super(PurchaseOrder, self).search(
            cr, uid, args, offset=offset, limit=limit, order=order,
            context=context, count=count)
