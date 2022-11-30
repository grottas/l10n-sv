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

import json
import datetime
import io

from odoo import fields, models, api, _
from odoo.tools.misc import xlsxwriter
from odoo.tools import config, date_utils, get_lang


class CustomSheetBalance(models.Model):
	_inherit = "account.financial.html.report"

	filter_analytic = False
	filter_accumulative = False

	def _get_report_name(self):
		""" Devuelve el nombre del reporte """
		if self.id == self.env.ref('b_custom_account_reports.report_balance_sheet').id:
			return _('Balance General')
		else:
			return super(CustomSheetBalance, self)._get_report_name()

	@api.model
	def _get_templates(self):
		templates = super(CustomSheetBalance, self)._get_templates()
		templates['search_template'] = 'b_custom_account_reports.custom_search_sheet'

		return templates

	def print_pdf(self, options):
		"""
		 Printing to pdf is redefined using the reports defined in the module "financierosv_sucursal"
		"""
		if self.id == self.env.ref('b_custom_account_reports.report_balance_sheet').id:

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
			return self.env.ref('financierosv_sucursal.report_general_pdf').report_action(self, data=data)
		else:
			return super(CustomSheetBalance, self).print_pdf(options=options)
