# -*- coding: utf-8 -*-
{
    'name': "Product Template Constraints",

    'summary': """
        Product Duplicate Constraints""",

    'description': """
Product Duplicate Constraints Detail
====================================
1. Tidak Dapat Membuat Produk, Bila Assembly Code Sudah Ada
2. Generate Internal Reference Pada Product Variant Bila Is Goods, Assembly Code, Variant Diisi
3. Contoh Assembly Code => KP17A => Variant S, M, L = KP17A S, KP17A M
    """,

    'author': "odoo-consultants",
    'website': "http://www.odoo-consultants.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Product',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['textile_assembly', 'product'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        # 'views/product_template_views.xml',
    ],
}
