odoo.define('pos_combo_reload_restaurant.PosSelectionComboRest', function (require) {
    "use strict";

    const Models = require('point_of_sale.models');

    var _super_orderline = Models.Orderline.prototype;
    Models.Orderline = Models.Orderline.extend({

        can_be_merged_with: function (orderline) {
            // stops the merge of the lines that have property is_selection_combo
            if (orderline.get_product().is_selection_combo) {
                return false;
            } else {
                return _super_orderline.can_be_merged_with.apply(this,arguments);
            }
        },
    });

});

