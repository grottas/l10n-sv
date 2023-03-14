{
    'name': 'Print your order for the kitchen',
    'version': '15.0.2.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'summary': 'Allows you to send the order to the kitchen printer without using the IoT Box.',
    'category': 'Point of Sale',
    'live_test_url': 'https://www.ganemo.co/demo',
    'depends': ['pos_restaurant'],
    'data': ['views/views.xml'],
    'assets': {
        'point_of_sale.assets': [
            '/pos_kitchen_receipt_without_iot/static/src/js/pos.js',
            '/pos_kitchen_receipt_without_iot/static/src/js/pos_orderlines_especial_lines.js',
            '/pos_kitchen_receipt_without_iot/static/src/js/print.min.1.6.0.js',
        ],
        'web.assets_qweb': [
            'pos_kitchen_receipt_without_iot/static/src/xml/**/*',
        ],
    },
    'images': ['static/description/receipt.jpg'],
    'installable': True,
    'auto_install': False,
    'license': 'Other proprietary',
    'currency': 'USD',
    'price': 72.00
}
