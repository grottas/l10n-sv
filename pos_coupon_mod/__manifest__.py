
{
    'name': 'Point of Sale coupon mod',
    'version': '1.0',
    'category': 'Sales/Point of Sale',
    'sequence': 6,
    'summary': 'Cupones de descuento',
    'description': 'Los cupones de descuento no toman en cuenta las propinas ni los descuentos de productos.' """

This module allows the cashier to quickly give percentage-based
discount to a customer.

""",
    'depends': ['point_of_sale', 'pos_coupon'],
    'data': [

        ],
    'installable': True,
    'assets': {
        'point_of_sale.assets': [
            'pos_discount_mod/static/src/js/**/*',
        ],
        'web.assets_qweb': [
        ],
    },
    'license': 'LGPL-3',
}
