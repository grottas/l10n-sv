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

from odoo.tools.misc import formatLang, format_date
from odoo import fields, models, api, _


class CustomBalanceSituation(models.AbstractModel):
	_name = 'custom.balance.situation'
	_description = 'Custom Balance Sheet'
	_inherit = "account.coa.report"

	# filter_comparison = False
	filter_analytic = False
	filter_hierarchy = True
	filter_multi_company = True
	filter_unfold_all = False

	@api.model
	def _get_templates(self):
		templates = super(CustomBalanceSituation, self)._get_templates()
		templates['line_template'] = 'b_custom_account_reports.custom_sheet_balance'
		# templates['search_template'] = 'b_custom_account_reports.search_template_custom'

		return templates

	@api.model
	def _get_columns(self, options):
		header1 = [
					  {'name': '', 'style': 'width: 100%'},
				  ] + [
					  {'name': options['date']['string'], 'class': 'number', 'colspan': 5}
				  ]

		header2 = [
					  {'name': '', 'style': 'width: 100%'},
				  ] + [
					  {'name': '', 'class': 'number', 'colspan': 5}
				  ]

		return [header1]

	@api.model
	def _get_lines(self, options, line_id=None):
		# Create new options with 'unfold_all' to compute the initial balances.
		# Then, the '_do_query' will compute all sums/unaffected earnings/initial balances for all comparisons.
		new_options = options.copy()
		new_options['unfold_all'] = True
		new_options['unfolded_lines'] = [
			'-account.account-964|-account.group-118'
		]
		options_list = self._get_options_periods_list(new_options)
		accounts_results, taxes_results = self.env['account.general.ledger']._do_query(options_list, fetch_lines=True)

		lines = []
		totals = [0.0] * ((len(options_list)))

		# Add lines, one per account.account record.
		for account, periods_results in accounts_results:
			sums = []
			sums1 = []
			account_balance = 0.0
			for i, period_values in enumerate(reversed(periods_results)):
				account_sum = period_values.get('sum', {})
				account_un_earn = period_values.get('unaffected_earnings', {})
				account_init_bal = period_values.get('initial_balance', {})

				if i == 0:
					# Append the initial balances.
					initial_balance = account_init_bal.get('balance', 0.0) + account_un_earn.get('balance', 0.0)
					account_balance += initial_balance

				sums1 += [
					account_sum.get('debit', 0.0) - account_init_bal.get('debit', 0.0),
					account_sum.get('credit', 0.0) - account_init_bal.get('credit', 0.0),
				]

				account_balance += sums1[-2] - sums1[-1]
				# account_balance += sums1[-1] - sums1[-2]

				# Append the totals.
				sums += [
					account_balance or 0.0
				]

			name = account.name_get()[0][1]

			# account.account report line.
			columns = []
			for i, value in enumerate(sums):
				# Update totals.
				totals[i] += value

				# Create columns.
				columns.append(
					{'name': self.format_value(value, blank_if_zero=False), 'class': 'number', 'no_format_name':
						value})

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
