# -*- coding: utf-8 -*-
from odoo import fields, models


class AccountMove(models.Model):
    _inherit = 'account.move'

    work_order_service_id = fields.Many2one(comodel_name="mrp.workorder.service.line",
                                            string="Reference Work Order Service", copy=False)
    material_production_id = fields.Many2one(comodel_name="mrp.production", string="MRP Order", copy=False)


