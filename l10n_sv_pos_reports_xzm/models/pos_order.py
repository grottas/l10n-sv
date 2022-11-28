from odoo import fields, models, api


class PosOrder(models.Model):
    _inherit = 'pos.order'

    cortex_id = fields.Many2one('corte.x', string='# de Corte X')
