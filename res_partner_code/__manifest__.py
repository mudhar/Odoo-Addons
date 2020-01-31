# -*- coding: utf-8 -*-
{
    'name': "Partner Code",

    'summary': """
        Code Unique Untuk Tiap Customer Dan CMT""",

    'description': """
RES PARTNER CODE INFO
=====================
1. Ketika Membuat Customer Baru , Kode Untuk Customer Tsb Perlu Diisi. Begitu Pula Bila Ada Contact Pada Customer tsb. Maksimal Code 5 Digit
2. Ketika Membuat CMT Baru , Kode Untuk CMT Tsb Perlu Diisi. Begitu Pula Bila Ada Contact Pada CMT tsb. Maksimal Code 3 Digit.
3. Jika Ada Bug Mohon Bantuannya Ikut Memperbaiki
    """,

    'author': "odoo-consultants",
    'website': "http://www.odoo-consultants.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Partner',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/res_partner_views.xml',
    ],

}
