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
from collections import defaultdict


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
					  {'name': '', 'style': 'width: 100%'}
				  ] + [
					  {'name': options['date']['string'], 'class': 'number', 'colspan': 4},
				  ]
		header2 = [
			{'name': ' ', 'style': 'width: 100%'},
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
			sums1 = []
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
			sums += [
				account_balance or 0.0
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
				'code': account.code,
				'name': name,
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
		"""
		Printing to pdf is redefined using the reports defined in the module "financierosv_sucursal"
		"""
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

	def print_xlsx(self, options):
		"""
		The printing to excel of the module from which it is inherited is redefined
		"""
		return {
			'type': 'ir_actions_account_report_download',
			'data': {'model': self.env.context.get('model'),
					 'options': json.dumps(options),
					 'output_format': 'xlsx',
					 'financial_id': self.env.context.get('id'),
					 'allowed_company_ids': self.env.context.get('allowed_company_ids'),
					 }
		}

	def get_xlsx(self, options, response=None):
		"""
		The excel file is created in memory with the data obtained from Odoo
		"""
		output = io.BytesIO()
		workbook = xlsxwriter.Workbook(output, {
			'in_memory': True,
			'strings_to_formulas': False,
		})
		sheet = workbook.add_worksheet(self._get_report_name()[:31])

		date_default_col1_style = workbook.add_format(
			{'font_name': 'Arial', 'font_size': 11, 'font_color': '#666666', 'indent': 2, 'num_format': 'yyyy-mm-dd', 'align': 'right'})
		date_default_style = workbook.add_format(
			{'font_name': 'Arial', 'font_size': 11, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})
		number_default_style = workbook.add_format(
			{'font_name': 'Arial', 'font_size': 11, 'font_color': '#666666', 'num_format': '#,##0.00'})
		default_col1_style = workbook.add_format(
			{'font_name': 'Arial', 'font_size': 11, 'font_color': '#666666', 'indent': 2})
		default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'font_color': '#666666'})
		title_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'bottom': 2, 'align': 'right'})
		level_0_style = workbook.add_format(
			{'font_name': 'Arial', 'bold': True, 'font_size': 10, 'bottom': 6, 'font_color': '#666666'})
		level_1_style = workbook.add_format(
			{'font_name': 'Arial', 'bold': True, 'font_size': 10, 'bottom': 1, 'font_color': '#666666'})
		level_2_col1_style = workbook.add_format(
			{'font_name': 'Arial', 'bold': True, 'font_size': 10, 'font_color': '#666666', 'indent': 1})
		level_2_col1_total_style = workbook.add_format(
			{'font_name': 'Arial', 'bold': True, 'font_size': 10, 'font_color': '#666666'})
		level_2_style = workbook.add_format(
			{'font_name': 'Arial', 'bold': True, 'font_size': 10, 'font_color': '#666666'})
		level_3_col1_style = workbook.add_format(
			{'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'indent': 2})
		level_3_col1_total_style = workbook.add_format(
			{'font_name': 'Arial', 'bold': True, 'font_size': 10, 'font_color': '#666666', 'indent': 1})
		level_3_style = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'font_color': '#666666'})

		company_name_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'font_size': 20, 'font_color': '#666666'})
		period_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'font_size': 14, 'font_color': '#666666'})
		note_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'font_size': 12, 'font_color': '#666666'})
		signature_style = workbook.add_format(
			{'font_name': 'Arial', 'valign': 'bottom', 'font_size': 12, 'font_color': '#666666'})
		code_style = workbook.add_format(
			{'font_name': 'Arial', 'valign': 'left', 'font_size': 10, 'font_color': '#666666'})

		# Set the first column width to 50
		sheet.set_column(0, 0, 50)

		period = self._get_report_name() + ' DEL ' + options.get('date').get('date_from') + ' AL ' + options.get('date').get('date_to')

		sheet.set_row(0, 30)
		sheet.merge_range(0, 0, 0, 5, self.env.company.name, company_name_style)
		sheet.set_row(1, 20)
		sheet.merge_range(1, 0, 1, 5, period, period_style)
		sheet.merge_range(2, 0, 2, 5, '(Valores expresados en dólares de los Estados Unidos de America)', note_style)

		y_offset = 3
		headers, lines = self.with_context(no_format=True, print_mode=True, prefetch_fields=False)._get_table(options)

		tmp = [
			{'name': 'Código', 'style': '10%'},
			{'name': 'Cuenta', 'style': '90%'},
			{'name': 'Saldo anterior', 'class': 'number o_account_coa_column_contrast'},
			{'name': 'Débito', 'class': 'number o_account_coa_column_contrast'},
			{'name': 'Crédito', 'class': 'number o_account_coa_column_contrast'},
			{'name': 'Balance', 'class': 'number o_account_coa_column_contrast'}
		]

		headers[1] = tmp

		# Add headers.
		for header in headers:
			x_offset = 0
			for column in header:
				column_name_formated = column.get('name', '').replace('<br/>', ' ').replace('&nbsp;', ' ')
				colspan = column.get('colspan', 1)
				if colspan == 1:
					sheet.set_column(y_offset, x_offset, 40)
					sheet.write(y_offset, x_offset, column_name_formated, title_style)
				# else:
				# sheet.merge_range(y_offset, x_offset, y_offset, x_offset + colspan, column_name_formated,title_style)
				x_offset += colspan
			y_offset += 1

		if options.get('hierarchy'):
			lines = self._create_hierarchy(lines, options)
		if options.get('selected_column'):
			lines = self._sort_lines(lines, options)

		# Add lines.
		for y in range(0, len(lines)):
			level = lines[y].get('level')
			if lines[y].get('caret_options'):
				style = level_3_style
				col1_style = level_3_col1_style
			elif level == 0:
				y_offset += 1
				style = level_0_style
				col1_style = style
			elif level == 1:
				style = level_1_style
				col1_style = style
			elif level == 2:
				style = level_2_style
				col1_style = 'total' in lines[y].get('class', '').split(
					' ') and level_2_col1_total_style or level_2_col1_style
			elif level == 3:
				style = level_3_style
				col1_style = 'total' in lines[y].get('class', '').split(
					' ') and level_3_col1_total_style or level_3_col1_style
			else:
				style = default_style
				col1_style = default_col1_style

			sheet.write(y + y_offset, 0, lines[y].get('code'), code_style)

			# write the first column, with a specific style to manage the indentation
			cell_type, cell_value = self._get_cell_type_value(lines[y])
			if lines[y].get('class') != 'total o_account_coa_column_contrast':
				if cell_type == 'date':
					sheet.write_datetime(y + y_offset, 1, cell_value, date_default_col1_style)
				else:
					cell_value = cell_value.split(' ', 1)
					if len(cell_value) == 1:
						cuenta = cell_value[0]
					else:
						cuenta = cell_value[1]
					sheet.write(y + y_offset, 1, cuenta, col1_style)

			# write all the remaining cells
			if lines[y].get('class') != 'total o_account_coa_column_contrast':
				for x in range(1, len(lines[y]['columns']) + 1):
					cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 1])
					if cell_type == 'number':
						sheet.write_number(y + y_offset, x + lines[y].get('colspan', 1), cell_value,
										   number_default_style)
					else:
						sheet.write(y + y_offset, x + lines[y].get('colspan', 1), cell_value, style)

		sheet.set_row(len(lines) + 10, 30)

		sheet.merge_range(len(lines) + 10, 0, len(lines) + 10, 5,
						  'F._________________                                '
						  'F._________________                                   '
						  'F._________________', signature_style)

		sheet.merge_range(len(lines) + 11, 0, len(lines) + 11, 5,
						  '            Representante Legal                                                    '
						  '                      Contador                                                 '
						  '                          Auditor ', '')

		workbook.close()
		output.seek(0)
		generated_file = output.read()
		output.close()

		return generated_file

	def _get_cell_type_value(self, cell):
		"""
		Returns the value of each cell and its format to print it in the excel file
		"""
		if 'no_format_name' in cell:
			return ('number', cell.get('no_format_name', ''))
		if 'number' in cell.get('class', ''):
			return ('number', cell.get('name', ''))
		if 'date' not in cell.get('class', '') or not cell.get('name'):
			# cell is not a date
			return ('text', cell.get('name', ''))
		if isinstance(cell['name'], (float, datetime.date, datetime.datetime)):
			# the date is xlsx compatible
			return ('date', cell['name'])
		try:
			# the date is parsable to a xlsx compatible date
			lg = self.env['res.lang']._lang_get(self.env.user.lang) or get_lang(self.env)
			return ('date', datetime.datetime.strptime(cell['name'], lg.date_format))
		except:
			# the date is not parsable thus is returned as text
			return ('text', cell['name'])

	@api.model
	def _create_hierarchy(self, lines, options):
		"""Compute the hierarchy based on account groups when the option is activated.

		The option is available only when there are account.group for the company.
		It should be called when before returning the lines to the client/templater.
		The lines are the result of _get_lines(). If there is a hierarchy, it is left
		untouched, only the lines related to an account.account are put in a hierarchy
		according to the account.group's and their prefixes.
		"""
		unfold_all = self.env.context.get('print_mode') and len(options.get('unfolded_lines')) == 0 or options.get(
			'unfold_all')

		def add_to_hierarchy(lines, key, level, parent_id, hierarchy):
			val_dict = hierarchy[key]
			unfolded = val_dict['id'] in options.get('unfolded_lines') or unfold_all
			# add the group totals
			lines.append({
				'id': val_dict['id'],
				'code': val_dict['code'],
				'name': val_dict['name'],
				'title_hover': val_dict['name'],
				'unfoldable': True,
				'unfolded': unfolded,
				'level': level,
				'parent_id': parent_id,
				'columns': [{'name': self.format_value(c) if isinstance(c, (int, float)) else c, 'no_format_name': c}
							for c in val_dict['totals']],
			})
			if not self._context.get('print_mode') or unfolded:
				for i in val_dict['children_codes']:
					hierarchy[i]['parent_code'] = i
				all_lines = [hierarchy[id] for id in val_dict["children_codes"]] + val_dict["lines"]
				for line in sorted(all_lines, key=lambda k: k.get('account_code', '') + k['name']):
					if 'children_codes' in line:
						children = []
						# if the line is a child group, add it recursively
						add_to_hierarchy(children, line['parent_code'], level + 1, val_dict['id'], hierarchy)
						lines.extend(children)
					else:
						# add lines that are in this group but not in one of this group's children groups
						line['level'] = level + 1
						line['parent_id'] = val_dict['id']
						lines.append(line)

		def compute_hierarchy(lines, level, parent_id):
			# put every line in each of its parents (from less global to more global) and compute the totals
			hierarchy = defaultdict(
				lambda: {'totals': [None] * len(lines[0]['columns']), 'lines': [], 'children_codes': set(), 'name': '',
						 'parent_id': None, 'id': ''})
			for line in lines:
				account = self.env['account.account'].browse(
					line.get('account_id', self._get_caret_option_target_id(line.get('id'))))
				codes = self.get_account_codes_custom(account)  # id, name
				for code in codes:
					hierarchy[code[0]]['id'] = self._get_generic_line_id('account.group', code[0],
																		 parent_line_id=line['id'])
					hierarchy[code[0]]['name'] = code[1]
					hierarchy[code[0]]['code'] = self.env['account.group'].browse(code[0]).code_prefix_start
					for i, column in enumerate(line['columns']):
						if 'no_format_name' in column:
							no_format = column['no_format_name']
						elif 'no_format' in column:
							no_format = column['no_format']
						else:
							no_format = None
						if isinstance(no_format, (int, float)):
							if hierarchy[code[0]]['totals'][i] is None:
								hierarchy[code[0]]['totals'][i] = no_format
							else:
								hierarchy[code[0]]['totals'][i] += no_format
				for code, child in zip(codes[:-1], codes[1:]):
					hierarchy[code[0]]['children_codes'].add(child[0])
					hierarchy[child[0]]['parent_id'] = hierarchy[code[0]]['id']
				hierarchy[codes[-1][0]]['lines'] += [line]
			# compute the tree-like structure by starting at the roots (being groups without parents)
			hierarchy_lines = []
			for root in [k for k, v in hierarchy.items() if not v['parent_id']]:
				add_to_hierarchy(hierarchy_lines, root, level, parent_id, hierarchy)
			return hierarchy_lines

		new_lines = []
		account_lines = []
		current_level = 0
		parent_id = 'root'
		for line in lines:
			if not (line.get('caret_options') == 'account.account' or line.get('account_id')):
				# make the hierarchy with the lines we gathered, append it to the new lines and restart the gathering
				if account_lines:
					new_lines.extend(compute_hierarchy(account_lines, current_level + 1, parent_id))
				account_lines = []
				new_lines.append(line)
				current_level = line['level']
				parent_id = line['id']
			else:
				# gather all the lines we can create a hierarchy on
				account_lines.append(line)
		# do it one last time for the gathered lines remaining
		if account_lines:
			new_lines.extend(compute_hierarchy(account_lines, current_level + 1, parent_id))
		return new_lines

	def get_account_codes_custom(self, account):
		# A code is tuple(id, name)
		codes = []
		if account.group_id:
			group = account.group_id
			while group:
				codes.append((group.id, group.display_name, account.group_id.code_prefix_start))
				group = group.parent_id
		else:
			codes.append((0, _('(No Group)'), ' '))
		return list(reversed(codes))

	def _get_report_name(self):
		return ("Balance Sumas y Saldos")
