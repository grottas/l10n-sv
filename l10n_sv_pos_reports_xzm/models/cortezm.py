from odoo import fields, models, api


class CorteZM(models.Model):
    _name = 'corte.zm'
    _description = 'Corte ZM'
    _order = 'fecha desc, id desc'
    _inherit = ['portal.mixin', 'mail.thread', 'mail.activity.mixin', 'utm.mixin']

    name = fields.Char(string='Nombre', compute='_name_cortezm', readonly=True)

    # ENCABEZADO
    fecha = fields.Date(string='Fecha de corte z', readonly=True)
    fecha_impresion = fields.Date(string='Fecha de impresion', readonly=True)
    company_id = fields.Many2one('res.company', string='Compania', readonly=True)

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

    def _name_cortezm(self):
        for record in self:
            record.name = 'Corte ZM ' + str(record.id)

    def create(self, vals_list):
        result = super(CorteZM, self).create(vals_list)
        return result

