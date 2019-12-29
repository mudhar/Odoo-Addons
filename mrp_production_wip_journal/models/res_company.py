# -*- coding: utf-8 -*-

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = 'res.company'

    account_valuation_material_id = fields.Many2one(comodel_name="account.account",
                                                    string="Stock Account Valuation WIP Material")
    account_valuation_service_id = fields.Many2one(comodel_name="account.account",
                                                   string="Stock Account Valuation WIP Service")
    account_expense_material_id = fields.Many2one(comodel_name="account.account",
                                                  string="Expense Account WIP Material Differ")
