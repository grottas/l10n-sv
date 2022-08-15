# -*- coding: utf-8 -*-
{
    'name': "sv_reports",

    'summary': """
       Agrega el asistente para crear reportes a partir del catalogo de cuentas y no por tipos de cuentas""",

    'description': """
       Agrega el asistente para crear reportes a partir del catalogo de cuentas y no por tipos de cuentas
    """,

    'author': "Roberto Leonel Gracias",
    'website': "",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '15.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account_accountant'],

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
