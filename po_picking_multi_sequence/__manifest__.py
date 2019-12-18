# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Multi Select Sequence Number',
    'version' : '11.0.1',
    'author' : 'odoo-consultants',
    'summary': 'Multi Select Sequence Number',
    'description': """
Generate Multi Sequence Number Based On Selected Field
    # SPBN -> Bahan Baku -> Picking Outgoing\n
    # SPBJ -> Bahan Jadi -> Picking Outgoing\n
    # STBN -> Bahan Baku -> Picking Incoming\n
    # STBJ -> Bahan Jadi -> Picking Incoming\n
    # POBN -> Bahan Baku -> PO\n 
    # POBJ -> Bahan Jadi -> PO\n
    """,
    'category': 'Tools',
    'website': 'https://www.odoo-consultants.com',
    'depends': [
        'mrp',
        'purchase',
        'sale',

    ],
    'data': [
        'data/purchase_sequence_views.xml',
        'data/picking_sequence_views.xml',

        'views/purchase_views.xml',
        'views/product_views.xml',
        'views/stock_views.xml',
        'views/sale_order_views.xml',
    ],
    'demo': [

    ],
    'qweb': [

    ],
    'installable': True,
    'application': True,
}
