import ast
from odoo import fields, models


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _get_fields_for_order_line(self):
        res = super(PosOrder, self)._get_fields_for_order_line()
        res += ['order_menu', 'own_data', 'own_ids', 'is_selection_combo']
        return res

    @staticmethod
    def _order_lines_combo(orders):
        """
            the function captures and eliminates the repeated lines that are generated from the combo
        """
        for order in orders:
            list_combo = []
            list_del = []
            if order.get("lines", False):
                # Cap
                for num, line in enumerate(order['lines']):
                    if line[2]['is_selection_combo'] and line[2]['order_menu']:
                        for products in line[2]['order_menu']:
                            list_combo += products['products']
                    else:
                        # this line exist in list_destruction, compare a product_id and qty
                        for count, del_elem in enumerate(list_combo):
                            if line[2]['product_id'] == del_elem['product_id'] and line[2]['qty'] == del_elem['qty']:
                                list_del.append(order['lines'][num])
                                list_combo.pop(count)
                # delete
                for element in list_del:
                    if element in order['lines']:
                        order['lines'].remove(element)

    def order_line_pos(self, order_line):
        order_line['order_menu'] = ast.literal_eval(order_line['order_menu']) if order_line['order_menu'] else False
        order_line['own_data'] = ast.literal_eval(order_line['own_data']) if order_line['own_data'] else False
        res = super(PosOrder, self).order_line_pos(order_line)

    def _get_order_lines(self, orders):
        res = super(PosOrder, self)._get_order_lines(orders)
        self._order_lines_combo(orders)
        return res


class PosOrderLine(models.Model):
    _inherit = "pos.order.line"

    order_menu = fields.Text()
    own_data = fields.Text()
