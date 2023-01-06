odoo.define('pos_combo_reload.PosSelectionCombo', function (require) {
"use strict";

    const ProductScreen = require('point_of_sale.ProductScreen');
    const Registries = require('point_of_sale.Registries');
    const Models = require('point_of_sale.models');

    Models.load_fields("product.product",['is_selection_combo', 'product_topping_ids', 'include_price']);

    Models.load_models({
        model: 'product.selection.topping',
        fields: ['id', 'product_categ_id', 'multi_selection', 'product_ids', 'no_of_min_items', 'no_of_items', 'description'],
        loaded: function(self, result){
            self.topping_item_by_id = {};
            _.each(result, function(topping_item){
                self.topping_item_by_id[topping_item.id] = topping_item;
            })
        },
    });

    const SelectionComboProductScreen = (ProductScreen) =>
        class extends ProductScreen {
            async _clickProduct(event) {
                const self = this;
                const product = event.detail;
                var default_product_topping_id = false;
                if(product.is_selection_combo) {
                    const data = [];
                    _.each(product.product_topping_ids, function(product_topping_id){
                        const products = [];
                        const selected_product = self.env.pos.topping_item_by_id[product_topping_id];
                        _.each(selected_product.product_ids, function(product_id){
                            const item = self.env.pos.db.get_product_by_id(product_id);
                            if(item) products.push(item);
                        });
                        if (!default_product_topping_id) default_product_topping_id = selected_product.id
                        data.push({
                            'id': selected_product.id,
                            'category': selected_product.description,
                            'categ_id': selected_product.product_categ_id[0],
                            'products': products || [],
                            'multi_selection': selected_product.multi_selection,
                            'no_of_items': selected_product.no_of_items,
                            'no_of_min_items': selected_product.no_of_min_items,
                            'qty': selected_product.product_quantity,
                        });
                    });
                    this.env.pos.set('SelectionSelectedToppingId', default_product_topping_id);
                    await this.showPopup('ProductSelectionPopup', {
                        'data': data,
                        'main_product': product.id,
                        'main_product_name': product.display_name,
                        'main_product_price': product.lst_price,
                        'include_price': product.include_price,
                        'order_menu': []
                    });
                } else {
                    super._clickProduct(event);
                }
            }
        };

    Registries.Component.extend(ProductScreen, SelectionComboProductScreen);


    var _super_order_line = Models.Orderline.prototype;
    Models.Orderline = Models.Orderline.extend({
        init_from_JSON: function(json) {
            var self = this;
            _super_order_line.init_from_JSON.apply(this,arguments);
            this.own_data = this.own_data || json.own_data || [];
            this.order_menu = this.order_menu || json.order_menu || [];
            if (this.own_data && this.own_data.product_id == undefined) {
                var own_data = [];
                _.each(this.order_menu, function(order){
                    var products = [];
                    _.each(order.products, function(product){
                        own_data.push({
                            "product_id": self.pos.db.get_product_by_id(parseInt(product.product_id)),
                            'qty': product.qty,
                            'price': product.price
                        });
                    });
                });
                this.own_data = own_data;
            }
        },
        set_own_data: function(own_data){
            this.own_data = own_data;
        },
        get_own_data: function(){
            return this.own_data;
        },
        set_order_menu: function(order_menu){
            this.order_menu = order_menu;
        },
        get_order_menu: function(){
            return this.order_menu;
        },
        export_as_JSON: function(){
            var self = this;
            var own_line = [];
            var total_price = 0.0;
            var json = _super_order_line.export_as_JSON.call(this,arguments);
            if(self.product.is_selection_combo && self.own_data) {
                _.each(self.own_data, function(item) {
                    var sub_total = 0.0;
                    let uom_id = item.product_id.uom_id[0]
                    var full_name = item.product_id.display_name;
                    if (item.product_id.description) {
                        full_name += ` (${item.product_id.description})`;
                    }
                    own_line.push([0, 0, {
                        'product_id': item.product_id.id,
                        'full_product_name': full_name.replace('(<p><br></p>)',''),
                        'qty': self.get_quantity() * item.qty,'price':item.price,
                        'price_subtotal': sub_total,
                        'price_subtotal_incl': sub_total,
                        'product_uom': self.pos.units_by_id[uom_id],
                    }]);
                    total_price += item.price;
                });
            }
            if (this.product.is_selection_combo) {
                json.price_unit = total_price;
            }
            json.price_unit = this.price;
            json.is_selection_combo = this.product.is_selection_combo;
            json.own_line = this.product.is_selection_combo ? own_line : [];
            json.own_data = this.own_data ? this.own_data : [];
            json.order_menu = this.order_menu ? this.order_menu : [];
            return json;
        },
        export_for_printing: function(){
            var json = _super_order_line.export_for_printing.call(this,arguments);
            json['order_menu'] = this.order_menu;
            json['is_selection_combo_product'] = this.get_product().is_selection_combo;
            return json;
        },
    });

    return SelectionComboProductScreen;
});
