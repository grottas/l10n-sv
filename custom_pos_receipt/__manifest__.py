{
    'name': 'Custom POS Receipt',
    'category': 'Sales/Point of Sale',
    'summary': '',
    'description': "Customized our point of sale receipt",
    'version': '15.0.1.0',
    'license': 'GPL-3',
    'author': "Expertha(Nestor Ulloa)",
    'depends': ['base', 'point_of_sale', 'contacts', 'sv_partner'],
    'data': [
        'data/precision_POS.xml',
    ],
    'assets': {
        'web.assets_qweb': [
            "custom_pos_receipt/static/src/xml/cliente.xml",
            "custom_pos_receipt/static/src/xml/pos.xml",
        ],
        'point_of_sale.assets':[
             "custom_pos_receipt/static/src/js/models.js",
             "custom_pos_receipt/static/src/js/screens.js",
        ]
    },
    'installable': True,
}
