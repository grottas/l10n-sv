odoo.define('pos_discount_mod.DiscountButton', function(require) {
    'use strict';

    const PosDiscount = require('pos_discount.DiscountButton');
//    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

     const FEPosDiscount = (PosDiscount) =>
      class extends PosDiscount {
        constructor() {
            super(...arguments);
            // useListener('send-payment-adjust', this._sendPaymentAdjust);
        }

        async apply_discount(pc) {
            var order    = this.env.pos.get_order();
            var lines    = order.get_orderlines();
            var product  = this.env.pos.db.get_product_by_id(this.env.pos.config.discount_product_id[0]);
            var tip  = this.env.pos.db.get_product_by_id(this.env.pos.config.tip_product_id[0]);

           var tip_value = 0;

            for (const line of lines) {
                if (line.get_product() === tip) {
                   tip_value = line.get_price_with_tax();
                }
            }

            // Remove existing discounts
            for (const line of lines) {
                if (line.get_product() === product) {
                    order.remove_orderline(line);
                }
            }



            // Add discount
            // We add the price as manually set to avoid recomputation when changing customer.
            var base_to_discount = order.get_total_without_tax();
            if (product.taxes_id.length){
                var first_tax = this.env.pos.taxes_by_id[product.taxes_id[0]];
                if (first_tax.price_include) {
                    base_to_discount = order.get_total_with_tax();
                }
            }
            var discount = - pc / 100.0 * (base_to_discount - tip_value);

            if( discount < 0 ){
                await order.add_product(product, {
                    price: discount,
                    lst_price: discount,
                    extras: {
                        price_manually_set: true,
                    },
                });
            }
        }
    }

     Registries.Component.extend(PosDiscount, FEPosDiscount);

      return FEPosDiscount;

});
