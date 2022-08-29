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
from odoo import fields, models, api, _


class CustomTrialBalance(models.AbstractModel):
	_name = "custom.trial.balance"
	_description = "Trial Balance Report"
	_inherit = "account.coa.report"

	filter_comparison = None
	filter_analytic = False
	filter_hierarchy = True
	filter_multi_company = True
	filter_unfold_all = True
	filter_accumulative = False

	@api.model
	def _get_templates(self):
		templates = super(CustomTrialBalance, self)._get_templates()
		templates['line_template'] = 'b_custom_account_reports.custom_line_template'
		templates['search_template'] = 'b_custom_account_reports.search_template_custom'

		return templates

	@api.model
	def _get_columns(self, options):
		header1 = [
					  {'name': '', 'style': 'width: 100%'},
					  {'name': '', 'class': 'number', 'colspan': 1},
				  ] + [
					  {'name': options['date']['string'], 'class': 'number', 'colspan': 2},
					  {'name': '', 'class': 'number', 'colspan': 1},
				  ]
		header2 = [
			{'name': '', 'style': 'width: 100%'},
			{'name': _('Previous balance'), 'class': 'number o_account_coa_column_contrast'},
		]

		header2 += [
			{'name': _('Debit'), 'class': 'number o_account_coa_column_contrast'},
			{'name': _('Credit'), 'class': 'number o_account_coa_column_contrast'},
			{'name': _('Balance'), 'class': 'number o_account_coa_column_contrast'},
		]
		return [header1, header2]

	@api.model
	def _get_lines(self, options, line_id=None):
		# Create new options with 'unfold_all' to compute the initial balances.
		# Then, the '_do_query' will compute all sums/unaffected earnings/initial balances for all comparisons.
		new_options = options.copy()
		new_options['unfold_all'] = True
		options_list = self._get_options_periods_list(new_options)
		accounts_results, taxes_results = self.env['account.general.ledger']._do_query(options_list, fetch_lines=False)

		lines = []
		totals = [0.0] * (2 * (len(options_list) + 1))

		# Add lines, one per account.account record.
		for account, periods_results in accounts_results:
			sums = []
			account_balance = 0.0
			for i, period_values in enumerate(reversed(periods_results)):
				account_sum = period_values.get('sum', {})
				account_un_earn = period_values.get('unaffected_earnings', {})
				account_init_bal = period_values.get('initial_balance', {})

				if i == 0:
					# Append the initial balances.
					initial_balance = account_init_bal.get('balance', 0.0) + account_un_earn.get('balance', 0.0)
					if new_options.get('accumulative', False):
						sums += [
							initial_balance or 0.0
						]
					else:
						sums += [
							0.0
						]
					account_balance += initial_balance

				# Append the debit/credit columns.
				sums += [
					account_sum.get('debit', 0.0) - account_init_bal.get('debit', 0.0),
					account_sum.get('credit', 0.0) - account_init_bal.get('credit', 0.0),
				]
				account_balance += sums[-2] - sums[-1]

			# Append the totals.
			if new_options.get('accumulative', False):
				sums += [
					account_balance or 0.0
				]
			else:
				sums += [
					0.0
				]

			# account.account report line.
			columns = []
			for i, value in enumerate(sums):
				# Update totals.
				totals[i] += value

				# Create columns.
				columns.append(
					{'name': self.format_value(value, blank_if_zero=False), 'class': 'number', 'no_format_name': value})

			name = account.name_get()[0][1]

			lines.append({
				'id': self._get_generic_line_id('account.account', account.id),
				'name': name,
				'code': account.code,
				'title_hover': name,
				'columns': columns,
				'unfoldable': False,
				'caret_options': 'account.account',
				'class': 'o_account_searchable_line o_account_coa_column_contrast',
			})

		# Total report line.
		lines.append({
			'id': self._get_generic_line_id(None, None, markup='grouped_accounts_total'),
			'name': _('Total'),
			'class': 'total o_account_coa_column_contrast',
			'columns': [{'name': self.format_value(total), 'class': 'number'} for total in totals],
			'level': 1,
		})

		return lines

	def print_pdf(self, options):
		report_name = 'financierosv_sucursal.report_balance_pdf'
		# report = self.env['ir.actions.report']._get_report_from_name(report_name)
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
		return self.env.ref('financierosv_sucursal.report_balance_pdf').report_action(self, data=data)
