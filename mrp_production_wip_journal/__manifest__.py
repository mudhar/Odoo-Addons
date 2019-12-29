# -*- coding: utf-8 -*-
{
    'name': "Journal WIP Pada Production",

    'summary': """
       Membuat Dua Jurnal WIP Jasa Dan WIP Material
        """,
    'description': """
Terbentuk Dua Jurnal Pada Produksi
==================================
1. Bila Ada Stock Move Pada Finish Goods, Terbentuk Jurnal WIP Untuk Biaya Produksi. \n
2. Bila Terdapat Selisih Pada WIP Material, User Dapat Adjust Selisih WIP Tsb. \n
 """,

    'author': "odoo-consultants",
    'website': "http://www.odoo-consultants.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Manufacturing',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base', 'account', 'stock_account', 'mrp', 'textile_assembly'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'wizards/production_journal_wip_wizard_views.xml',

        'views/res_company_views.xml',
        'views/mrp_production_views.xml',
        'views/mrp_workorder_service_line_views.xml',


    ],
    # only loaded in demonstration mode

}