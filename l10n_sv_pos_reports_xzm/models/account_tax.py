from odoo import fields, models, api


class AcccountTax(models.Model):
   _inherit = 'account.tax'

   es_tax_consumidor = fields.Boolean(string='Es Impuesto al Consumidor Final', default=False)
   es_tax_contribuyente = fields.Boolean(string='Es Impuesto al Contribuyente', default=False)
   es_tax_exento = fields.Boolean(string='Es Impuesto Exento', default=False)
   es_tax_nosujeto = fields.Boolean(string='Es Impuesto No Sujeto', default=False)