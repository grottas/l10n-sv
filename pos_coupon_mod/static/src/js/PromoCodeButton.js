odoo.define('pos_coupon_mod.PromoCodeButton', function(require) {
    'use strict';

    const PosCoupon = require('pos_coupon.DiscountButton');
//    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

     const FEPosCoupon = (PosCoupon) =>
      class extends PosCoupon {
        constructor() {
            super(...arguments);
            // useListener('send-payment-adjust', this._sendPaymentAdjust);
        }

        async onClick() {
            const { confirmed, payload: code } = await this.showPopup('TextInputPopup', {
                title: this.env._t('Enter Promotion or Coupon Code'),
                startingValue: '',
            });
            if (confirmed && code !== '') {
                const order = this.env.pos.get_order();
                order.activate              Code(code);
            }
        }
    }
    PromoCodeButton.template = 'pos_coupon.PromoCodeButton';

    ProductScreen.addControlButton({
        component: PromoCodeButton,
        condition: function () {
            return this.env.pos.config.use_coupon_programs;
        },
    });

    Registries.Component.extend(PosCoupon, FEPosCoupon);

    return FEPosCoupon;
});