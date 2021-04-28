# -*- coding: utf-8 -*-
{
    'name': "Picking Barcode Action",

    'summary': """
        List Picking with picking type barcode""",

    'description': """
        List Picking with picking type barcode
    """,

    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Extra Tools',
    'sequence': 1,
    'version': '13.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['barcodes', 'stock'],

    # always loaded
    'data': [
        'views/barcode_templates.xml',
        'wizard/picking_barcode_action_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
