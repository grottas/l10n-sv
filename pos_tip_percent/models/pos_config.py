# -*- coding: utf-8 -*-
# Part of Odoo. See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class PosConfig(models.Model):
    _inherit = 'pos.config'

    module_pos_tip_percent = fields.Boolean(string='Propinas globales')
    iface_tip = fields.Boolean(string='Order tips', help='Allow the cashier to give tips on the whole order.')
    tip_pc = fields.Float(string='Propina %', help='The default tip percentage', default=10.0)
    tip_product_id = fields.Many2one('product.product', string='Producto de propina',
        domain="[('sale_ok', '=', True)]", help='The product used to model the tip.')

    @api.onchange('company_id','module_pos_tip')
    def _default_tip_product_id(self):
        product = self.env.ref("point_of_sale.product_product_consumable", raise_if_not_found=False)
        self.tip_product_id = product if self.module_pos_tip_percent and product and (not product.company_id or product.company_id == self.company_id) else False

    @api.model
    def _default_tip_value_on_module_install(self):
        configs = self.env['pos.config'].search([])
        open_configs = (
            self.env['pos.session']
            .search(['|', ('state', '!=', 'closed'), ('rescue', '=', True)])
            .mapped('config_id')
        )
        # Do not modify configs where an opened session exists.
        for conf in (configs - open_configs):
            conf._default_tip_product_id()
