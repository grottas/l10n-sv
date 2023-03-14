{
    'name': 'Print your combo order for the kitchen',
    'version': '15.0.0.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'summary': 'Allows you to send the combo order to the kitchen printer without using the IoT Box',
    'Description': """Without using the IoT Box, you can choose the printer you will send your kitchen combo receipts to.
     After adding a combo to your order, you can send the print to the kitchen.""",
    'category': 'Point of Sale',
    'live_test_url': 'https://www.ganemo.co/demo',
    'depends': [
        'pos_kitchen_receipt_without_iot',
        'pos_combo_reload_restaurant',
    ],
    'assets': {
        'point_of_sale.assets': [
            '/pos_kitchen_receipt_combo/static/src/js/pos.js',
        ],
        'web.assets_qweb': [
            'pos_kitchen_receipt_combo/static/src/xml/pos_receipt_combo.xml',
        ],
    },
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 82.00
}
