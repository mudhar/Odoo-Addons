# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2004-2010 Tiny SPRL (<http://tiny.be>).
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################


{
    'name': 'CashBack on Sales Order',
    'version': '1.1',
    'category': 'Extra',
    'description': """
Add additional CashBack information to the sales order and account invoice.
===================================================
""",
    'author': 'odoo-consultants',
    'website': 'https://www.odoo-consultants.com',
    'depends': ['sale', 'stock', 'stock_account', 'account'],
    'data': ['views/sale_order_views.xml',
             'views/account_invoice_views.xml',
             'wizards/account_invoice_wizard_views.xml'],
    'demo': [],
    'test': [],
    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
