# -*- coding: utf-8 -*-
{
    'name': "res_company_giro",

    'summary': """
       """,

    'description': """
        Agrega el campo del giro
    """,

    'author': "Nestor Ulloa - Expertha",
    'website': "/",
    'license': 'GPL-3',
    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/13.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Uncategorized',
    'version': '15.0',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'data': [
        'views/res_company_giro.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        # 'demo/demo.xml',
    ],
}
