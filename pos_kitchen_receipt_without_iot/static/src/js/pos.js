odoo.define('pos_kitchen_receipt_without_iot.pos_kitchen_receipt_without_iot', function (require) {
    const models = require('point_of_sale.models');
    const ReceiptScreen = require('point_of_sale.ReceiptScreen');
    const PosComponent = require('point_of_sale.PosComponent');
    const {useListener} = require('web.custom_hooks');
    const Registries = require('point_of_sale.Registries');
    const ProductScreen = require('point_of_sale.ProductScreen');
    let core = require('web.core');
    let QWeb = core.qweb;

    class WVPosKitchenReceiptButton extends PosComponent {
        constructor() {
            super(...arguments);
            useListener('click', this.onClick);
            this._currentOrder = this.env.pos.get_order();
            this._currentOrder.orderlines.on('change', this.render, this);
            this.env.pos.on('change:selectedOrder', this._updateCurrentOrder, this);
        }

        async onClick() {
            var self = this;
            var order = self.env.pos.get_order();
            if (order.hasChangesToPrint()) {
                order.printChanges2();
                order.saveChanges();
                self.showTempScreen('KitchenReceiptScreenWidget', {"report": order.receipt_val});

            }
        }

        get addedClasses() {
            if (!this._currentOrder) return {};
            const changes = this._currentOrder.hasChangesToPrint();
            const skipped = changes ? false : this._currentOrder.hasSkippedChanges();
            return {
                highlight: changes,
                altlight: skipped,
            };
        }

    }

    WVPosKitchenReceiptButton.template = 'WVPosKitchenReceiptButton';

    ProductScreen.addControlButton({
        component: WVPosKitchenReceiptButton,
        condition: function () {
            return this.env.pos.config.allow_kitchens_receipt;
        },
    });

    Registries.Component.add(WVPosKitchenReceiptButton);


    models.Order = models.Order.extend({
        printChanges2: function () {
            var printers = this.pos.printers;
            var receipt = "";
            var receiptList = [];
            for (var i = 0; i < printers.length; i++) {
                var changes = this.computeChanges(printers[i].config.product_categories_ids);
                if (changes['new'].length > 0 || changes['cancelled'].length > 0) {
                    receipt += QWeb.render('KitchenOrderChangeReceipt', {changes: changes, widget: this});
                    receiptList.push(QWeb.render('KitchenOrderChangeReceipt', {changes: changes, widget: this}));
                }
            }
            var order = this.pos.get_order();
            order.receipt_val = {'list': receiptList, 'normal': receipt};
        },
    });

    const KitchenReceiptScreenWidget = (ReceiptScreen) => {
        class KitchenReceiptScreenWidget extends ReceiptScreen {
            constructor() {
                super(...arguments);
                this.report = arguments[1].report.normal;
                this.reportList = arguments[1].report.list;
                this.len = arguments[1].report.list.length;
                this.config = this.env.pos.config;
            }

            mounted() {
                // override
                setTimeout(async () => await this.handleAutoPrint(), 0);
            }

            confirm() {
                this.props.resolve({confirmed: true, payload: null});
                this.trigger('close-temp-screen');
            }

            async printReceipt(index) {
                if (!this.config.use_multi_printer) {
                    await this._default_print();
                } else {
                    await this._print_by_ticket(this.reportList[index], index);
                }
            }

            async _default_print() {
                const isPrinted = await this._printReceipt();
                if (isPrinted && !this.env.pos.config.allow_kitchens_receipt) {
                    this.currentOrder._printed = true;
                }
            }

            async _print_by_ticket(receipt, index) {
                try {
                    printJS({
                        printable: 'ticket_container_' + index,
                        type: 'html',
                        targetStyles: ['*'],
                        css: '/web/assets/*.css',
                        scanStyles: true,
                        showModal: false,
                        documentTitle: ""
                    })
                } catch (err) {
                    await this.showPopup('ErrorPopup', {
                        title: this.env._t('Printing is not supported on some browsers'),
                        body: this.env._t(
                            'Printing is not supported on some browsers due to no default printing protocol ' +
                                'is available. It is possible to print your tickets by making use of an IoT Box.'
                        ),
                    });
                }
            };

        }

        KitchenReceiptScreenWidget.template = 'KitchenReceiptScreenWidget';
        return KitchenReceiptScreenWidget;
    };

    Registries.Component.addByExtending(KitchenReceiptScreenWidget, ReceiptScreen);

});
