# -*- coding: utf-8 -*-
##############################################################################
#
#    Odoo
#
##############################################################################
import base64
import json
import requests
import logging
import time
from datetime import datetime
from collections import OrderedDict
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
_logger = logging.getLogger(__name__)



class saldo_company(models.Model):
    _inherit='res.company'
    cuenta_cxc=fields.Many2one('account.account', string='Contrapartida de CXC para la carga')
    cuenta_cxp=fields.Many2one('account.account', string='Contrapartida de CXP para la carga')


class saldo_inicial(models.Model):
    _name='odoosv.saldo'
    _description='Saldo inicial'
    name=fields.Char("Nombre")
    account_id=fields.Many2one('account.account', required=True,string='Cuenta')
    partner_id=fields.Many2one('res.partner', required=False,string='Tecero')
    analytic_account_id=fields.Many2one('account.analytic.account', required=False,string='Cuenta analitica')
    debe=fields.Float("Debe",required=True)
    haber=fields.Float("Haber",required=True)
    company_id=fields.Many2one('res.company', required=False,string='Compania')

    def crear_partida(self):
        partida={}
        partida['name']='Saldos iniciales'
        partida['ref']='Saldos iniciales'
        journal_id=self.env['account.journal'].search([('type','=','general'),('company_id','=',self.env.user.company_id.id)],limit=1)
        partida['journal_id']=journal_id.id
        partida['company_id']=self.env.user.company_id.id
        partida['move_type']='entry'
        lines=[]
        for r in self:
            linea={}
            linea['name']=r.name
            if r.partner_id:
                linea['partner_id']=r.partner_id.id
            if r.analytic_account_id:
                linea['analytic_account_id']=r.analytic_account_id.id
            linea['account_id']=r.account_id.id
            linea['debit']=r.debe
            linea['credit']=r.haber            
            linea1=(0,0,linea)
            lines.append(linea1)
        partida['line_ids']=lines
        move=self.env['account.move'].create(partida)
        compose_form = self.env.ref('account.view_move_form', False)
        ctx = dict(
        )
        return {
            'name': 'Saldos iniciales',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'res_id': move.id,
            'views': [(compose_form.id, 'form')],
            'target': 'new',
            'view_id': 'compose_form.id',
            'flags': {'action_buttons': True},
            'context': ctx
        }
        

class saldo_inicial_cxc(models.Model):
    _name='odoosv.cxc'
    _description='Saldo inicial CXC'
    name=fields.Char("Nombre")
    fecha=fields.Date("Fecha")
    partner_id=fields.Many2one('res.partner', required=False,string='Tecero')
    company_id=fields.Many2one('res.company', required=False,string='Compania')
    monto=fields.Float("Monto total")
    saldo=fields.Float("Saldo")
    move_id=fields.Many2one('account.move', required=False,string='Movimiento')

    def crear_cxc(self):        
        for r in self:
            partida={}
            partida['name']='Saldos iniciales'
            partida['ref']=r.name
            partida['doc_numero']=r.name
            partida['invoice_date']=r.fecha
            journal_id=self.env['account.journal'].search([('type','=','sale'),('company_id','=',self.env.user.company_id.id)],limit=1)
            partida['journal_id']=journal_id.id
            partida['partner_id']=r.partner_id.id
            partida['company_id']=self.env.user.company_id.id
            documento_id=self.env['odoosv.fiscal.document'].search([('tipo_movimiento','=','out_invoice'),('company_id','=',self.env.user.company_id.id)],limit=1)
            partida['tipo_documento_id']=documento_id.id
            partida['move_type']='out_invoice'
            partida['nofiscal']=True
            lines=[]
            linea={}
            linea['name']='saldo inicial doc'+r.name+ ' monto:' +str(r.monto)+' saldo:'+str(r.saldo)
            linea['account_id']=self.env.user.company_id.cuenta_cxc.id
            linea['price_unit']=r.saldo
            linea['quantity']=1
            linea['exclude_from_invoice_tab']=False
            linea['debit']=0
            linea['credit']=r.saldo
            linea1=(0,0,linea)
            lines.append(linea1)

            linea={}
            linea['name']='saldo inicial doc'+r.name+ ' monto:' +str(r.monto)+' saldo:'+str(r.saldo)
            linea['account_id']=r.partner_id.property_account_receivable_id.id
            linea['exclude_from_invoice_tab']=True
            linea['debit']=r.saldo
            linea['credit']=0
            linea['partner_id']=r.partner_id.id
            linea2=(0,0,linea)
            lines.append(linea2)

            partida['line_ids']=lines
            move=self.env['account.move'].create(partida)
            r.write({'move_id':move.id})
        

    
class saldo_inicial_cxp(models.Model):
    _name='odoosv.cxp'
    _description='Saldo inicial CXP'
    name=fields.Char("Nombre")
    fecha=fields.Date("Fecha")
    partner_id=fields.Many2one('res.partner', required=False,string='Tecero')
    company_id=fields.Many2one('res.company', required=False,string='Compania')
    monto=fields.Float("Monto total")
    saldo=fields.Float("Saldo")
    move_id=fields.Many2one('account.move', required=False,string='Movimiento')

    def crear_cxp(self):        
        for r in self:
            partida={}
            partida['name']='Saldos iniciales'
            partida['ref']=r.name
            partida['doc_numero']=r.name
            partida['invoice_date']=r.fecha
            journal_id=self.env['account.journal'].search([('type','=','purchase'),('company_id','=',self.env.user.company_id.id)],limit=1)
            partida['journal_id']=journal_id.id
            partida['partner_id']=r.partner_id.id
            partida['company_id']=self.env.user.company_id.id
            documento_id=self.env['odoosv.fiscal.document'].search([('tipo_movimiento','=','in_invoice'),('company_id','=',self.env.user.company_id.id)],limit=1)
            partida['tipo_documento_id']=documento_id.id
            partida['move_type']='in_invoice'
            partida['nofiscal']=True
            lines=[]
            linea={}
            linea['name']='saldo inicial doc'+r.name+ ' monto:' +str(r.monto)+' saldo:'+str(r.saldo)
            linea['account_id']=self.env.user.company_id.cuenta_cxp.id
            linea['price_unit']=r.saldo
            linea['quantity']=1
            linea['exclude_from_invoice_tab']=False
            linea['debit']=r.saldo
            linea['credit']=0
            linea1=(0,0,linea)
            lines.append(linea1)

            linea={}
            linea['name']='saldo inicial doc'+r.name+ ' monto:' +str(r.monto)+' saldo:'+str(r.saldo)
            linea['account_id']=r.partner_id.property_account_payable_id.id
            linea['exclude_from_invoice_tab']=True
            linea['debit']=0
            linea['credit']=r.saldo
            linea['partner_id']=r.partner_id.id
            linea2=(0,0,linea)
            lines.append(linea2)

            partida['line_ids']=lines
            move=self.env['account.move'].create(partida)
            r.write({'move_id':move.id})
        



    

