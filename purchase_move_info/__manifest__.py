# -*- coding: utf-8 -*-
{
    'name': "Purchase Move Info",

    'summary': """
       Display Info Total Quantity Received And Total Amount Payable on List View""",

    'description': """
        Display Info Total Quantity Received And Total Amount Payable on List View
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