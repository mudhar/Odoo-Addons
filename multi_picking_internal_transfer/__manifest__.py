# -*- coding: utf-8 -*-
{
    'name': "Multi Picking Internal Transfer",

    'summary': """
    Buat Picking Baru Dari Picking Yang TerValidasi\n
    Hanya Digunakan Untuk Picking Internal Transfer\n
        """,

    'description': """
MULTI PICKING INTERNAL TRANSFER
===============================
1. TRANSFER ANTAR TOKO KE GUDANG MELALUI LOKASI TRANSIT
    """,

    'author': "odoo-consultants",
    'website': "http://www.odoo-consultants.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Stock',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['stock', 'textile_assembly'],

    # always loaded
    'data': [
        'views/stock_picking_views.xml',
    ],
    # only loaded in demonstration mode
    'demo': [

    ],
    'installable': True,
    'application': True,
}