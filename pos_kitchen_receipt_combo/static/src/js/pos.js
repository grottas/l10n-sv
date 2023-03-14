odoo.define('pos_kitchen_receipt_combo.pos_kitchen_receipt_combo', function (require) {
    const models = require('point_of_sale.models');

    models.Order = models.Order.extend({
        // The order_menu variable contains values for the combo.
        _change_order_line: function (resume, line) {
            let line_hash = line.get_line_diff_hash();
            let qty = Number(line.get_quantity());
            let note = line.get_note();
            let product_id = line.get_product().id;

            if (typeof resume[line_hash] === 'undefined') {
                resume[line_hash] = {
                    printed_line_id: line.printed_line_id,
                    qty: qty,
                    note: note,
                    product_id: product_id,
                    product_name_wrapped: line.generate_wrapped_product_name(),
                    order_menu: line.order_menu,
                };
            } else {
                resume[line_hash].qty += qty;
            }
            return resume;
        },
        _compute_change_current: function (found, add, rem, curr, old) {

            if (!found) {
                add.push({
                    'id': curr.product_id,
                    'name': this.pos.db.get_product_by_id(curr.product_id).display_name,
                    'name_wrapped': curr.product_name_wrapped,
                    'note': curr.note,
                    'qty': curr.qty,
                    'order_menu': curr.order_menu,
                });
            } else if (old.qty < curr.qty) {
                add.push({
                    'id': curr.product_id,
                    'name': this.pos.db.get_product_by_id(curr.product_id).display_name,
                    'name_wrapped': curr.product_name_wrapped,
                    'note': curr.note,
                    'qty': curr.qty - old.qty,
                    'order_menu': curr.order_menu,
                });
            } else if (old.qty > curr.qty) {
                rem.push({
                    'id': curr.product_id,
                    'name': this.pos.db.get_product_by_id(curr.product_id).display_name,
                    'name_wrapped': curr.product_name_wrapped,
                    'note': curr.note,
                    'qty': old.qty - curr.qty,
                    'order_menu': curr.order_menu,
                });
            }

            return {
                add: add,
                rem: rem,
            };
        },

        _compute_change_old: function (rem, old_2nd) {

            rem.push({
                'id': old_2nd.product_id,
                'name': this.pos.db.get_product_by_id(old_2nd.product_id).display_name,
                'name_wrapped': old_2nd.product_name_wrapped,
                'note': old_2nd.note,
                'qty': old_2nd.qty,
                'order_menu': old_2nd.order_menu,
            });

            return rem;
        },

    });

});
