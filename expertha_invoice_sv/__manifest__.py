# -*- coding: utf-8 -*-
{
    'name': "Facturacion de El Salvador",
    'summary': """Facturacion de El Salvador""",
    'description': """
       Facturacion de El Salvador.
       Permite Imprimir los tres tipos de facturas utilizados en El Salvador
        - Consumidor Final
        - Credito Fiscal
        - Exportaciones
      Tambien permite imprimir los documentos que retifican:
        - Anulaciones.
        - Nota de Credito
        - Anulaciones de Exportacion
      Valida que todos los documentos lleven los registros requeridos por ley
        """,
    'author': "Expertha(Nestor Ulloa)",
    'website': "http://www.expertha.com",

    'currency': 'EUR',
    'license': 'GPL-3',
    'category': 'Contabilidad',
    'version': '1.3',
    'depends': ['base', 'sv_accounting', 'sv_partner', 'account', 'product'],
    'data': [

        'report/report_invoice_anu.xml',
        'report/report_invoice_ccf.xml',
        'report/report_invoice_fcf.xml',
        'report/report_invoice_exp.xml',
        'report/report_invoice_ndc.xml',
        'report/report_invoice_digital.xml',
        'report/report_invoice_sujeto.xml',
        'report/invoice_report.xml',
        'report/report_invoice_main.xml',
        'views/account_move_view.xml',

    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
