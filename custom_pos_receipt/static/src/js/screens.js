odoo.define('custom_pos_receipt.screens', function (require) {
"use strict";

  var PaymentScreen = require('point_of_sale.PaymentScreen');
  var core = require('web.core');
  var QWeb = core.qweb;
  var _t = core._t;
  var rpc = require('web.rpc');
  const { useListener } = require('web.custom_hooks');
  const Registries = require('point_of_sale.Registries');

  const FEPaymentScreen = (PaymentScreen) =>
      class extends PaymentScreen {
        constructor() {
            super(...arguments);
            // useListener('send-payment-adjust', this._sendPaymentAdjust);
        }

        async _finalizeValidation() {
            var self = this;
            if ((this.currentOrder.is_paid_with_cash() || this.currentOrder.get_change()) && this.env.pos.config.iface_cashdrawer) {
                this.env.pos.proxy.printer.open_cashbox();
            }
            var domain = [['pos_reference', '=', this.currentOrder['name']]]
            var fields = ['name'];

            this.currentOrder.initialize_validation_date();
            this.currentOrder.finalized = true;

            let syncedOrderBackendIds = [];

            try {
                if (this.currentOrder.is_to_invoice()) {
                    syncedOrderBackendIds = await this.env.pos.push_and_invoice_order(
                        this.currentOrder
                    );
                } else {
                    syncedOrderBackendIds = await this.env.pos.push_single_order(this.currentOrder);
                }
            } catch (error) {
                if (error instanceof Error) {
                    throw error;
                } else {
                    await this._handlePushOrderError(error);
                }
            }
            if (syncedOrderBackendIds.length && this.currentOrder.wait_for_push_order()) {
                const result = await this._postPushOrderResolve(
                    this.currentOrder,
                    syncedOrderBackendIds
                );
                if (!result) {
                    await this.showPopup('ErrorPopup', {
                        title: 'Error: no internet connection.',
                        body: error,
                    });
                }
            }
            if (!this.currentOrder.is_to_invoice()) {
					this.rpc({
						model: 'pos.order',
						method: 'search_read',
						args: [domain, fields],
					})
					.then(function (output) {
						console.log( self.currentOrder  )
						self.currentOrder.name_secuencia = output[0]['name']

						self.showScreen(self.nextScreen);
					})

				}
//            this.showScreen(this.nextScreen);
            else{
                this.showScreen(this.nextScreen);
            }

            // If we succeeded in syncing the current order, and
            // there are still other orders that are left unsynced,
            // we ask the user if he is willing to wait and sync them.
            if (syncedOrderBackendIds.length && this.env.pos.db.get_orders().length) {
                const { confirmed } = await this.showPopup('ConfirmPopup', {
                    title: this.env._t('Remaining unsynced orders'),
                    body: this.env._t(
                        'There are unsynced orders. Do you want to sync these orders?'
                    ),
                });
                if (confirmed) {
                    // NOTE: Not yet sure if this should be awaited or not.
                    // If awaited, some operations like changing screen
                    // might not work.
                    this.env.pos.push_orders();
                }
            }
        }

       is_to_ticket_regalo(){
            return false;
      	}

        click_ticket_regalo(){
            alert('QUE DAS?')
      		this.render();
      	}


      }
      Registries.Component.extend(PaymentScreen, FEPaymentScreen);

      return FEPaymentScreen;
});

