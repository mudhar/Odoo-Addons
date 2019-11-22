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
    'name': 'Group Purchase Order Based On Procurement Group',
    'version': '1.0',
    'category': 'Purchase',
    'description': """
Purchase Management & Procurement.
====================================

Create Purchase Order Based On Grouping(Procurement Group):
--------------------------------------------
    * Override Search Purchase Order Model With Domain Group ID
    * Get Values Of Schedule Date From Procurement Order
    
    """,
    'author': 'Odoo Consultants',
    'depends': ['purchase',
                'procurement',],
    'data': [
             ],
    'demo': [
    ],
    'test': [
    ],
    'installable': True,
    'auto_install': False,
}
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
