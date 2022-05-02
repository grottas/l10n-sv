# -*- coding: utf-8 -*-
{
    'name': "inicio",

    'summary': """
       contiene las funcionalidades para realizar las cargas iniciales""",

    'description': """
       contiene las funcionalidades para realizar las cargas iniciales
    """,

    'author': "Roberto Leonel Gracias",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '15.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account'],

    # always loaded
    'data': [
        'views/views.xml',
        'security/ir.model.access.csv',
        'data/data.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
