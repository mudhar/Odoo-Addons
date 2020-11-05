# -*- coding: utf-8 -*-
{
    'name': "Stock Picking Import Wizard",

    'summary': """
      Import Stock Move Items From Stock Picking
        """,

    'description': """
        Import Stock Move CSV File From Stock Picking Page
    """,

    'author': "odoo-consultans",
    'website': "http://www.odoo-consultants.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Stock',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/stock_picking_views.xml',
    ],

}