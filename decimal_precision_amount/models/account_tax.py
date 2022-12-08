from odoo import fields, models, api


class AccountTax(models.Model):
    _inherit = 'account.tax'

    amount = fields.Float(digits=(12, 0))
