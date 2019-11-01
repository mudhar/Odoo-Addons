from openerp import models, fields, api, _
import openerp.addons.decimal_precision as dp


class AccountInvoice(models.Model):
    _inherit = 'account.invoice'

    cash_back = fields.Float('Cash Back', digits_compute=dp.get_precision('Product Price'))
