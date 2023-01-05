odoo.define('pos_tip_percent.TipButton', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const ProductScreen = require('point_of_sale.ProductScreen');
    const { useListener } = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');

    class TipButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
        }
        async onClick() {
            var self = this;
            const { confirmed, payload } = await this.showPopup('NumberPopup',{
                title: this.env._t('Procentaje de Propina'),
                startingValue: this.env.pos.config.tip_pc,
                isInputSelected: true
            });
            if (confirmed) {
                const val = Math.round(Math.max(0,Math.min(100,parseFloat(payload))));
                await self.apply_tip(val);
            }
        }

        async apply_tip(tpc) {
            var order    = this.env.pos.get_order();
            var lines    = order.get_orderlines();
            var product  = this.env.pos.db.get_product_by_id(this.env.pos.config.tip_product_id[0]);
            var discount  = this.env.pos.db.get_product_by_id(this.env.pos.config.discount_product_id[0]);
            if (product === undefined) {
                await this.showPopup('ErrorPopup', {
                    title : this.env._t("No se encontró ningún producto con propina"),
                    body  : this.env._t("El producto de propina parece mal configurado. Asegúrese de que esté marcado como 'Se puede vender' y 'Disponible en el punto de venta'."),
                });
                return;
            }

            var discount_value = 0;
            for (const line of lines) {
                if (line.get_product() === discount) {
                   discount_value = line.get_price_with_tax();
                }
            }

            // Remove existing tips
            for (const line of lines) {
                if (line.get_product() === product) {
                    order.remove_orderline(line);
                }
            }


////            obtener los nombres de las lineas del pedido con sus precios
//            var lineas = order.get_orderlines();
//            for (const linea of lineas) {
//                console.log(linea.get_product().display_name);
//                console.log(linea.get_price_with_tax());
//            }



            // Add tip
            // We add the price as manually set to avoid recomputation when changing customer.
            var base_to_tip = order.get_total_without_tax();
            if (product.taxes_id.length){
                var first_tax = this.env.pos.taxes_by_id[product.taxes_id[0]];
                if (first_tax.price_include) {
                    base_to_tip = order.get_total_with_tax();
                }
            }
            var tip = tpc / 100.0 * (base_to_tip + (base_to_tip * 0.13) - discount_value) ;

            if( tip > 0 ){
                await order.add_product(product, {
                    price: tip,
                    lst_price: tip,
                    extras: {
                        price_manually_set: true,
                    },
                });
            }
        }
    }
    TipButton.template = 'TipButton';

    ProductScreen.addControlButton({
        component: TipButton,
        condition: function() {
            return this.env.pos.config.module_pos_tip_percent && this.env.pos.config.tip_product_id;
        },
    });

    Registries.Component.add(TipButton);

    return TipButton;
});
