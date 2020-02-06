# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Multi Select Sequence Number',
    'version' : '11.0.1',
    'author' : 'odoo-consultants',
    'summary': 'Multi Select Sequence Number',
    'description': """
Generate Multi Sequence Number Based On Selected Field
======================================================
1. PICKING OUTGOING GOODS, SRC SALES ORDER. FORMAT CUSTOMER CODE/YEAR/MONTH/SEQUENCE.
2. PICKING INCOMING GOODS, SRC WORK ORDER, FORMAT STBJ/YEAR/MONTH/SEQUENCE.
3. PICKING OUTGOING MATERIALS, SRC MANUFACTURING ORDER, FORMAT SJPB/YEAR/MONTH/SEQUENCE.
4. PICKING INCOMING MATERIALS, SRC PURCHASE ORDER, FORMAT SPBN/YEAR/MONTH/SEQUENCE.
5. PURCHASE ORDER REFERENCE MATERIALS, FORMAT POBN/YEAR/MONTH/SEQUENCE.
6. PURCHASE ORDER REFERENCE SERVICE, FORMAT SUBPO/YEAR/MONTH/SEQUENCE.
    """,
    'category': 'Tools',
    'website': 'https://www.odoo-consultants.com',
    'depends': [
        'mrp',
        'purchase',
        'sale',
        'res_partner_code',

    ],
    'data': [
        'data/purchase_sequence_views.xml',
        'data/picking_sequence_views.xml',

        'views/purchase_views.xml',
        'views/product_views.xml',
        'views/stock_views.xml',
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': True,
}
