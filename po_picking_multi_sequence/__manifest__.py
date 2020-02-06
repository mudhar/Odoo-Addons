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
1. PICKING OUTGOING GOODS, SRC SALES ORDER. PREFIX CUSTOMER CODE.
2. PICKING INCOMING GOODS, SRC WORK ORDER, PREFIX STBJ.
3. PICKING OUTGOING MATERIALS, SRC MANUFACTURING ORDER, PREFIX SJPB.
4. PICKING INCOMING MATERIALS, SRC PURCHASE ORDER, PREFIX STBN.
5. PURCHASE ORDER REFERENCE MATERIALS, PREFIX POBN.
6. PURCHASE ORDER REFERENCE SERVICE, PREFIX SUBPO.
7. PICKING OUTGOING MATERIALS, PURCHASE RETURN, PREFIX SRJB
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
