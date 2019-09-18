# -*- coding: utf-8 -*-
{
    'name': "MRP Daily Report",

    'summary': """
       MRP Daily Report""",

    'description': """
        MRP Daily Report
    """,

    'author': "My Company",
    'website': "http://www.yourcompany.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Report',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'mrp', 'stock', 'product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/mrp_workorder_view_report.xml',
        'views/mrp_wip_view_report.xml',

        'wizards/mrp_select_report_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
}