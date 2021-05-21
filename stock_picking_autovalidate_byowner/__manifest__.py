{
    'name': "Auto Validate Stock Picking Move By Product Owner",

    'summary': """
        Auto Validate Stock Move By Product Owner From Sale Order Line""",

    'description': """
    Auto Validate Stock Move By Product Owner From Sale Order Line
    """,

    'author': "Port Cities",
    'website': "http://www.portcities.net",
    'category': 'Sales',
    'sequence': 1,
    'version': '13.0.1.0',

    # any module necessary for this one to work correctly
    'depends': ['sale_stock'],

    # always loaded
    'data': [
        # 'security/ir.model.access.csv',
        'views/sale_order_line_views.xml'
    ],
    'auto_install': False,
    'installable': True,
    'application': False,
}
