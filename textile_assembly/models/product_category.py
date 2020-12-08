# -*- coding: utf-8 -*-
from odoo import fields, models


class ProductCategory(models.Model):
    _inherit = 'product.category'

    account_analytic_id = fields.Many2one(comodel_name='account.analytic.account', string='Analytic Account')



