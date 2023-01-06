odoo.define('point_of_sale.ProductSelectionPopup', function(require) {
    'use strict';

    const { useState, useSubEnv } = owl.hooks;
    const AbstractAwaitablePopup = require('point_of_sale.AbstractAwaitablePopup');
    const Registries = require('point_of_sale.Registries');
    const { useListener } = require('web.custom_hooks');

    class ProductSelectionPopup extends AbstractAwaitablePopup {
        constructor() {
            super(...arguments);
            useListener('click-combo-product', this._clickProduct);
            useListener('remove-combo-product', this._removeProduct);
            useListener('switch-category', this._switchCategory);
            this.data = this.props.data;
            this.main_product = this.props.main_product;
            this.main_product_name = this.props.main_product_name;
            this.main_product_price = this.props.main_product_price;
            this.pricelist = this.currentOrder.pricelist;
            this.popup = useState({ isRemoved: false});
            useSubEnv({ order_menu: this.props.order_menu || [] });
            this.is_editable = this.props.is_editable || false;
            this.selected_orderline = this.props.selected_orderline || false;
            if(this.is_editable) {
                this.selected_order_menu = JSON.parse(JSON.stringify(this.selected_orderline.order_menu));
            }
        }
        mounted() {
            this.env.pos.on('change:SelectionSelectedToppingId', this.render, this);
        }
        willUnmount() {
            this.env.pos.off('change:SelectionSelectedToppingId', null, this);
        }
        get SelectionSelectedToppingId() {
            return this.env.pos.get('SelectionSelectedToppingId');
        }
        get productsToDisplay() {
            const topping_data = this.env.pos.topping_item_by_id[this.SelectionSelectedToppingId]
            var list = [];
            if (topping_data) {
                var product_ids = topping_data.product_ids;
                if (product_ids) {
                    for (var i = 0; i < product_ids.length; i++) {
                        list.push(this.env.pos.db.get_product_by_id(product_ids[i]));
                    }
                }
            }
            return list;
        }
        get OrderMenuToDisplay() {
            return this.env.order_menu;
        }
        get TotalPriceToDisplay() {
            var total_price = 0.0;
            _.each(this.env.order_menu, function(order){
                _.each(order.products, function(product){
                    total_price += product.price;
                });
            });
            return total_price.toFixed(2);
        }
        async _clickProduct(event) {
            if (this.popup.isRemoved) {
                this.popup.isRemoved = false;
                return
            }
            const topping_data = this.env.pos.topping_item_by_id[this.SelectionSelectedToppingId];
            if (!topping_data) return;
            const category = topping_data.product_categ_id[0];
            const product = event.detail.product;
            const description = topping_data.description;
            const multi_selection = topping_data.multi_selection;
            var allow = true;
            var order_menu = this.props.order_menu || [];

            if(!topping_data.no_of_items && multi_selection){
                return
            }

            var item = _.where(order_menu, {'toppingId': topping_data.id})
            if(item && item.length > 0){
                item = item[0];
                var item_products = item.products;

                if(item_products.length > 0 && multi_selection == false){
                    alert("You can select only one item.");
                    allow = false;
                    return
                } else {
                    var total_items = 0;
                    _.each(item_products, function(product){
                        total_items += product.qty;
                    });
                    if(item_products.length > 0 && total_items >= topping_data.no_of_items){
                        alert("You can only select "+ topping_data.no_of_items + " item from "+ topping_data.description);
                        return
                    }
                }
            }

            for(var i=0; i < order_menu.length; i++){
                if(topping_data.id == order_menu[i].toppingId){
                    var exist_product = _.find(order_menu[i].products, function(p) { return p.product_id === product.id});
                    if(exist_product) {
                        exist_product['qty'] = exist_product.qty + 1;
                        exist_product['price'] = exist_product.qty * product.get_price(this.pricelist,1);
                        allow = false;
                    } else {
                        order_menu[i].products.push({
                                'product_id': product.id,
                                'product_name': product.display_name.replace('(<p><br></p>)',''),
                                'price': product.get_price(this.pricelist,1),
                                'qty': 1
                            });
                    }
                    allow = false;
                }
                if(order_menu[i].products.length <= 0){
                    order_menu.splice(i, 1);
                }
            }
            if(allow){
                order_menu.push({
                        'toppingId': topping_data.id,
                        'categoryName': description,
                        'include_price': this.props.include_price,
                        'products': [{
                            'product_id':product.id,
                            'product_name': product.display_name,
                            'price': product.get_price(this.pricelist, 1),
                            'qty': 1
                        }]
                    });
            }
            this.env.order_menu = order_menu;
            this.render();
        }
        async _removeProduct(event) {
            this.popup.isRemoved = true;

            const topping_data = this.env.pos.topping_item_by_id[this.SelectionSelectedToppingId];
            const product = event.detail.product;

            _.each(this.env.order_menu, function(order_menu){
                if(topping_data.id == order_menu.toppingId){
                    order_menu['products'] = _.reject(order_menu.products, function(p){ return p.product_id === product.id });
                }
            });
            this.env.order_menu = _.reject(this.env.order_menu, function(order_menu){ return order_menu.products < 1});
        }
        get currentOrder() {
            return this.env.pos.get_order();
        }
        update_order_line(product, total_price) {
            if(this.is_editable) {
                this.selected_orderline.set_unit_price(product.get_price(this.pricelist,1) + total_price);
                this.currentOrder.select_orderline(this.selected_orderline);
            } else {
                this.currentOrder.add_product(product, {'price': product.get_price(this.pricelist, 1) + total_price});
                this.currentOrder.selected_orderline.price_manually_set = true;
            }
        }
        async confirm() {
            const topping_data = this.env.pos.topping_item_by_id[this.SelectionSelectedToppingId];
            if (!topping_data) return;
            const multi_selection = topping_data.multi_selection;
            const self = this;

            var own_data = [];
            var selection = [];
            var total_price = 0.0;
            var required_sub_item = false;

            for(var i=0; i < this.data.length; i++){
                if (this.data[i].no_of_min_items != 0){
                    required_sub_item = true;
                    break;
                }
            }
            if (this.env.order_menu.length == 0 && required_sub_item) {
                alert("You can not confirm without select any item of min qty > 0 lines!");
                return
            } else {
                for(var i=0; i < this.data.length; i++){
                    if (this.data[i].no_of_min_items != 0){
                        var min_items = 0;
                        for(var j=0; j < this.env.order_menu.length; j++){
                            _.each(this.env.order_menu[j]['products'], function(product){
                                if (self.env.order_menu[j]['toppingId'] == self.data[i]['id']) {
                                    min_items += product.qty;
                                }
                            });
                        }
                        if(this.data[i].no_of_min_items > min_items){
                            alert("You Must Have to Select " + this.data[i].no_of_min_items + " item from " + this.data[i].category);
                            return
                        }
                    }
                }
            }

            for(var i=0; i < this.env.order_menu.length; i++){
                for(var j=0; j < this.env.order_menu[i].products.length; j++) {
                    var product_id = this.env.order_menu[i].products[j].product_id;
                    own_data.push({
                        "product_id": this.env.pos.db.get_product_by_id(parseInt(product_id)),
                        'qty': this.env.order_menu[i].products[j].qty,
                        'price': this.env.order_menu[i].products[j].price
                    });
                    if (this.env.order_menu[i].include_price) {
                        total_price += this.env.order_menu[i].products[j].price;
                    }
                }
            }
            var product = this.env.pos.db.get_product_by_id(this.main_product);

            this.update_order_line(product, total_price);

            this.currentOrder.selected_orderline.set_own_data(own_data);
            this.currentOrder.selected_orderline.set_order_menu(this.env.order_menu);
            this.currentOrder.selected_orderline.set_selected();
            super.confirm();
        }
        _switchCategory(event) {
            this.env.pos.set('SelectionSelectedToppingId', event.detail);
        }
        cancel() {
            if(this.is_editable) {
                this.selected_orderline.order_menu = this.selected_order_menu;
            }
            super.cancel();
        }
    }

    ProductSelectionPopup.template = 'ProductSelectionPopup';
    ProductSelectionPopup.defaultProps = {
        confirmText: 'Confirm',
        cancelText: 'Cancel',
    };

    Registries.Component.add(ProductSelectionPopup);

    return ProductSelectionPopup;
});
