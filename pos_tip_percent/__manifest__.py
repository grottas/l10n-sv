# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.


{
    'name': 'Point of Sale Tip Percent',
    'version': '1.0',
    'category': 'Sales/Point of Sale',
    'sequence': 6,
    'summary': 'Simple Discounts in the Point of Sale ',
    'description': """

This module allows the cashier to quickly give percentage-based
discount to a customer.

""",
    'depends': ['point_of_sale', 'pos_discount', 'pos_restaurant', 'pos_tip_custom'],
    'data': [
        'views/pos_tip_views.xml',
        ],
    'installable': True,
    'assets': {
        'point_of_sale.assets': [
            'pos_tip_percent/static/src/js/**/*',
        ],
        'web.assets_qweb': [
            'pos_tip_percent/static/src/xml/**/*',
        ],
    },
    'license': 'LGPL-3',
}
