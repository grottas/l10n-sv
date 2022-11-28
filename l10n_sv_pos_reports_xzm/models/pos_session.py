from odoo import fields, models, api
from datetime import datetime
# import datetime
import calendar

from odoo.exceptions import AccessError, UserError, ValidationError
class PosSession(models.Model):
    _inherit = 'pos.session'

    x_cortez = fields.Boolean(string='Aplicar Corte X')
    cortex_id = fields.Many2one('corte.x', string='Corte X')
    cortez_id = fields.Many2one('corte.z', related='cortex_id.cortez_id', readonly=True, string='Corte Z')

    def generar_cortex(self):
        fecha = datetime.strftime(self.start_at, '%Y-%m-%d')
        cortez = self.env['corte.z'].search([('fecha', '=', fecha)])
        if len(cortez) == 0:
            if self.state == 'closed':
                if not self.cortex_id:
                    # fecha = datetime.strftime(self.start_at, '%Y-%m-%d')
                    # fecha = '29-09-2022'
                    orders = self.env['pos.order'].search([('id', '=', self.order_ids.ids)])
                    invoice_fac = self.env['account.move'].search([('invoice_date', '=', fecha), ('tipo_documento_id.name', '=', 'Factura'), ('state', '=', 'posted'), ('cortex_id', '=', False)])
                    invoice_ccf = self.env['account.move'].search([('invoice_date', '=', fecha), ('tipo_documento_id.name', '=', 'CCF'), ('state', '=', 'posted'), ('cortex_id', '=', False)])
                    invoice_ndc= self.env['account.move'].search([('invoice_date', '=', fecha), ('tipo_documento_id.name', '=', 'Nota de Credito'), ('state', '=', 'posted'), ('cortex_id', '=', False)])
                    invoice_contado = self.env['account.move'].search([('invoice_date', '=', fecha), ('invoice_payment_term_id', '=', 'Pago inmediato'), ('cortex_id', '=', False)])
                    invoice_contado_pos = self.env['account.move'].search([('invoice_date', '=', fecha), ('invoice_payment_term_id', '=', fecha), ('cortex_id', '=', False)])
                    invoice_credito = self.env['account.move'].search([('invoice_date', '=', fecha), ('invoice_payment_term_id', '!=', 'Pago inmediato'), ('cortex_id', '=', False)])

                    #FACTURA
                    fac_grav_total = 0.00
                    fac_exen_total = 0.00
                    fac_total_nosuj = 0.00

                    if len(invoice_fac) > 0:
                        fact_total_num_desde = invoice_fac[-1].doc_numero
                        fact_total_num_hasta = invoice_fac[0].doc_numero
                    else:
                        fact_total_num_desde = 0
                        fact_total_num_hasta = 0

                    #TK
                    pos_grav_total = 0.00
                    pos_exen_total = 0.00
                    pos_total_nosuj = 0.00
                    if len(orders) > 0:
                        tk_total_num_desde = orders[-1].name
                        tk_total_num_hasta = orders[0].name
                    else:
                        tk_total_num_desde = 0
                        tk_total_num_hasta = 0

                    # CCF
                    ccf_grav_total = 0.00
                    ccf_exen_total = 0.00
                    ccf_total_nosuj = 0.00
                    if len(invoice_ccf) > 0:
                        ccf_total_num_desde = invoice_ccf[-1].doc_numero
                        ccf_total_num_hasta = invoice_ccf[0].doc_numero
                    else:
                        ccf_total_num_desde = 0
                        ccf_total_num_hasta = 0

                    # NDC
                    ndc_grav_total = 0.00
                    ndc_exen_total = 0.00
                    ndc_total_nosuj = 0.00
                    if len(invoice_ndc) > 0:
                        ndc_total_num_desde = invoice_ndc[-1].doc_numero
                        ndc_total_num_hasta = invoice_ndc[0].doc_numero
                    else:
                        ndc_total_num_desde = 0
                        ndc_total_num_hasta = 0

                    #CREDITO O CONTADO
                    invoice_contado_set = 0.00
                    invoice_contado_pos_set = 0.00
                    invoice_credito_set = 0.00

                    for pos_orders in orders:
                        if not pos_orders.account_move:
                            for lines in pos_orders.lines:
                                if lines.tax_ids_after_fiscal_position.name == 'IVA Consumidor.':
                                    pos_grav_total += lines.price_subtotal_incl
                                if lines.tax_ids_after_fiscal_position.name == 'IVA Incluido':
                                    pos_grav_total += lines.price_subtotal_incl
                                if lines.tax_ids_after_fiscal_position.name == 'Exento venta':
                                    pos_exen_total += lines.price_subtotal_incl
                                if lines.tax_ids_after_fiscal_position.name == 'No Sujeto Venta':
                                    pos_total_nosuj += lines.price_subtotal_incl

                    # SUMATORIA DE CONSUMIDOR FINAL
                    for invoice_orders_fac in invoice_fac:
                        for lines in invoice_orders_fac.invoice_line_ids:
                            if lines.tax_ids.name == 'IVA Consumidor.':
                                fac_grav_total += lines.price_total
                            if lines.tax_ids.name == 'IVA Incluido':
                                fac_grav_total += lines.price_total
                            if lines.tax_ids.name == 'Exento venta':
                                fac_exen_total += lines.price_total
                            if lines.tax_ids.name == 'No Sujeto Venta':
                                fac_total_nosuj += lines.price_total

                    #SUMATORIA DE CREDITOS FISCALES
                    for invoice_orders_ccf in invoice_ccf:
                        for lines in invoice_orders_ccf.invoice_line_ids:
                            if lines.tax_ids.name == 'IVA Contribuyente.':
                                ccf_grav_total += lines.price_total
                            if lines.tax_ids.name == 'Exento venta':
                                ccf_exen_total += lines.price_total
                            if lines.tax_ids.name == 'No Sujeto Venta':
                                ccf_total_nosuj += lines.price_total


                    #SUMATORIA DE NOTA DE CREDITO
                    for invoice_orders_ndc in invoice_ndc:
                        for lines in invoice_orders_ndc.invoice_line_ids:
                            if lines.tax_ids.name == 'IVA Consumidor.':
                                ndc_grav_total += lines.price_total
                            if lines.tax_ids.name == 'IVA Contribuyente.':
                                ndc_grav_total += lines.price_total
                            if lines.tax_ids.name == 'Exento venta':
                                ndc_exen_total += lines.price_total
                            if lines.tax_ids.name == 'No Sujeto Venta':
                                ndc_total_nosuj += lines.price_total


                    #SUMATORIA DE CONTADO Y CREDITO
                    for invoice_orders_contado in invoice_contado:
                        invoice_contado_set += invoice_orders_contado.amount_total
                    for invoice_orders_contado in invoice_contado_pos:
                        invoice_contado_pos_set += invoice_orders_contado.amount_total
                    for invoice_orders_credito in invoice_credito:
                        invoice_credito_set += invoice_orders_credito.amount_total

                    cortex = self.env['corte.x']
                    cortex_id = cortex.create({
                        'fecha': self.start_at,
                        'fecha_impresion': datetime.now(),
                        'fact_total_num_desde': fact_total_num_desde,
                        'fact_total_num_hasta': fact_total_num_hasta,
                        'fact_vent_grav': fac_grav_total,
                        'fact_vent_exen': fac_exen_total,
                        'fact_vent_nosj': fac_total_nosuj,
                        'fact_total': (fac_grav_total + fac_exen_total + fac_total_nosuj),

                        'ccf_total_num_desde': ccf_total_num_desde,
                        'ccf_total_num_hasta': ccf_total_num_hasta,
                        'ccf_vent_grav': ccf_grav_total,
                        'ccf_vent_exen': ccf_exen_total,
                        'ccf_vent_nosj': ccf_total_nosuj,
                        'ccf_total': (ccf_grav_total + ccf_exen_total + ccf_total_nosuj),

                        'tk_total_num_desde': tk_total_num_desde,
                        'tk_total_num_hasta': tk_total_num_hasta,
                        'tk_vent_grav': pos_grav_total,
                        'tk_vent_exen': pos_exen_total,
                        'tk_vent_nosj': pos_total_nosuj,
                        'tk_total': (pos_grav_total + pos_exen_total + pos_total_nosuj),

                        'ndc_total_num_desde': ndc_total_num_desde,
                        'ndc_total_num_hasta': ndc_total_num_hasta,
                        'ndc_vent_grav': ndc_grav_total,
                        'ndc_vent_exen': ndc_exen_total,
                        'ndc_vent_nosj': ndc_total_nosuj,
                        'ndc_total': (ndc_grav_total + ndc_exen_total + ndc_total_nosuj),


                        'total_contado': (invoice_contado_set + invoice_contado_pos_set + pos_grav_total + pos_exen_total + pos_total_nosuj),
                        'total_credito': invoice_credito_set,
                        'pos_sesion_id': self.id,
                        'company_id': self.company_id.id
                    })
                    invoice_cortex = self.env['account.move'].search([('invoice_date', '=', fecha)])
                    for invoice_cortex_update in invoice_cortex:
                        if not invoice_cortex_update.cortex_id:
                            invoice_cortex_update.write({'cortex_id': cortex_id.id})
                    for orders_cortex in self.order_ids:
                        if not orders_cortex.cortex_id:
                            orders_cortex.write({'cortex_id': cortex_id.id})
                    self.cortex_id = cortex_id.id
                else:
                    raise UserError('Ya existe un Corte X para esta sesion.')
            else:
                raise UserError('La sesion debe estar cerrada y contabilizada.')
        else:
            raise UserError('Existe un corte Z en este dia, no puede hacer un corte X.')

    def generar_cortez(self):
        fecha = datetime.strftime(self.start_at, '%Y-%m-%d')
        cortexvalidation = self.env['corte.x'].search([('fecha', '=', fecha)])
        if len(cortexvalidation) == 0:
            raise UserError('No existe ningun Corte X en este dia.')
        session_pos = self.env['pos.session'].search([('start_at', '=', fecha)])
        cortez = self.env['corte.z'].search([('fecha', '=', fecha)])

        if len(cortez) > 0:
            raise UserError('Ya existe un Corte Z en este dia.')

        else:
            cortex = self.env['corte.x'].search([('fecha', '=', fecha)])
            for verify_session in session_pos:
                if not verify_session.state == 'closed':
                    raise UserError('La sesion del POS %s no esta cerrada.', verify_session.name)
                if not verify_session.cortex_id:
                    raise UserError('La sesion del POS %s no tiene un Corte X.', verify_session.name)
            # FAC
            z_fact_vent_grav = 0.00
            z_fact_vent_exen = 0.00
            z_fact_vent_nosj = 0.00
            z_fact_total = 0.00
            z_fact_total_num_desde = 0
            z_fact_total_num_hasta = 0

            # CCF
            z_ccf_vent_grav = 0.00
            z_ccf_vent_exen = 0.00
            z_ccf_vent_nosj = 0.00
            z_ccf_total = 0.00
            z_ccf_total_num_desde = 0
            z_ccf_total_num_hasta = 0

            # TK
            z_tk_vent_grav = 0.00
            z_tk_vent_exen = 0.00
            z_tk_vent_nosj = 0.00
            z_tk_total = 0.00
            z_tk_total_num_desde = 0
            z_tk_total_num_hasta = 0

            # TK
            z_ndc_vent_grav = 0.00
            z_ndc_vent_exen = 0.00
            z_ndc_vent_nosj = 0.00
            z_ndc_total = 0.00
            z_ndc_total_num_desde = 0
            z_ndc_total_num_hasta = 0

            z_total_credito = 0.00
            z_total_contado = 0.00


            if len(cortex) > 0:
                for lines in cortex:
                    # FAC
                    z_fact_vent_grav += lines.fact_vent_grav
                    z_fact_vent_exen += lines.fact_vent_exen
                    z_fact_vent_nosj += lines.fact_vent_nosj
                    z_fact_total += lines.fact_total
                    z_fact_total_num_desde = cortex[-1].fact_total_num_desde
                    if len(cortex) > 1:
                        if cortex[0].fact_total_num_hasta == '0':
                            z_fact_total_num_hasta = cortex[-1].fact_total_num_hasta
                    else:
                        z_fact_total_num_hasta = cortex[0].fact_total_num_hasta

                    # CCF
                    z_ccf_vent_grav += lines.ccf_vent_grav
                    z_ccf_vent_exen += lines.ccf_vent_exen
                    z_ccf_vent_nosj += lines.ccf_vent_nosj
                    z_ccf_total += lines.ccf_total
                    z_ccf_total_num_desde = cortex[-1].ccf_total_num_desde
                    if len(cortex) > 1:
                        if cortex[0].ccf_total_num_hasta == '0':
                            z_ccf_total_num_hasta = cortex[-1].ccf_total_num_hasta
                    else:
                        z_ccf_total_num_hasta = cortex[0].ccf_total_num_hasta


                    # TK
                    z_tk_vent_grav += lines.tk_vent_grav
                    z_tk_vent_exen += lines.tk_vent_exen
                    z_tk_vent_nosj += lines.tk_vent_nosj
                    z_tk_total += lines.tk_total
                    for desde in reversed(cortex):
                        if z_tk_total_num_desde == 0:
                            if desde.tk_total_num_desde != '0':
                                z_tk_total_num_desde = desde.tk_total_num_desde
                    for hasta in cortex:
                        if z_tk_total_num_hasta == 0:
                            if hasta.tk_total_num_hasta != '0':
                                z_tk_total_num_hasta = hasta.tk_total_num_hasta

                    # NDC
                    z_ndc_vent_grav += lines.ndc_vent_grav
                    z_ndc_vent_exen += lines.ndc_vent_exen
                    z_ndc_vent_nosj += lines.ndc_vent_nosj
                    z_ndc_total += lines.ndc_total
                    if len(cortex) > 1:
                        z_ndc_total_num_desde = cortex[-1].ndc_total_num_desde
                        if cortex[0].ndc_total_num_hasta == '0':
                            z_ccf_total_num_hasta = cortex[-1].ndc_total_num_hasta
                    else:
                        z_ndc_total_num_hasta = cortex[0].ndc_total_num_hasta


                    z_total_credito += lines.total_credito
                    z_total_contado += lines.total_contado

            cortez = self.env['corte.z']
            cortez_id = cortez.create({
                'fecha': self.start_at,
                'fecha_impresion': datetime.now(),
                'fact_total_num_desde': z_fact_total_num_desde,
                'fact_total_num_hasta': z_fact_total_num_hasta,
                'fact_vent_grav': z_fact_vent_grav,
                'fact_vent_exen': z_fact_vent_exen,
                'fact_vent_nosj': z_fact_vent_nosj,
                'fact_total': z_fact_total,
                'ccf_total_num_desde': z_ccf_total_num_desde,
                'ccf_total_num_hasta': z_ccf_total_num_hasta,
                'ccf_vent_grav': z_ccf_vent_grav,
                'ccf_vent_exen': z_ccf_vent_exen,
                'ccf_vent_nosj': z_ccf_vent_nosj,
                'ccf_total': z_ccf_total,


                'tk_total_num_desde': z_tk_total_num_desde,
                'tk_total_num_hasta': z_tk_total_num_hasta,
                'tk_vent_grav': z_tk_vent_grav,
                'tk_vent_exen': z_tk_vent_exen,
                'tk_vent_nosj': z_tk_vent_nosj,

                'ndc_total_num_desde': z_ndc_total_num_desde,
                'ndc_total_num_hasta': z_ndc_total_num_hasta,
                'ndc_vent_grav': z_ndc_vent_grav,
                'ndc_vent_exen': z_ndc_vent_exen,
                'ndc_vent_nosj': z_ndc_vent_nosj,

                'tk_total': z_tk_total,
                'total_contado': z_total_contado,
                'total_credito': z_total_credito,
                'company_id': self.company_id.id
            })

            if len(cortex) > 0:
                for lines in cortex:
                    lines.cortez_id = cortez_id.id



        return True

    def generar_cortezm(self):

        today = datetime.now()

        InicioMes = "%s-%s-01" % (today.year, today.month)
        FinMes = "%s-%s-%s" % (today.year, today.month, calendar.monthrange(today.year - 1, today.month - 1)[1])


        fecha = datetime.strftime(self.start_at, '%Y-%m-%d')
        session_pos = self.env['pos.session'].search([('start_at', '=', fecha)])
        # cortezm = self.env['corte.zm'].search([('fecha', '=', fecha)])

        cortezm = self.env['corte.zm'].search([('fecha', '>=', InicioMes), ('fecha', '<=', FinMes)])

        if len(cortezm) > 0:
            raise UserError('Ya existe un Corte ZM en este mes.')

        else:
            cortez = self.env['corte.z'].search([('fecha', '>=', InicioMes), ('fecha', '<=', FinMes)])
            for verify_session in session_pos:
                if not verify_session.state == 'closed':
                    raise UserError('La sesion del POS %s no esta cerrada.', verify_session.name)
                if not verify_session.cortex_id:
                    raise UserError('La sesion del POS %s no tiene un Corte X.', verify_session.name)
            # FAC
            z_fact_vent_grav = 0.00
            z_fact_vent_exen = 0.00
            z_fact_vent_nosj = 0.00
            z_fact_total = 0.00
            z_fact_total_num_desde = 0
            z_fact_total_num_hasta = 0

            # CCF
            z_ccf_vent_grav = 0.00
            z_ccf_vent_exen = 0.00
            z_ccf_vent_nosj = 0.00
            z_ccf_total = 0.00
            z_ccf_total_num_desde = 0
            z_ccf_total_num_hasta = 0

            # TK
            z_tk_vent_grav = 0.00
            z_tk_vent_exen = 0.00
            z_tk_vent_nosj = 0.00
            z_tk_total = 0.00
            z_tk_total_num_desde = 0
            z_tk_total_num_hasta = 0


            # ND
            z_ndc_vent_grav = 0.00
            z_ndc_vent_exen = 0.00
            z_ndc_vent_nosj = 0.00
            z_ndc_total = 0.00
            z_ndc_total_num_desde = 0
            z_ndc_total_num_hasta = 0

            z_total_credito = 0.00
            z_total_contado = 0.00


            if len(cortez) > 0:
                for lines in cortez:
                    # FAC
                    z_fact_vent_grav += lines.fact_vent_grav
                    z_fact_vent_exen += lines.fact_vent_exen
                    z_fact_vent_nosj += lines.fact_vent_nosj
                    z_fact_total += lines.fact_total
                    z_fact_total_num_desde = cortez[-1].fact_total_num_desde
                    if  cortez[0].fact_total_num_hasta == '0':
                        z_fact_total_num_hasta = cortez[-1].fact_total_num_hasta
                    else:
                        z_fact_total_num_hasta = cortez[0].fact_total_num_hasta

                    # CCF
                    z_ccf_vent_grav += lines.ccf_vent_grav
                    z_ccf_vent_exen += lines.ccf_vent_exen
                    z_ccf_vent_nosj += lines.ccf_vent_nosj
                    z_ccf_total += lines.ccf_total
                    z_ccf_total_num_desde = cortez[-1].ccf_total_num_desde
                    if cortez[0].ccf_total_num_hasta == '0':
                        z_ccf_total_num_hasta = cortez[-1].ccf_total_num_hasta
                    else:
                        z_ccf_total_num_hasta = cortez[0].ccf_total_num_hasta


                    # TK
                    z_tk_vent_grav += lines.tk_vent_grav
                    z_tk_vent_exen += lines.tk_vent_exen
                    z_tk_vent_nosj += lines.tk_vent_nosj
                    z_tk_total += lines.tk_total
                    # z_tk_total_num_desde = cortez[-1].tk_total_num_desde
                    # z_tk_total_num_hasta = cortez[0].tk_total_num_hasta

                    for desde in reversed(cortez):
                        if z_tk_total_num_desde == 0:
                            if desde.tk_total_num_desde != '0':
                                z_tk_total_num_desde = desde.tk_total_num_desde
                    for hasta in cortez:
                        if z_tk_total_num_hasta == 0:
                            if hasta.tk_total_num_hasta != '0':
                                z_tk_total_num_hasta = hasta.tk_total_num_hasta

                    # NDC
                    z_ndc_vent_grav += lines.ndc_vent_grav
                    z_ndc_vent_exen += lines.ndc_vent_exen
                    z_ndc_vent_nosj += lines.ndc_vent_nosj
                    z_ndc_total += lines.ndc_total
                    z_ndc_total_num_desde = cortez[-1].ndc_total_num_desde
                    if cortez[0].ndc_total_num_hasta == '0':
                        z_ccf_total_num_hasta = cortez[-1].ndc_total_num_hasta
                    else:
                        z_ndc_total_num_hasta = cortez[0].ndc_total_num_hasta


                    z_total_credito += lines.total_credito
                    z_total_contado += lines.total_contado

            cortezm = self.env['corte.zm']
            cortezm_id = cortezm.create({
                'fecha': datetime.now(),
                'fecha_impresion': datetime.now(),
                'fact_total_num_desde': z_fact_total_num_desde,
                'fact_total_num_hasta': z_fact_total_num_hasta,
                'fact_vent_grav': z_fact_vent_grav,
                'fact_vent_exen': z_fact_vent_exen,
                'fact_vent_nosj': z_fact_vent_nosj,
                'fact_total': z_fact_total,
                'ccf_total_num_desde': z_ccf_total_num_desde,
                'ccf_total_num_hasta': z_ccf_total_num_hasta,
                'ccf_vent_grav': z_ccf_vent_grav,
                'ccf_vent_exen': z_ccf_vent_exen,
                'ccf_vent_nosj': z_ccf_vent_nosj,
                'ccf_total': z_ccf_total,

                'tk_total_num_desde': z_tk_total_num_desde,
                'tk_total_num_hasta': z_tk_total_num_hasta,
                'tk_vent_grav': z_tk_vent_grav,
                'tk_vent_exen': z_tk_vent_exen,
                'tk_vent_nosj': z_tk_vent_nosj,

                'ndc_total_num_desde': z_ndc_total_num_desde,
                'ndc_total_num_hasta': z_ndc_total_num_hasta,
                'ndc_vent_grav': z_ndc_vent_grav,
                'ndc_vent_exen': z_ndc_vent_exen,
                'ndc_vent_nosj': z_ndc_vent_nosj,

                'tk_total': z_tk_total,
                'total_contado': z_total_contado,
                'total_credito': z_total_credito,
                'company_id': self.company_id.id
            })

            if len(cortez) > 0:
                for lines in cortez:
                    lines.cortezm_id = cortezm_id.id

        return True