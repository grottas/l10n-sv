# -*- coding: utf-8 -*-
{
    'name': "POS Tip Custom",
    'summary': """propinas customizadas""",
    'description': """
   propinas customizadas
        """,
    'author': "Expertha(Nestor Ulloa)",
    'website': "",
    'license': 'GPL-3',
    'category': 'Localization',
    'version': '1.1',
    'depends': ['base', 'point_of_sale', 'pos_restaurant', 'custom_pos_receipt'],
    'data': [
        # 'report/report_zm.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            "pos_tip_custom/static/src/xml/ReceiptScreen/OrderReceipt.xml",
        ],
        'point_of_sale.assets': [
            # "custom_pos_receipt/static/src/js/screens.js",
        ]
    },
    'demo': [
    ],
    'installable': True,
    'application': False,
    'auto_install': True,

}
