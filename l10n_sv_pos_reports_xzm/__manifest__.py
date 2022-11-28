# -*- coding: utf-8 -*-
{
    'name': "Reportes X, Z y Z Mensual de El Salvador",
    'summary': """Reportes X, Z y Z Mensual de El Salvador""",
    'description': """
    Localizacion de El Salvador :
        - Reportes X, Z y Z Mensual
        """,
    'author': "Expertha(Nestor Ulloa)",
    'website': "",
    'license': 'GPL-3',
    'category': 'Localization',
    'version': '1.1',
    'depends': ['base', 'point_of_sale', 'account', 'sv_accounting', 'portal', 'utm'],
    'data': [
        # 'data/action_server_x.xml',
        # 'data/action_server_z.xml',
        # 'data/action_server_zm.xml',
        # 'data/cron_corte_z.xml',
        # 'data/correlativo.xml',
        'security/ir.model.access.csv',
        'views/account_move_inherit_x.xml',
        'views/session_pos_inherit_x.xml',
        'views/pos_order_inherit_x.xml',
        'views/cortex.xml',
        'views/cortez.xml',
        'views/cortezm.xml',
        'report/reports_receipt.xml',
        'report/report_x.xml',
        'report/report_z.xml',
        'report/report_zm.xml',
    ],
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': True,

}
