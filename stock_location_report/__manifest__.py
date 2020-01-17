# -*- coding: utf-8 -*-
{
    'name': "Stock Location Report",

    'summary': """
    Report Untuk Melihat Pergerakan Stock Setiap Gudang \n
       """,

    'description': """
       Report Untuk Melihat Pergerakan Stock Setiap Gudang
    """,

    'author': "odoo-consultants",
    'website': "http://www.odoo-consultants.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Report',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['stock'],

    # always loaded
    'data': [
        'views/stock_location_report_report.xml',
        'views/stock_location_report_pdf_report.xml',

        'wizard/stock_location_report_wizard_view.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
    'installable': True,
    'application': True,
}