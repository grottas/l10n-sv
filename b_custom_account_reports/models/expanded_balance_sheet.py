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


class ExpandedBalanceSheet(models.Model):
	_inherit = "account.financial.html.report"

	position = fields.Integer(help="Indicates the position where it will be printed in the excel file")

	filter_analytic = False

	def print_pdf(self, options):
		if self.id == self.env.ref('b_custom_account_reports.expanded_balance_sheet_report').id:
			date_from = fields.Date.from_string(options.get('date').get('date_from'))
			date_to = fields.Date.from_string(options.get('date').get('date_to'))

			form = {
				'fechai': date_from,
				'fechaf': date_to,
				'date_year': 0000,
				'date_month': 1,
				'acum': options.get('accumulative', True),
				'company_id': [self.env.company.id]
			}
			data = {
				'ids': [self.env.company.id],
				'form': form,
				'model': 'res_company'
			}
			return self.env.ref('financierosv_sucursal.report_general_pdf').report_action(self, data=data)
		else:
			return super(ExpandedBalanceSheet, self).print_pdf(options=options)

	def _get_report_name(self):
		if self.id == self.env.ref('b_custom_account_reports.expanded_balance_sheet_report').id:
			return _('Balance de Comprobación')
		else:
			return super(ExpandedBalanceSheet, self)._get_report_name()

	def print_xlsx(self, options):
		"""
		Printing to pdf is redefined using the reports defined in the module "financierosv_sucursal"
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

	def _state_result_xlsx(self, options):
		"""
		Generates the excel view of the Income Statement report with the same format as the PDF document
		"""
		output = io.BytesIO()
		workbook = xlsxwriter.Workbook(output, {
			'in_memory': True,
			'strings_to_formulas': False,
		})
		sheet = workbook.add_worksheet(self._get_report_name()[:31])

		sheet.set_print_scale(95)
		sheet.set_paper(1)
		sheet.center_horizontally()

		date_default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})

		level_0_style = workbook.add_format(
			{'font_name': 'Arial', 'bold': True, 'font_size': 11, 'valign': 'vcenter', 'bottom': 6, 'font_color': '#666666'})
		level_0_number = workbook.add_format(
			{'font_name': 'Arial', 'bold': True, 'font_size': 10, 'valign': 'vcenter', 'font_color': '#666666', 'num_format': '#,##0.00'})

		level_1_style = workbook.add_format({'font_name': 'Arial', 'bold': True, 'font_size': 10, 'valign': 'vcenter', 'font_color': '#666666'})
		level_1_number = workbook.add_format(
			{'font_name': 'Arial', 'bold': False, 'font_size': 10, 'valign': 'vcenter', 'font_color': '#666666', 'num_format': '#,##0.00'})

		level_2_style = workbook.add_format({'font_name': 'Arial', 'bold': False, 'font_size': 10, 'valign': 'vcenter', 'font_color': '#666666'})
		level_2_number = workbook.add_format(
			{'font_name': 'Arial', 'bold': False, 'font_size': 10, 'valign': 'vcenter', 'font_color': '#666666', 'num_format': '#,##0.00'})

		company_name_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'font_size': 16, 'font_color': '#666666'})
		period_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'font_size': 11, 'font_color': '#666666'})
		note_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'font_size': 11, 'font_color': '#666666'})
		signature_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'bottom', 'font_size': 11, 'font_color': '#666666'})
		name_signature_style = workbook.add_format(
			{'font_name': 'Arial', 'font_size': 11, 'font_color': '#666666'})

		# Set the first column width to 50
		sheet.set_column(0, 0, 50)
		sheet.set_column(1, 1, 14)
		sheet.set_column(2, 2, 13)
		sheet.set_column(3, 3, 12)
		sheet.set_row(0, 30)

		period = self._get_report_name() + ' DEL ' + options.get('date').get('date_from') + ' AL ' + options.get('date').get('date_to')

		sheet.merge_range(0, 0, 0, 3, self.env.company.name, company_name_style)
		sheet.set_row(1, 20)
		sheet.merge_range(1, 0, 1, 3, period, period_style)
		sheet.merge_range(2, 0, 2, 3, '(Valores expresados en dólares de los Estados Unidos de America)', note_style)

		y_offset = 3
		headers, lines = self.with_context(no_format=True, print_mode=True, prefetch_fields=False)._get_table(options)

		# col_one = list(filter(lambda item: item['position'] == 1, lines))

		for y in range(0, len(lines)):
			level = lines[y].get('level')
			if level == 0:
				y_offset += 1
				style = level_0_style
				number_style = level_0_number
			elif level == 1:
				style = level_1_style
				number_style = level_1_number
			elif level == 2:
				style = level_2_style
				number_style = level_2_number

			# write the first column, with a specific style to manage the indentation
			if lines[y].get('class') != 'total':
				cell_type, cell_value = self._get_cell_type_value(lines[y])

				if cell_type == 'date':
					sheet.write_datetime(y + y_offset, 0, cell_value, date_default_style)
				else:
					sheet.write(y + y_offset, 0, cell_value, style)

			# write all the remaining cells
			if lines[y].get('class') != 'total':
				for x in range(1, len(lines[y]['columns']) + 1):
					cell_type, cell_value = self._get_cell_type_value(lines[y]['columns'][x - 1])

					if cell_type == 'number' and level == 0:
						sheet.write_number(y + y_offset, x + lines[y].get('colspan', 1) + 1, cell_value, number_style)

					if cell_type == 'number' and level == 2:
						sheet.write_number(y + y_offset, x + lines[y].get('colspan', 1) - 1, cell_value, number_style)

					if cell_type == 'number' and level == 1:
						sheet.write_number(y + y_offset, x + lines[y].get('colspan', 1), cell_value, number_style)

		sheet.merge_range(41, 0, 41, 3, 'F._________________                         '
										'F._________________                        '
										'F._________________', signature_style)

		sheet.merge_range(42, 0, 42, 3, '     Representante Legal                                   '
										'Contador                                                    '
										'Auditor ', name_signature_style)

		workbook.close()
		output.seek(0)
		generated_file = output.read()
		output.close()

		return generated_file

	def _balance_sheet_xlsx(self, options):
		"""
		Generates the excel file of the balance sheet report with the same format as the pdf file
		"""
		output = io.BytesIO()
		workbook = xlsxwriter.Workbook(output, {
			'in_memory': True,
			'strings_to_formulas': False,
		})
		sheet = workbook.add_worksheet(self._get_report_name()[:31])

		sheet.set_print_scale(95)
		sheet.set_landscape()
		sheet.set_paper(1)
		sheet.center_horizontally()
		# sheet.set_footer('&LF____________________&CF____________________&RF____________________')

		date_default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 12, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})

		level_0_style = workbook.add_format(
			{'font_name': 'Arial', 'bold': True, 'text_wrap': True, 'font_size': 11, 'valign': 'vcenter', 'bottom': 6, 'font_color': '#666666'})
		level_0_number = workbook.add_format(
			{'font_name': 'Arial', 'bold': False, 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'font_color': '#666666', 'num_format':
				'#,##0.00'})

		level_1_style = workbook.add_format(
			{'font_name': 'Arial', 'text_wrap': True, 'bold': True, 'font_size': 10, 'valign': 'vcenter', 'font_color': '#666666'})
		level_1_number = workbook.add_format(
			{'font_name': 'Arial', 'bold': False, 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'font_color': '#666666', 'num_format':
				'#,##0.00'})

		level_2_style = workbook.add_format(
			{'font_name': 'Arial', 'text_wrap': True, 'bold': False, 'font_size': 10, 'valign': 'vcenter', 'font_color': '#666666'})
		level_2_number = workbook.add_format(
			{'font_name': 'Arial', 'bold': False, 'font_size': 10, 'valign': 'vcenter', 'font_color': '#666666', 'num_format': '#,##0.00'})

		company_name_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'font_size': 16, 'font_color': '#666666'})
		period_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'font_size': 11, 'font_color': '#666666'})
		note_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'font_size': 11, 'font_color': '#666666'})
		signature_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'bottom', 'font_size': 11, 'font_color': '#666666'})

		name_signature_style = workbook.add_format({'font_name': 'Arial', 'font_size': 11, 'font_color': '#666666'})

		# Set the first column width to 50
		sheet.set_column(0, 0, 40)
		sheet.set_column(1, 1, 10)
		sheet.set_column(2, 2, 13)
		sheet.set_column(3, 3, 40)
		sheet.set_column(4, 4, 10)
		sheet.set_column(5, 5, 13)
		sheet.set_row(0, 25)

		period = self._get_report_name() + ' DEL ' + options.get('date').get('date_from') + ' AL ' + options.get('date').get('date_to')

		sheet.merge_range(0, 0, 0, 5, self.env.company.name, company_name_style)
		sheet.set_row(1, 20)
		sheet.merge_range(1, 0, 1, 5, period, period_style)
		sheet.merge_range(2, 0, 2, 5, '(Valores expresados en dólares de los Estados Unidos de America)', note_style)

		y_offset = 3
		z_offset = 3
		headers, lines = self.with_context(no_format=True, print_mode=True, prefetch_fields=False)._get_table(options)

		col_one = list(filter(lambda item: item['position'] == 1, lines))
		col_two = list(filter(lambda item: item['position'] == 2, lines))

		for y in range(0, len(col_one)):
			level = col_one[y].get('level')
			if level == 0:
				y_offset += 1
				style = level_0_style
				number_style = level_0_number
			elif level == 1:
				style = level_1_style
				number_style = level_1_number
			elif level == 2:
				style = level_2_style
				number_style = level_2_number

			# write the first column, with a specific style to manage the indentation
			if col_one[y].get('class') != 'total':
				cell_type, cell_value = self._get_cell_type_value(col_one[y])

				if cell_type == 'date':
					sheet.write_datetime(y + y_offset, 0, cell_value, date_default_style)
				else:
					sheet.write(y + y_offset, 0, cell_value, style)

			# write all the remaining cells
			if col_one[y].get('class') != 'total':
				for x in range(1, len(col_one[y]['columns']) + 1):
					cell_type, cell_value = self._get_cell_type_value(col_one[y]['columns'][x - 1])

					if cell_type == 'number' and level == 0 and col_one[y].get('name') == 'TOTAL ACTIVO':
						sheet.write_number(y + y_offset, x + col_one[y].get('colspan', 1), cell_value, number_style)

					if cell_type == 'number' and level == 2:
						sheet.write_number(y + y_offset, x + col_one[y].get('colspan', 1) - 1, cell_value, number_style)

					if cell_type == 'number' and level == 1:
						sheet.write_number(y + y_offset, x + col_one[y].get('colspan', 1), cell_value, number_style)
			else:
				y_offset -= 1

		# Imprime la Segunda columna del fichero Excel.
		for y in range(0, len(col_two)):
			level = col_two[y].get('level')
			if level == 0:
				z_offset += 1
				style = level_0_style
				number_style = level_0_number
			elif level == 1:
				style = level_1_style
				number_style = level_1_number
			elif level == 2:
				style = level_2_style
				number_style = level_2_number

			# write the first column, with a specific style to manage the indentation
			if col_two[y].get('class') != 'total':
				cell_type, cell_value = self._get_cell_type_value(col_two[y])

				if cell_type == 'date':
					sheet.write_datetime(y + z_offset, 3, cell_value, date_default_style)
				else:
					sheet.write(y + z_offset, 3, cell_value, style)

			# write all the remaining cells
			if col_two[y].get('class') != 'total':
				for x in range(1, len(col_two[y]['columns']) + 1):
					cell_type, cell_value = self._get_cell_type_value(col_two[y]['columns'][x - 1])

					if cell_type == 'number' and level == 0 and 'CAPITAL' in col_two[y].get('name'):
						sheet.write_number(y + z_offset, x + 3 + col_two[y].get('colspan', 1), cell_value, number_style)

					if cell_type == 'number' and level == 2:
						sheet.write_number(y + z_offset, x + 3 + col_two[y].get('colspan', 1) - 1, cell_value, number_style)

					if cell_type == 'number' and level == 1:
						sheet.write_number(y + z_offset, x + 3 + col_two[y].get('colspan', 1), cell_value, number_style)
			else:
				z_offset -= 1

		sheet.merge_range(30, 0, 30, 5, 'F.____________________                                           '
										'F._________________                                                        '
										'F_________________', signature_style)

		sheet.merge_range(31, 0, 31, 5, '                Representante Legal                                                            '
										'Contador                                                                               '
										'Auditor ', name_signature_style)

		workbook.close()
		output.seek(0)
		generated_file = output.read()
		output.close()

		return generated_file

	def _checking_balance_xlsx(self, options):
		"""
		In this function the excel view of the trial balance is generated with the same format as the pdf document
		"""
		output = io.BytesIO()
		workbook = xlsxwriter.Workbook(output, {
			'in_memory': True,
			'strings_to_formulas': False,
		})
		sheet = workbook.add_worksheet(self._get_report_name()[:31])

		sheet.set_print_scale(95)
		sheet.set_landscape()
		sheet.set_paper(1)
		sheet.center_horizontally()

		date_default_style = workbook.add_format({'font_name': 'Arial', 'font_size': 10, 'font_color': '#666666', 'num_format': 'yyyy-mm-dd'})

		level_0_style = workbook.add_format(
			{'font_name': 'Arial', 'bold': True, 'text_wrap': True, 'font_size': 10, 'valign': 'vcenter', 'bottom': 6, 'font_color': '#666666'})
		level_0_number = workbook.add_format(
			{'font_name': 'Arial', 'bold': True, 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'font_color': '#666666', 'num_format':
				'#,##0.00'})

		level_1_style = workbook.add_format(
			{'font_name': 'Arial', 'text_wrap': True, 'bold': True, 'font_size': 10, 'valign': 'vcenter', 'font_color': '#666666'})
		level_1_number = workbook.add_format(
			{'font_name': 'Arial', 'bold': True, 'font_size': 10, 'align': 'center', 'valign': 'vcenter', 'font_color': '#666666', 'num_format':
				'#,##0.00'})

		level_2_style = workbook.add_format(
			{'font_name': 'Arial', 'text_wrap': True, 'bold': False, 'font_size': 10, 'valign': 'vcenter', 'font_color': '#666666'})
		level_2_number = workbook.add_format(
			{'font_name': 'Arial', 'bold': False, 'font_size': 10, 'valign': 'vcenter', 'font_color': '#666666', 'num_format': '#,##0.00'})

		company_name_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'font_size': 14, 'font_color': '#666666'})
		period_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'font_size': 11, 'font_color': '#666666'})
		note_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'vcenter', 'font_size': 11, 'font_color': '#666666'})
		signature_style = workbook.add_format(
			{'font_name': 'Arial', 'align': 'center', 'valign': 'bottom', 'font_size': 11, 'font_color': '#666666'})

		name_signature_style = workbook.add_format({'font_name': 'Arial', 'font_size': 11, 'font_color': '#666666'})

		# Set the first column width to 50
		sheet.set_column(0, 0, 40)
		sheet.set_column(1, 1, 10)
		sheet.set_column(2, 2, 13)
		sheet.set_column(3, 3, 40)
		sheet.set_column(4, 4, 10)
		sheet.set_column(5, 5, 13)
		sheet.set_row(0, 25)

		period = self._get_report_name() + ' DEL ' + options.get('date').get('date_from') + ' AL ' + options.get('date').get('date_to')

		sheet.merge_range(0, 0, 0, 5, self.env.company.name, company_name_style)
		sheet.set_row(1, 20)
		sheet.merge_range(1, 0, 1, 5, period, period_style)
		sheet.merge_range(2, 0, 2, 5, '(Valores expresados en dólares de los Estados Unidos de America)', note_style)

		y_offset = 3
		z_offset = 3
		headers, lines = self.with_context(no_format=True, print_mode=True, prefetch_fields=False)._get_table(options)

		col_one = list(filter(lambda item: item['position'] == 1, lines))
		col_two = list(filter(lambda item: item['position'] == 2, lines))

		for y in range(0, len(col_one)):
			level = col_one[y].get('level')
			if level == 0:
				y_offset += 1
				style = level_1_style
				number_style = level_0_number
			elif level == 1:
				style = level_1_style
				number_style = level_1_number
			elif level == 2:
				style = level_2_style
				number_style = level_2_number

			# write the first column, with a specific style to manage the indentation
			if col_one[y].get('class') != 'total':
				cell_type, cell_value = self._get_cell_type_value(col_one[y])

				if cell_type == 'date':
					sheet.write_datetime(y + y_offset, 0, cell_value, date_default_style)
				else:
					sheet.write(y + y_offset, 0, cell_value, style)

			# write all the remaining cells
			if col_one[y].get('class') != 'total':
				for x in range(1, len(col_one[y]['columns']) + 1):
					cell_type, cell_value = self._get_cell_type_value(col_one[y]['columns'][x - 1])

					if cell_type == 'number' and level == 0 and col_one[y].get('name') != 'ACTIVO':
						sheet.write_number(y + y_offset, x + col_one[y].get('colspan', 1), cell_value, number_style)

					if cell_type == 'number' and level == 2:
						sheet.write_number(y + y_offset, x + col_one[y].get('colspan', 1) - 1, cell_value, number_style)

					if cell_type == 'number' and level == 1:
						sheet.write_number(y + y_offset, x + col_one[y].get('colspan', 1), cell_value, number_style)
			else:
				y_offset -= 1

		# Imprime la Segunda columna del fichero Excel.
		for y in range(0, len(col_two)):
			level = col_two[y].get('level')
			if level == 0:
				z_offset += 1
				style = level_1_style
				number_style = level_0_number
			elif level == 1:
				style = level_1_style
				number_style = level_1_number
			elif level == 2:
				style = level_2_style
				number_style = level_2_number

			# write the first column, with a specific style to manage the indentation
			if col_two[y].get('class') != 'total':
				cell_type, cell_value = self._get_cell_type_value(col_two[y])

				if cell_type == 'date':
					sheet.write_datetime(y + z_offset, 3, cell_value, date_default_style)
				else:
					sheet.write(y + z_offset, 3, cell_value, style)

			# write all the remaining cells
			if col_two[y].get('class') != 'total':
				for x in range(1, len(col_two[y]['columns']) + 1):
					cell_type, cell_value = self._get_cell_type_value(col_two[y]['columns'][x - 1])

					if cell_type == 'number' and level == 0 and col_two[y].get('name') != 'PASIVO':
						sheet.write_number(y + z_offset, x + 3 + col_two[y].get('colspan', 1), cell_value, number_style)

					if cell_type == 'number' and level == 2:
						sheet.write_number(y + z_offset, x + 3 + col_two[y].get('colspan', 1) - 1, cell_value, number_style)

					if cell_type == 'number' and level == 1:
						sheet.write_number(y + z_offset, x + 3 + col_two[y].get('colspan', 1), cell_value, number_style)
			else:
				z_offset -= 1

		# sheet.merge_range(30, 0, 30, 5, 'F.____________________                                           '
		# 								'F._________________                                                        '
		# 								'F_________________', signature_style)
		#
		# sheet.merge_range(31, 0, 31, 5, '                Representante Legal                                                            '
		# 								'Contador                                                                               '
		# 								'Auditor ', name_signature_style)

		workbook.close()
		output.seek(0)
		generated_file = output.read()
		output.close()

		return generated_file

	def get_xlsx(self, options):
		"""
		The excel file is created in memory with the data obtained from Odoo
		"""
		if self.id == self.env.ref('b_custom_account_reports.result_state_report').id:
			return self._state_result_xlsx(options)

		if self.id == self.env.ref('b_custom_account_reports.report_balance_sheet').id:
			return self._balance_sheet_xlsx(options)

		if self.id == self.env.ref('b_custom_account_reports.expanded_balance_sheet_report').id:
			return self._checking_balance_xlsx(options)

	def _get_cell_type_value(self, cell):
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
	def _get_financial_line_report_line(self, options, financial_line, solver, groupby_keys):
		''' Create the report line for an account.financial.html.report.line record.
		:param options:             The report options.
		:param financial_line:      An account.financial.html.report.line record.
		:param solver_results:      An instance of the FormulaSolver class.
		:param groupby_keys:        The sorted encountered keys in the solver.
		:return:                    The dictionary corresponding to a line to be rendered.
		'''
		results = solver.get_results(financial_line)['formula']

		is_leaf = solver.is_leaf(financial_line)
		has_lines = solver.has_move_lines(financial_line)
		has_something_to_unfold = is_leaf and has_lines and bool(financial_line.groupby)

		# Compute if the line is unfoldable or not.
		is_unfoldable = has_something_to_unfold and financial_line.show_domain == 'foldable'

		# Compute the id of the report line we'll generate
		report_line_id = self._get_generic_line_id('account.financial.html.report.line', financial_line.id)

		# Compute if the line is unfolded or not.
		# /!\ Take care about the case when the line is unfolded but not unfoldable with show_domain == 'always'.
		if not has_something_to_unfold or financial_line.show_domain == 'never':
			is_unfolded = False
		elif financial_line.show_domain == 'always':
			is_unfolded = True
		elif financial_line.show_domain == 'foldable' and (report_line_id in options['unfolded_lines'] or options.get('unfold_all')):
			is_unfolded = True
		else:
			is_unfolded = False

		# Standard columns.
		columns = []
		for key in groupby_keys:
			amount = results.get(key, 0.0)
			columns.append({'name': self._format_cell_value(financial_line, amount), 'no_format': amount, 'class': 'number'})

		# Growth comparison column.
		if self._display_growth_comparison(options):
			columns.append(self._compute_growth_comparison_column(options,
																  columns[0]['no_format'],
																  columns[1]['no_format'],
																  green_on_positive=financial_line.green_on_positive
																  ))

		financial_report_line = {
			'id': report_line_id,
			'name': financial_line.name,
			'model_ref': ('account.financial.html.report.line', financial_line.id),
			'level': financial_line.level,
			'class': 'o_account_reports_totals_below_sections' if self.env.company.totals_below_sections else '',
			'columns': columns,
			'unfoldable': is_unfoldable,
			'unfolded': is_unfolded,
			'page_break': financial_line.print_on_new_page,
			'action_id': financial_line.action_id.id,
			'position': financial_line.position,
		}

		# Only run the checks in debug mode
		if self.user_has_groups('base.group_no_one'):
			# If a financial line has a control domain, a check is made to detect any potential discrepancy
			if financial_line.control_domain:
				if not financial_line._check_control_domain(options, results, self):
					# If a discrepancy is found, a check is made to see if the current line is
					# missing items or has items appearing more than once.
					has_missing = solver._has_missing_control_domain(options, financial_line)
					has_excess = solver._has_excess_control_domain(options, financial_line)
					financial_report_line['has_missing'] = has_missing
					financial_report_line['has_excess'] = has_excess
					# In either case, the line is colored in red.
					# The ids of the missing / excess report lines are stored in the options for the top yellow banner
					if has_missing:
						financial_report_line['class'] += ' alert alert-danger'
						options.setdefault('control_domain_missing_ids', [])
						options['control_domain_missing_ids'].append(financial_line.id)
					if has_excess:
						financial_report_line['class'] += ' alert alert-danger'
						options.setdefault('control_domain_excess_ids', [])
						options['control_domain_excess_ids'].append(financial_line.id)

		# Debug info columns.
		if self._display_debug_info(options):
			columns.append(self._compute_debug_info_column(options, solver, financial_line))

		# Custom caret_options for tax report.
		if self.tax_report and financial_line.domain and not financial_line.action_id:
			financial_report_line['caret_options'] = 'tax.report.line'

		return financial_report_line

	@api.model
	def _get_financial_total_section_report_line(self, options, financial_report_line):
		''' Create the total report line.
		:param options:                 The report options.
		:param financial_report_line:   The line dictionary created by the '_get_financial_line_report_line' method.
		:return:                        The dictionary corresponding to a line to be rendered.
		'''
		return {
			'id': self._get_generic_line_id('account.financial.html.report.line', None, parent_line_id=financial_report_line['id'], markup='total'),
			'name': _('Total') + ' ' + financial_report_line['name'],
			'level': financial_report_line['level'] + 1,
			'parent_id': financial_report_line['id'],
			'class': 'total',
			'columns': financial_report_line['columns'],
			'position': financial_report_line['position']
		}


class ExpandedBalanceSheetLine(models.Model):
	_inherit = "account.financial.html.report.line"

	position = fields.Integer(help="Indicates the position where it will be printed in the excel file")
