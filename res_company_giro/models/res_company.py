from odoo import fields, models, api


class ResCompany(models.Model):
    _inherit = 'res.company'

    giro = fields.Char(string='Giro Fiscal')
