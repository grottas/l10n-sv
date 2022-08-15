# -*- coding: utf-8 -*-
{
    'name': "sv_accunt_reports",

    'summary': """
       Agrega los campos para los reportes""",

    'description': """
       Agrega los campos para los reportes
    """,

    'author': "Roberto Leonel Gracias",
    'website': "https://rgingenierossv.com/",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '15.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

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
