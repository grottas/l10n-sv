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
    x_activo=fields.Char('Dominio para indentificar activos')
    x_pasivo=fields.Char('Dominio para indentificar pasivo')
    x_capital=fields.Char('Dominio para indentificar capital')
    x_ingresos=fields.Char('Dominio para indentificar ingresos')
    x_egresos=fields.Char('Dominio para indentificar egresos')
    x_cierre=fields.Char('Dominio para indentificar activos')
    x_signos=fields.One2many(comodel_name='x_signos',inverse_name='x_company_id',string='Signos')


class saldo_inicial(models.Model):
    _name='x_signos'
    _description='Signos'
    x_name=fields.Char('Codigo cuenta')
    x_negativo=fields.Boolean('Negativo')
    x_company_id=fields.Many2one(comodel_name='res.company',string='Company')

    

    

