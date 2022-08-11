{
    'name': 'Manage combos at the pos restaurant',
    'version': '15.0.0.0.0',
    'author': 'Ganemo',
    'website': 'https://www.ganemo.co',
    'live_test_url': 'https://www.ganemo.co/demo',
    'summary': "Allows the management of Combos from the Point of Sale Restaurant",
    'description': """
    You can create Combo type products, associated with several products. When you choose the "Combo", add, remove, through a dynamic selection, the items or
    products that make up the combo.
    """,
    'category': 'Point of Sale',
    'depends': [
        'pos_combo_reload',
        'pos_epson_printer_restaurant',
        'pos_restaurant_get_order_line'
    ],
    'assets': {
        'point_of_sale.assets': [
            '/pos_combo_reload_restaurant/static/src/js/PosSelectionComboRest.js',
        ],
    },
    "auto_install": False,
    "installable": True,
    'license': "Other proprietary",
    'currency': "USD",
    'price': 158,
}
