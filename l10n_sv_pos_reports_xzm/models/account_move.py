from odoo import fields, models, api


class AccountMove(models.Model):
    _inherit = 'account.move'

    cortex_id = fields.Many2one('corte.x', string='# de Corte X', readonly=True)
