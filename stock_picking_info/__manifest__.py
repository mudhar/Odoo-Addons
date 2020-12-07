# -*- coding: utf-8 -*-
{
    'name': "Stock Picking Info",

    'summary': """
       Display Info Total Quantity Received, Total Initial Quantity, Total Values Done, Total Values Initial""",

    'description': """
        Display Info Total Quantity Received, Total Initial Quantity, Total Values Done, Total Values Initial
    """,

    'author': "odoo-consultants",
    'website': "http://www.odoo-consultants.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'stock_account'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
    ],
}