# -*- coding: utf-8 -*-
{
    'name': "Assembly Cleaner",

    'summary': """
       Delete  Data Related to Assembly""",

    'description': """
       Delete  Data Related to Assembly
    """,

    'author': "odoo-consultants",
    'website': "http://www.odoo-consultants.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/11.0/odoo/addons/base/module/module_data.xml
    # for the full list
    'category': 'Tools',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'views/res_config_settings_views.xml',
    ],

}