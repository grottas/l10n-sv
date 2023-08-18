# -*- coding: utf-8 -*-
from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError
from .amount_to_text_sv import to_word


class AccountMove(models.Model):
    _inherit = 'account.move'

    print_invoice = fields.Boolean('Factura Impresa', default=False, copy=False)
    amount_text = fields.Char(string=_('Monto en texto'),
                              store=True,
                              readonly=True,
                              compute='_amount_to_text',
                              tracking="2")


    @api.depends('amount_total')
    def _amount_to_text(self):
        for invoice in self:
            invoice.amount_text = to_word(invoice.amount_total)


    def action_invoice_digital_print(self):
        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Solo se pueden imprimir facturas."))
        self.filtered(lambda inv: not inv.is_move_sent).write({'is_move_sent': True})
        return self.env.ref('expertha_invoice_sv.report_invoice_digital').report_action(self)

    def action_invoice_print(self):
        """ Print the invoice and mark it as sent, so that we can see more
        easily the next step of the workflow
        """

        if any(not move.is_invoice(include_receipts=True) for move in self):
            raise UserError(_("Solo se pueden imprimir facturas."))
        self.filtered(lambda inv: not inv.is_move_sent).write({'is_move_sent': True})
        self.print_invoice = True
        report = self.tipo_documento_id.codigo
        if not self.tipo_documento_id:
            raise UserError(_("No se ha asignado un Tipo de Documento."))

        if self.tipo_documento_id:
            if report == 'CCF':
                return self.env.ref('expertha_invoice_sv.report_credito_fiscal').report_action(self)
            if report == 'Factura':
                return self.env.ref('expertha_invoice_sv.report_consumidor_final').report_action(self)
            if report == 'Exportacion':
                return self.env.ref('expertha_invoice_sv.report_exportacion').report_action(self)
            if report == 'Nota de Debito':
                return self.env.ref('expertha_invoice_sv.report_ndc').report_action(self)
            if report == 'anu':
                return self.env.ref('expertha_invoice_sv.report_anu').report_action(self)
            if report == 'axp':
                return self.env.ref('expertha_invoice_sv.report_axp').report_action(self)
            if report == 'suexcluido':
                return self.env.ref('expertha_invoice_sv.report_sujeto_excluido').report_action(self)

            return self.env.ref('account.account_invoices').report_action(self)


 #   def button_draft(self):
 #       return super(AccountMove, self).button_draft()
