# -*- coding: utf-8 -*-
import time
from odoo import models, fields, api, tools

class odoosv_purchase_report_pdf(models.AbstractModel):
    _name = 'report.reportesv_sucursal.odoosv_purchase_report_pdf'
    _auto = False

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report'].\
            _get_report_from_name('reportesv_sucursal.odoosv_purchase_report_pdf')
        if data and data.get('form')\
            and  data.get('form').get('company_id')\
            and  data.get('form').get('date_year')\
            and  data.get('form').get('date_month'):
            docids = self.env['res.company'].browse(data['form']['company_id'][0])
        return {'doc_ids': self.env['wizard.sv.purchase.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['res.company'].browse(data['form']['company_id'][0]),
                'data': data,
                }

class odoosv_taxpayer_report_pdf(models.AbstractModel):
    _name = 'report.reportesv_sucursal.odoosv_taxpayer_report_pdf'
    _auto = False

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report'].\
            _get_report_from_name('reportesv_sucursal.odoosv_taxpayer_report_pdf')
        if data and data.get('form')\
            and  data.get('form').get('company_id')\
            and  data.get('form').get('date_year')\
            and  data.get('form').get('date_month'):
            docids = self.env['res.company'].browse(data['form']['company_id'][0])
        return {'doc_ids': self.env['wizard.sv.taxpayer.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['res.company'].browse(data['form']['company_id'][0]),
                'data': data,
                }

class odoosv_consumer_report_pdf(models.AbstractModel):
    _name = 'report.reportesv_sucursal.odoosv_consumer_report_pdf'
    _auto = False

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report'].\
            _get_report_from_name('reportesv_sucursal.odoosv_consumer_report_pdf')
        if data and data.get('form')\
            and  data.get('form').get('company_id')\
            and  data.get('form').get('date_year')\
            and  data.get('form').get('date_month'):
            docids = self.env['res.company'].browse(data['form']['company_id'][0])
        return {'doc_ids': self.env['wizard.sv.consumer.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['res.company'].browse(data['form']['company_id'][0]),
                'data': data,
                }

class odoosv_ticket_report_pdf(models.AbstractModel):
    _name = 'report.reportesv_sucursal.odoosv_ticket_report_pdf'
    _auto = False

    @api.model
    def _get_report_values(self, docids, data=None):
        report = self.env['ir.actions.report'].\
            _get_report_from_name('reportesv_sucursal.odoosv_ticket_report_pdf')
        if data and data.get('form')\
            and  data.get('form').get('company_id')\
            and  data.get('form').get('date_year')\
            and  data.get('form').get('date_month'):
            docids = self.env['res.company'].browse(data['form']['company_id'][0])
        return {'doc_ids': self.env['wizard.sv.ticket.report'].browse(data['ids']),
                'doc_model': report.model,
                'docs': self.env['res.company'].browse(data['form']['company_id'][0]),
                'data': data,
                }

