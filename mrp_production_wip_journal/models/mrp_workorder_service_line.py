# -*- coding: utf-8 -*-
from odoo import fields, models


class WorkOrderService(models.Model):
    _inherit = 'mrp.workorder.service.line'

    account_move_ids = fields.One2many(comodel_name="account.move", inverse_name="work_order_service_id",
                                       string="Work Order Service Reference")

