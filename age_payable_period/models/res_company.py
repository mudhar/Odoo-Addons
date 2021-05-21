from odoo import fields, models


class ResCompany(models.Model):
    """
    Inherit Res Company
    """
    _inherit = 'res.company'
    _description = 'Res Company'

    column1_from = fields.Integer('Column 1 - From', default=1)
    column1_to = fields.Integer('Column 1 - To', default=30)
    column2_from = fields.Integer('Column 2 - From', default=31)
    column2_to = fields.Integer('Column 2 - To', default=60)
    column3_from = fields.Integer('Column 3 - From', default=61)
    column3_to = fields.Integer('Column 3 - To', default=90)
    column4_from = fields.Integer('Column 4 - From', default=91)
    column4_to = fields.Integer('Column 4 - To', default=120)


