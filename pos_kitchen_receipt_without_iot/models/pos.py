from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    allow_kitchens_receipt = fields.Boolean('Allow Kitchen Receipt', default=True)
    use_multi_printer = fields.Boolean('Use multi printer', default=False)

    @api.onchange('allow_kitchens_receipt')
    def _onchange_use_multi_printer(self):
        self.ensure_one()
        self.use_multi_printer = False if not self.allow_kitchens_receipt else self.use_multi_printer


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _get_fields_for_order_line(self):
        res = super(PosOrder, self)._get_fields_for_order_line()
        res += ['printed_line_id']
        return res


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    printed_line_id = fields.Char(string='It is used to kwnow if was sended to kitchen')
