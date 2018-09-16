# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.
{
    'name' : 'Textile Assembly Production',
    'version' : '1',
    'author' : 'odoo-consultants',
    'summary': 'Textile Assembly Production',
    'description': """
Textile Assembly Production.
    """,
    'category': 'Mrp',
    'website': 'https://www.odoo-consultants.com',
    'depends': ['base', 'product', 'mrp', 'stock', 'purchase', 'contoh_mrp_bom'],
    'data': [
        'views/assembly_plan_views.xml',
        'views/assembly_production_views.xml',
        'views/assembly_menu_views.xml',
        'views/res_company_views.xml',
        'data/assembly_sequence.xml',

    ],
    'demo': [

    ],
    'qweb': [

    ],
    'installable': True,
    'application': False,
    'auto_install': False,

}
