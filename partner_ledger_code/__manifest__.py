# -*- coding: utf-8 -*-
{
    'name': "Extend Account Partner Ledger Report",

    'summary': """
       Update Value Column of Account with value account name + account code""",

    'description': """
        Update Value Column of Account with value account name + account code
    """,

    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Extra Tools',
    'sequence': 1,
    'version': '13.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['account_reports'],

    # always loaded
    'data': [

    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
