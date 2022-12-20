# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Point of Sale Discounts mod',
    'version': '1.0',
    'category': 'Sales/Point of Sale',
    'sequence': 6,
    'summary': 'Descuento general en POS omite la propina',
    'description': 'Descuento general en POS omite la propina' """

This module allows the cashier to quickly give percentage-based
discount to a customer.

""",
    'depends': ['point_of_sale', 'pos_discount', 'pos_tip_percent'],
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
