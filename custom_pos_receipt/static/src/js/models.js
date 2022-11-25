odoo.define('custom_pos_receipt.models', function (require) {
 "use strict";

    var models = require('point_of_sale.models');

    models.load_fields('res.partner', ['dui', 'nit', 'nrc', 'website', 'property_account_position_id' ]);

    models.load_models({
        model: 'account.fiscal.position',
        fields: ['id','name'],
        loaded: function (self, fiscal) {
            self.fiscal=fiscal
        },
    });

    models.load_models({
        model: 'account.fiscal.position',
        fields: ['id','name'],
        loaded: function (self, fiscal) {
            self.fiscal=fiscal
        },
    });

//   var _super_order = models.Order.prototype;
//   exports.Order = Backbone.Model.extend({
//        initialize: function(attributes,options){
//            this.to_ticket_regalo = false;
//         },
//        set_ticket_regalo: function(to_ticket_regalo) {
//            this.assert_editable();
//            this.to_ticket_regalo = to_ticket_regalo;
//        },
//
//
//        is_to_ticket_regalo: function(){
//            return this.to_ticket_regalo;
//        },
//    });

    var _super_orderline = models.Orderline.prototype;
    models.Orderline = models.Orderline.extend({
         export_for_printing: function () {
            var res = _super_orderline.export_for_printing.apply(this, arguments);
            res.default_code = this.get_product().default_code;
            return res;
     },


    });

});
