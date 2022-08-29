from odoo import fields, models, api, _


class CustomSheetBalance(models.Model):
	_inherit = "account.financial.html.report"

	filter_analytic = False

	def print_pdf(self, options):
		if self.id == self.env.ref('b_custom_account_reports.report_balance_sheet').id:

			report_name = 'financierosv_sucursal.report_balance_pdf'
			# report = self.env['ir.actions.report']._get_report_from_name(report_name)
			date_from = fields.Date.from_string(options.get('date').get('date_from'))
			date_to = fields.Date.from_string(options.get('date').get('date_to'))

			form = {
				'fechai': date_from,
				'fechaf': date_to,
				'date_year': 2022,
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
			return super(CustomSheetBalance, self).print_pdf(options=options)
