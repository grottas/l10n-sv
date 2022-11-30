# -*- encoding: utf-8 -*-
#
# Module written to Odoo, Open Source Management Solution
#
# Copyright (c) 2022 Birtum - http://www.birtum.com
# All Rights Reserved.
#
# Developer(s): Carlos Maykel López González
#               (clg@birtum.com)
#
########################################################################
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
########################################################################

from odoo import fields, models, api, _


class CustomResultState(models.Model):
	_inherit = "account.financial.html.report"

	def _get_report_name(self):
		if self.id == self.env.ref('b_custom_account_reports.expanded_balance_sheet_report').id:
			return _('Estado de Resultado')
		else:
			return super(CustomResultState, self)._get_report_name()

	def print_pdf(self, options):
		"""
		Printing to pdf is redefined using the reports defined in the module "financierosv_sucursal"
		"""
		if self.id == self.env.ref('b_custom_account_reports.result_state_report').id:

			report_name = 'financierosv_sucursal.report_resultado_pdf'
			date_from = fields.Date.from_string(options.get('date').get('date_from'))
			date_to = fields.Date.from_string(options.get('date').get('date_to'))

			form = {
				'fechai': date_from,
				'fechaf': date_to,
				'date_year': 2022,
				'date_month': 1,
				'acum': options.get('accumulative', False),
				'company_id': [self.env.company.id]
			}
			data = {
				'ids': [self.env.company.id],
				'form': form,
				'model': 'res_company'
			}
			return self.env.ref('financierosv_sucursal.report_resultado_pdf').report_action(self, data=data)
		else:
			return super(CustomResultState, self).print_pdf(options=options)
