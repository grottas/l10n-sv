# -*- coding: utf-8 -*-
{
    'name': "Financiero-SV-Sucursal",

    'summary': """Allows users to print Purchase Report, Sales Report either taxpayer or consumer by invoices or tickets""",

    'description': "Creación de Reportes para Compras, Ventas Contribuyentes, Ventas Consumidores y Ventas por tickets",

    'author': "El Salvador",
    'website': "http://yoursite.com",

    # Categories can be used to filter modules in modules listing
    # Check https://github.com/odoo/odoo/blob/15.0/odoo/addons/base/data/ir_module_category_data.xml
    # for the full list
    'category': 'Reporting',
    'version': '1.0',

    # any module necessary for this one to work correctly
    'depends': ['base','account','sv_accounting','purchase'],

    # always loaded
    'data': [
        'reports.xml',
        'security/ir.model.access.csv',
        'views/balance_report_pdf_view.xml',
        'views/mayor_report_pdf_view.xml',
        'views/auxiliar_report_pdf_view.xml',
        'views/general_report_pdf_view.xml',
        'views/resultado_report_pdf_view.xml',
        #'views/ticket_report_pdf_view.xml',
        'wizard/wizard_balance_report.xml',
        'wizard/wizard_mayor_report.xml',
        'wizard/wizard_auxiliar_report.xml',
        'wizard/wizard_general_report.xml',
        'wizard/wizard_resultado_report.xml',
    ],
    # only loaded in demonstration mode
    'qweb': [],
    'instalable': True,
    'auto_install': False,
}
