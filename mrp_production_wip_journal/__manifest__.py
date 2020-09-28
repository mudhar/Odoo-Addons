# -*- coding: utf-8 -*-
{
    'name': "Journal WIP Pada Production",

    'summary': """
       Membuat Dua Jurnal WIP Jasa Dan WIP Material
        """,
    'description': """
Terbentuk Dua Jurnal Pada Produksi
==================================
1. Bila Ada Stock Move Pada Finish Goods, Terbentuk Jurnal WIP Untuk Biaya Produksi.
2. Bila Terdapat Selisih Pada WIP Material, User Dapat Melakukan Penyesuain Selisih WIP Tsb.
 """,

    'author': "odoo-consultants",
    'website': "http://www.odoo-consultants.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Manufacturing',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'stock_account', 'textile_assembly'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'wizards/journal_wip_message_wizard_views.xml',

        'views/res_company_views.xml',
        'views/mrp_production_views.xml',
        'views/menu_mrp_production_accounting.xml',
        'views/mrp_workorder_views.xml',

    ],
    'installable': True,
    'application': True,
}
