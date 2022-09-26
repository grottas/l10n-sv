from email.policy import default
from odoo import fields, models, api, _
from odoo.exceptions import Warning, RedirectWarning
from datetime import datetime, date, time, timedelta
from pytz import timezone
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import SUPERUSER_ID

class wizard_sv_general_report(models.TransientModel):
    _name = 'wizard.sv.general.report'

    company_id=fields.Many2one('res.company', string="Company", help='Company',default=lambda self: self.env.user.company_id.id)
    date_month = fields.Selection([('1','Enero'),('2','Febrero'),('3','Marzo'),('4','Abril'),('5','Mayo'),('6','Junio'),('7','Julio'),('8','Agosto'),('9','Septiembre'),('10','Octubre'),('11','Noviembre'),('12','Diciembre')],string='Mes de facturación', default='3',required=True)
    date_year = fields.Integer("Año de facturación", default=2022, requiered=True)
   # contabilizada=fields.Boolean(string="contabilizada", default=False)
    acum=fields.Boolean(string="Acumulativo",default=True)
    fechai=fields.Date(string="Fecha Inicial",default='2022-3-1')
    fechaf=fields.Date(string="Fecha Final",default='2022-3-31')
    cont=fields.Char(string="Contador")
    audi=fields.Char(string="Auditor")
    repre=fields.Char(string="Representante")
    #show_serie = fields.Boolean("Ventas a Consumidor", default=False)
    #serie_lenght = fields.Integer("Agrupación de facturas", default = 1)

    def print_general_report(self):
        datas = {'ids': self._ids,
                 'form': self.read()[0],
                 'model': 'wizard.sv.general.report'}
        return self.env.ref('financierosv_sucursal.report_general_pdf').report_action(self, data=datas)
