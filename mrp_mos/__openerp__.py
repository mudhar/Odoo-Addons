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
    'name' : 'MRP Extra',
    'version' : '1.1',
    'author' : 'odoo-consultants',
    'category' : 'Tools',
    'description' : """
MRP Extra
    """,
    'website': 'https://www.odoo-consultants.com',
    'depends' : ['base', 'product', 'mrp', 'stock', 'mrp_operations', 'report', 'mrp_ppic', 'sale'],
    'data': [
        'views/mrp.xml',
        'views/res_company_views.xml',
        'views/stock_picking.xml',
        'wizards/reject_reason_views.xml',
        'wizards/workorder_pending_views.xml',

        'data/sequence_views.xml',
        'security/ir.model.access.csv',

        'report/report_mrporder.xml',
        'report/report_mrprequest_product.xml',
        'report/report_saleorder.xml',
    ],

    'installable': True,
    'auto_install': False,
}

# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
