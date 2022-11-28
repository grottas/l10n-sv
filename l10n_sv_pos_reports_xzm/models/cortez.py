from odoo import fields, models, api
from datetime import datetime
from odoo.exceptions import AccessError, UserError, ValidationError

class CorteZ(models.Model):
    _name = 'corte.z'
    _description = 'Corte Z'
    _order = 'fecha desc, id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Nombre', compute='_name_cortez', readonly=True)

    # RELACIONES
    cortezm_id = fields.Many2one('corte.zm', string='Corte ZM', readonly=True)
    company_id = fields.Many2one('res.company', string='Compañía', readonly=True)

    # ENCABEZADO
    fecha = fields.Date(string='Fecha de corte z', readonly=True)
    fecha_impresion = fields.Date(string='Fecha de impresion', readonly=True)

    # FAC
    fact_total_num_desde = fields.Char('#Fac desde', readonly=True)
    fact_total_num_hasta = fields.Char('#Fac hasta', readonly=True)
    fact_vent_grav = fields.Float('FAC. Total ventas gravadas', readonly=True)
    fact_vent_exen = fields.Float('FAC. Total ventas exentas', readonly=True)
    fact_vent_nosj = fields.Float('FAC. Total ventas no sujetas', readonly=True)
    fact_total = fields.Float('Total de Facturas', readonly=True)

    # CCF
    ccf_total_num_desde = fields.Char('#CCF desde', readonly=True)
    ccf_total_num_hasta = fields.Char('#CCF hasta', readonly=True)
    ccf_vent_grav = fields.Float('CCF. Total ventas gravadas', readonly=True)
    ccf_vent_exen = fields.Float('CCF. Total ventas exentas', readonly=True)
    ccf_vent_nosj = fields.Float('CCF. Total ventas no sujetas', readonly=True)
    ccf_total = fields.Float('Total de CCF', readonly=True)

    # TK
    tk_total_num_desde = fields.Char('#TK  desde', readonly=True)
    tk_total_num_hasta = fields.Char('#TK hasta', readonly=True)
    tk_vent_grav = fields.Float('TK. Total ventas gravadas', readonly=True)
    tk_vent_exen = fields.Float('TK. Total ventas exentas', readonly=True)
    tk_vent_nosj = fields.Float('TK. Total ventas no sujetas', readonly=True)
    tk_total = fields.Float('Total de TK', readonly=True)

    # NDC
    ndc_total_num_desde = fields.Char('#NDC  desde', readonly=True)
    ndc_total_num_hasta = fields.Char('#NDC hasta', readonly=True)
    ndc_vent_grav = fields.Float('NDC. Total ventas gravadas', readonly=True)
    ndc_vent_exen = fields.Float('NDC. Total ventas exentas', readonly=True)
    ndc_vent_nosj = fields.Float('NDC. Total ventas no sujetas', readonly=True)
    ndc_total = fields.Float('Total de NDC', readonly=True)

    total_credito = fields.Float('Total credito', readonly=True)
    total_contado = fields.Float('Total contado', readonly=True)

    def _name_cortez(self):
        for record in self:
            record.name = 'Corte Z ' + str(record.id)

    def create(self, vals_list):
        result = super(CorteZ, self).create(vals_list)
        return result


    def generar_cortez(self):
        fecha = datetime.strftime(self.start_at, '%d-%m-%Y')
        cortex = self.env['corte.x'].search([('fecha', '=', fecha)])

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
                z_fact_total_num_hasta = cortex[0].fact_total_num_hasta

                # CCF
                z_ccf_vent_grav += lines.ccf_vent_grav
                z_ccf_vent_exen += lines.ccf_vent_exen
                z_ccf_vent_nosj += lines.ccf_vent_nosj
                z_ccf_total += lines.ccf_total
                z_ccf_total_num_desde = cortex[-1].ccf_total_num_desde
                z_ccf_total_num_hasta = cortex[-0].ccf_total_num_hasta

                # TK
                z_tk_vent_grav += lines.tk_vent_grav
                z_tk_vent_exen += lines.tk_vent_exen
                z_tk_vent_nosj += lines.tk_vent_nosj
                z_tk_total += lines.tk_total
                z_tk_total_num_desde = cortex[-1].tk_total_num_desde
                z_tk_total_num_hasta = cortex[0].tk_total_num_hasta

                # NDC
                z_ndc_vent_grav += lines.tk_vent_grav
                z_ndc_vent_exen += lines.tk_vent_exen
                z_ndc_vent_nosj += lines.tk_vent_nosj
                z_ndc_total += lines.tk_total
                z_ndc_total_num_desde = cortex[-1].ndc_total_num_desde
                z_ndc_total_num_hasta = cortex[0].ndc_total_num_hasta

                z_total_credito += lines.total_credito
                z_total_contado += lines.total_contado


        self.create({
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
        })

        cortez = self.env['corte.z'].search([('fecha', '=', datetime.strftime(datetime.now(), '%d-%m-%Y'))])
        if len(cortex) > 0:
            for lines in cortex:
                lines.cortez_id = cortez.id



        return True