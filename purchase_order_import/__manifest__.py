# -*- coding: utf-8 -*-
{
    'name': "Purchase Order Line Import Wizard",

    'summary': """
        Import Product From CSV File To Purchase Order Lines""",

    'description': """
        Import Product From CSV File To Purchase Order Lines
    """,

    'author': "odoo-consultants",
    'website': "http://www.odoo-consultants.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Purchase',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['purchase'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/purchase_order_views.xml',
    ],
}
