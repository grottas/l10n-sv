from odoo import fields, models
from functools import partial



class PosOrder(models.Model):
    _inherit = "pos.order"

    def _order_fields(self, ui_order):
        res = super(PosOrder, self)._order_fields(ui_order)
        process_line = partial(self.env['pos.order.line'].with_context(add_own_line=True)._order_line_fields)
        order_lines = [process_line(line) for line in ui_order['lines']] if ui_order['lines'] else False
        new_order_line = []
        if order_lines:
            for order_line in order_lines:
                if order_line:
                    new_order_line.append(order_line)
                    if "own_line" in order_line[2] and res.get('to_invoice', False):
                        own_pro_list = [process_line(line, None) for line in order_line[2]["own_line"]] if order_line[2]["own_line"] else False
                        if own_pro_list:
                            for own in own_pro_list:
                                new_order_line.append(own)
        if new_order_line:
            for order_line in range(len(new_order_line)):
                if len(ui_order['lines']) > order_line:
                    if ui_order['lines'][order_line] and ui_order['lines'][order_line][2].get('sale_order_origin_id'):
                        new_order_line[order_line][2]['sale_order_origin_id'] = ui_order['lines'][order_line][2]['sale_order_origin_id']
                    if ui_order['lines'][order_line][2].get('sale_order_line_id'):
                        new_order_line[order_line][2]['sale_order_line_id'] = ui_order['lines'][order_line][2]['sale_order_line_id']
            process_line = partial(self.env['pos.order.line']._order_line_fields)
            order_lines = [process_line(line) for line in new_order_line]
            res['lines'] = order_lines
        return res


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    is_selection_combo = fields.Boolean("Selection Combo Line")
    own_ids = fields.One2many("pos.order.line.own", 'orderline_id', "Extra Toppings")

    def _order_line_fields(self, line, session_id=None):
        own_line = []
        if line and 'own_line' in line[2] and self.env.context.get('add_own_line', False):
            own_line = line[2]['own_line']

        line = super(PosOrderLine, self)._order_line_fields(line, session_id=session_id)

        if own_line:
            line[2]['own_line'] = own_line
        return line


class pos_order_line_own(models.Model):
    _name = "pos.order.line.own"
    _description = "POS Order Line own"

    orderline_id = fields.Many2one('pos.order.line', 'POS Line')
    product_id = fields.Many2one('product.product', 'Product')
    price = fields.Float('Item Price', required=True)
    qty = fields.Float('Quantity', default='1', required=True)
