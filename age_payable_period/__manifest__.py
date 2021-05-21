{
    'name': "Extend Age Payable Report",

    'summary': """
        Set Period on Column Report, Get values based on settings""",

    'description': """
        Set Period on Column Report, Get values based on settings
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
        'views/res_config_settings_views.xml',
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
