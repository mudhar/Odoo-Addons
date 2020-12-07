# -*- coding: utf-8 -*-
{
    'name': "Multi Sub Sequence Per Date Range",

    'summary': """
        Membuat Sub Sequence Number Bila Data Sequence Di Checklist Use subsequence per date range""",

    'description': """
        Membuat Sub Sequence Number Bila Data Sequence Di Checklist Use subsequence per date range
    """,

    'author': "odoo-consultants",
    'website': "http://www.odoo-consultants.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['textile_assembly', 'stock', 'purchase', 'sale'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/views.xml',
        # 'views/templates.xml',
    ],
}