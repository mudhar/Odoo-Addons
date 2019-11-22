# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2014 Odoo Consultants (<http://www.odoo-consultants.com/>)
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
    'name': 'Sale Report Analysis Non Tax',
    'version': '1.0',
    'category': 'Sale',
    'summary': 'Report',
    'description': """
Sale Report Analysis Non Tax
================================================================

    """,
    'author': 'Odoo Consultants',
    'depends': ['sale'],
    'data': ['wizard/sale_order_wizard_views.xml',
             'views/sale_report_views.xml',
             ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
