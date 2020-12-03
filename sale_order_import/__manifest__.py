# -*- coding: utf-8 -*-
{
    'name': "Sale Order Line Import Wizard",

    'summary': """
        Import Product From CSV File To Sale Order Lines""",

    'description': """
Import Product From CSV File To Sale Order Lines
================================================
1. Prefix : product, quantity, price, tax
    """,

    'author': "odoo-consultants",
    'website': "http://www.odoo-consultants.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Sale',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_order_views.xml',
    ],
}
