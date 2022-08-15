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


class Node:
    def __init__(self,codigo,name,level,parent,signo_negativo):
        self.childs=[]
        self.parent=parent
        self.codigo=codigo
        self.name=name
        self.level=level
        self.ref=None
        self.signo_negativo=signo_negativo

class report_account(models.Model):
    _inherit='account.account'
    #Grupos por nivel, no son campos normalizados por cuestiones de desempe;o 
    level_group1=fields.Char("Nievel de grupos 1")
    level_group2=fields.Char("Nievel de grupos 2")
    level_group3=fields.Char("Nievel de grupos 3")
    level_group4=fields.Char("Nievel de grupos 4")
    level_group5=fields.Char("Nievel de grupos 5")
    level_group6=fields.Char("Nievel de grupos 6")
    level_group7=fields.Char("Nievel de grupos 7")

class report_account_group(models.Model):
    _inherit='account.group'
    #Grupos por nivel, no son campos normalizados por cuestiones de desempe;o 
    signo_negativo=fields.Boolean("Signo Negativo")
    
class report_company(models.Model):
    _inherit='res.company'
    level_group1=fields.Integer("Nievel de grupos 1")
    level_group2=fields.Integer("Nievel de grupos 2")
    level_group3=fields.Integer("Nievel de grupos 3")
    level_group4=fields.Integer("Nievel de grupos 4")
    level_group5=fields.Integer("Nievel de grupos 5")
    level_group6=fields.Integer("Nievel de grupos 6")
    level_group7=fields.Integer("Nievel de grupos 7")
    contador=fields.Char("Contador")
    auditor=fields.Char("Auditor")
    representante=fields.Char("Representante Legal")


    def configurar_cuentas(self):
        for r in self:
            cuentas=self.env['account.account'].search([('company_id','=',r.id)])
            for c in cuentas:
                if r.level_group1>0:
                    if len(c.code)>r.level_group1:
                        c.write({'level_group1':c.code[:r.level_group1]})
                    else:
                        c.write({'level_group1':c.code})
                if r.level_group2>0:
                    if len(c.code)>r.level_group2:
                        c.write({'level_group2':c.code[:r.level_group2]})
                    else:
                        c.write({'level_group2':c.code})
                if r.level_group3>0:
                    if len(c.code)>r.level_group3:
                        c.write({'level_group3':c.code[:r.level_group3]})
                    else:
                        c.write({'level_group3':c.code})
                if r.level_group4>0:
                    if len(c.code)>r.level_group4:
                        c.write({'level_group4':c.code[:r.level_group4]})
                    else:
                        c.write({'level_group4':c.code})
                if r.level_group5>0:
                    if len(c.code)>r.level_group5:
                        c.write({'level_group5':c.code[:r.level_group5]})
                    else:
                        c.write({'level_group5':c.code})
                if r.level_group6>0:
                    if len(c.code)>r.level_group6:
                        c.write({'level_group6':c.code[:r.level_group6]})
                    else:
                        c.write({'level_group6':c.code})
                if r.level_group7>0:
                    if len(c.code)>r.level_group7:
                        c.write({'level_group7':c.code[:r.level_group7]})
                    else:
                        c.write({'level_group7':c.code})

                


                


class saldo_inicial(models.Model):
    _inherit='account.financial.html.report'
    nivel_interno=fields.Integer("Nivel a considerar")
    cuentas=fields.Char("Cuentas a considerar")
    bloquear=fields.Boolean("Bloquear")
    hide_if_empty=fields.Boolean("Ocultar items vacios")



    def crear_arbol(self):
        level0=Node('0','Root',0,None,False)
        levels=[]
        dic={}
        dicsignos={}
        self.ensure_one()
        levels.append(0)
        levels.append(self.company_id.level_group1)
        levels.append(self.company_id.level_group2)
        levels.append(self.company_id.level_group3)
        levels.append(self.company_id.level_group4)
        levels.append(self.company_id.level_group5)
        levels.append(self.company_id.level_group6)
        levels.append(self.company_id.level_group7)
        groups=self.env['account.group'].search([('company_id','=',self.company_id.id)],order='code_prefix_start asc')
        for g in groups:
            dic[g.code_prefix_start]=g.name
            dicsignos[g.code_prefix_start]=g.signo_negativo
        cuentas=self.env['account.account'].search([('company_id','=',self.company_id.id)],order='code asc')
        for g in cuentas:
            dic[g.code]=g.name
        for c,n in dic.items():
            if len(c)==self.company_id.level_group1:
                node=self.crearnode(c,n,1,level0,dic,levels,dicsignos[c])
                level0.childs.append(node)
        return level0

    def crearnode(self,code,name,level,parent,dic,levels,signo):
        node=Node(code,name,level,parent,signo)
        if level<7:
            for c,n in dic.items():
                if len(c)==levels[level+1] and c[:levels[level]]==code:
                    nc=self.crearnode(c,n,level+1,node,dic,levels,signo)
                    node.childs.append(nc)
        return node
        
        




    def crear_structura(self):
        for r in self:
            if not r.bloquear:
                r.line_ids.unlink()
                node=r.crear_arbol()
                if not r.cuentas or r.cuentas=='':
                    for n in node.childs:
                        r.crear_linea(n,r,True)
                else:
                    cuentas=r.cuentas.split(',')
                    diccuentas={}
                    r.fill_dic_cuentas(node,diccuentas)
                    for c in cuentas:
                        if diccuentas[c]:
                            r.crear_linea(diccuentas[c],r,True)

    def fill_dic_cuentas(self,node,diccuentas):
        diccuentas[node.codigo]=node
        for n in node.childs:
            self.fill_dic_cuentas(n,diccuentas)


    def crear_linea(self,node,report,root):
        dic={}
        dic['name']=node.codigo+'-'+node.name
        dic['code']='RL'+str(report.id)+'_'+node.codigo
        dic['level']=node.level
        dic['figure_type']='float'
        dic['hide_if_empty']=report.hide_if_empty
        if root==True:
            dic['financial_report_id']=report.id
        if node.parent:
            if node.parent.ref:
                dic['parent_id']=node.parent.ref.id
        dic['show_domain']='foldable'
        if report.nivel_interno==node.level:
            if node.signo_negativo==True:
                dic['formulas']='-sum'
            else:
                dic['formulas']='sum'
            dic['groupby']='account_id'
            dic['domain']="[('account_id.level_group"+str(node.level)+"','=','"+node.codigo+"')]"
        else:
            text=''
            separator=''
            for e in node.childs:
                text+=separator+'RL'+str(report.id)+'_'+e.codigo
                separator='+'
            dic['formulas']=text
        ref=self.env['account.financial.html.report.line'].create(dic)
        node.ref=ref
        if report.nivel_interno>node.level:
            for e in node.childs:
                self.crear_linea(e,report,False)
    
    

        



    
    

    

