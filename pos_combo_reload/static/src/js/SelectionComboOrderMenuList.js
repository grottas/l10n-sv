odoo.define('point_of_sale.SelectionComboOrderMenuList', function(require) {
    'use strict';

    const PosComponent = require('point_of_sale.PosComponent');
    const Registries = require('point_of_sale.Registries');

    class SelectionComboOrderMenuList extends PosComponent {}
    SelectionComboOrderMenuList.template = 'SelectionComboOrderMenuList';

    Registries.Component.add(SelectionComboOrderMenuList);

    return SelectionComboOrderMenuList;
});