# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api, tools

class odoosv_balance_report_pdf(models.AbstractModel):
    _name = 'report.financierosv_sucursal.odoosv_balance_report_pdf'
    _auto = False

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report'].\
            _get_report_from_name('financierosv_sucursal.odoosv_balance_report_pdf')
        if data and data.get('form')\
            and  data.get('form').get('company_id')\
            and  data.get('form').get('date_year')\
            and  data.get('form').get('date_month'):
            docids = self.env['res.company'].browse(data['form']['company_id'][0])
        return {'doc_ids': self.env['wizard.sv.balance.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['res.company'].browse(data['form']['company_id'][0]),
                'data': data,
                }

class odoosv_mayor_report_pdf(models.AbstractModel):
    _name = 'report.financierosv_sucursal.odoosv_mayor_report_pdf'
    _auto = False

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report'].\
            _get_report_from_name('financierosv_sucursal.odoosv_mayor_report_pdf')
        if data and data.get('form')\
            and  data.get('form').get('company_id')\
            and  data.get('form').get('date_year')\
            and  data.get('form').get('date_month'):
            docids = self.env['res.company'].browse(data['form']['company_id'][0])
        return {'doc_ids': self.env['wizard.sv.mayor.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['res.company'].browse(data['form']['company_id'][0]),
                'data': data,
                }

class odoosv_resultado_report_pdf(models.AbstractModel):
    _name = 'report.financierosv_sucursal.odoosv_resultado_report_pdf'
    _auto = False

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report'].\
            _get_report_from_name('financierosv_sucursal.odoosv_resultado_report_pdf')
        if data and data.get('form')\
            and  data.get('form').get('company_id')\
            and  data.get('form').get('date_year')\
            and  data.get('form').get('date_month'):
            docids = self.env['res.company'].browse(data['form']['company_id'][0])
        return {'doc_ids': self.env['wizard.sv.resultado.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['res.company'].browse(data['form']['company_id'][0]),
                'data': data,
                }                

class odoosv_general_report_pdf(models.AbstractModel):
    _name = 'report.financierosv_sucursal.odoosv_general_report_pdf'
    _auto = False

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report'].\
            _get_report_from_name('financierosv_sucursal.odoosv_general_report_pdf')
        if data and data.get('form')\
            and  data.get('form').get('company_id')\
            and  data.get('form').get('date_year')\
            and  data.get('form').get('date_month'):
            docids = self.env['res.company'].browse(data['form']['company_id'][0])
        return {'doc_ids': self.env['wizard.sv.general.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['res.company'].browse(data['form']['company_id'][0]),
                'data': data,
                }

class odoosv_auxiliar_report_pdf(models.AbstractModel):
    _name = 'report.financierosv_sucursal.odoosv_auxiliar_report_pdf'
    _auto = False

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report'].\
            _get_report_from_name('financierosv_sucursal.odoosv_auxiliar_report_pdf')
        if data and data.get('form')\
            and  data.get('form').get('company_id')\
            and  data.get('form').get('date_year')\
            and  data.get('form').get('date_month'):
            docids = self.env['res.company'].browse(data['form']['company_id'][0])
        return {'doc_ids': self.env['wizard.sv.auxiliar.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['res.company'].browse(data['form']['company_id'][0]),
                'data': data,
                }            