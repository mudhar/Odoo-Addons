# -*- coding: utf-8 -*-
{
    'name': "Report Sale Excel",

    'summary': """
        Export Sale Orders To Excel Report""",

    'description': """
        Export Sale Orders To Excel Report
    """,

    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Sales',
    'sequence': 1,
    'version': '13.0.1',

    # any module necessary for this one to work correctly
    'depends': ['sale', 'report_xlsx'],

    # always loaded
    'data': [
        'report/report_sale_xlsx.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
