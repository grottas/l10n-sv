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
import uuid
from datetime import datetime, timedelta,date
from collections import OrderedDict
from odoo import api, fields, models,_
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval
_logger = logging.getLogger(__name__)


def numero_to_letras(numero):
    """
    Funciones para convertir las letas a numeros
    """
    indicador = [("",""),("MIL","MIL"),("MILLON","MILLONES"),("MIL","MIL"),("BILLON","BILLONES")]
    entero = int(numero)
    decimal = int(round((numero - entero)*100))
    #print 'decimal : ',decimal 
    contador = 0
    numero_letras = ""
    _logger.info('ENTERO:'+str(entero))
    while entero >0:
        a = entero % 1000
        if contador == 0:
            en_letras = convierte_cifra(a,1).strip()
            _logger.info('letras 1:'+en_letras)
        else :
            en_letras = convierte_cifra(a,0).strip()
            _logger.info('letras 2:'+en_letras)
        if a==0:
            numero_letras = en_letras+" "+numero_letras
            _logger.info('letras 3:'+numero_letras)
        elif a==1:
            if contador in (1,3):
                numero_letras = indicador[contador][0]+" "+numero_letras
                _logger.info('letras 4:'+numero_letras)
            else:
                numero_letras = en_letras+" "+indicador[contador][0]+" "+numero_letras
                _logger.info('letras 5:'+numero_letras)
        else:
            numero_letras = en_letras+" "+indicador[contador][1]+" "+numero_letras
            _logger.info('letras 6:'+numero_letras)
        numero_letras = numero_letras.strip()
        contador = contador + 1
        entero = int(entero / 1000)
    numero_letras = numero_letras+" CON " + str(decimal) +"/100"
    return numero_letras
 

def convierte_cifra(numero,sw):
    lista_centana = ["",("CIEN","CIENTO"),"DOSCIENTOS","TRESCIENTOS","CUATROCIENTOS","QUINIENTOS","SEISCIENTOS","SETECIENTOS","OCHOCIENTOS","NOVECIENTOS"]
    lista_decena = ["",("DIEZ","ONCE","DOCE","TRECE","CATORCE","QUINCE","DIECISEIS","DIECISIETE","DIECIOCHO","DIECINUEVE"),
                    ("VEINTE","VEINTIUNO","VEINTIDOS","VEINTITRES","VEINTICUATRO","VEINTICINCO","VEINTISEIS","VEINTISIETE","VEINTIOCHO","VEINTINUEVE")
                    ,("TREINTA","TREINTA Y "),("CUARENTA" , "CUARENTA Y "),
                    ("CINCUENTA" , "CINCUENTA Y "),("SESENTA" , "SESENTA Y "),
                    ("SETENTA" , "SETENTA Y "),("OCHENTA" , "OCHENTA Y "),
                    ("NOVENTA" , "NOVENTA Y ")
                ]
    lista_unidad = ["",("UN" , "UNO"),"DOS","TRES","CUATRO","CINCO","SEIS","SIETE","OCHO","NUEVE"]
    centena = int (numero / 100)
    decena = int((numero -(centena * 100))/10)
    unidad = int(numero - (centena * 100 + decena * 10))
    #print "centena: ",centena, "decena: ",decena,'unidad: ',unidad
    texto_centena = ""
    texto_decena = ""
    texto_unidad = ""
    #Validad las centenas
    texto_centena = lista_centana[centena]
    if centena == 1:
        if (decena + unidad)!=0:
            texto_centena = texto_centena[1]
        else :
            texto_centena = texto_centena[0]
    #Valida las decenas
    texto_decena = lista_decena[decena]
    if ((decena == 1) or (decena == 2)):
         texto_decena = texto_decena[unidad]
    elif decena > 2 :
        if unidad != 0 :
            texto_decena = texto_decena[1]
        else:
            texto_decena = texto_decena[0]
    #Validar las unidades
    #print "texto_unidad: ",texto_unidad
    if decena != 1:
        texto_unidad = lista_unidad[unidad]
        if unidad == 1:
            texto_unidad = texto_unidad[sw]
    return "%s %s %s" %(texto_centena,texto_decena,texto_unidad)


def calculo_letras(campo):
    cadena = list(campo)
    a = []
    for record in cadena: 
        if record=='0':
            a.append('cero')
        if record=='1':
            a.append('uno')
        if record=='2':
            a.append('dos')
        if record=='3':
            a.append('tres')
        if record=='4':
            a.append('cuatro')
        if record=='5':
            a.append('cinco')
        if record=='6':
            a.append('seis')
        if record=='7':
            a.append('siete')
        if record=='8':
            a.append('ocho')
        if record=='9':
            a.append('nueve')
        if record=='-':
            a.append('-')
            
    str1  = ' '.join(a)
    return str1


class caja_chica(models.Model):
    """
    Definicion de la caja chica
    """
    _name = 'odoosv.cajachica'
    _description='Caja Chica'
    #activo_id=fields.Many2one(comodel_name='account.asset.asset', string='Activo')
    vale_ids=fields.One2many(comodel_name='odoosv.vale_caja',inverse_name='caja_id', string='Pagos')
    monto_comprometido=fields.Float("Monto comprometido en Vales",compute='calcularvales')
    sv_total = fields.Float('Total de pagos',compute='_end_balance2',store=True)
    sv_saldo = fields.Float("Saldo de la caja",compute='_end_balance2',store=True)
    recalcular=fields.Integer("Calculando",default='0')
    grupo=fields.Char("Grupo de partidas")
    name = fields.Char("Caja chica")
    journal_id = fields.Many2one('account.journal',string='Libro asociado',help='Libro asociado')
    account_id = fields.Many2one(related='journal_id.default_account_id', string="cuenta a utilizar")
    user_id = fields.Many2one('res.users',string='Responsable',help='Responsable')
    partner_id = fields.Many2one('res.partner',string='Proveedor asociado',help='Proveedor asociado')
    sv_monto_inicial = fields.Float("Monto inicial")
    line_ids = fields.One2many('account.payment','sv_cajachica_id','Pagos realizados')
    sv_fecha_apertura = fields.Date("Fecha de apertura")
    sv_fecha_cierre = fields.Date("Fecha de cierre")
    state = fields.Selection([('draft','Borrador'), ('open','Abierto'),('closed','Cerrado')],default='draft')
    pagos_por_liquidacion=fields.Boolean("Pagos por liquidacion",related='journal_id.pagos_por_liquidacion')

    #pagos para cerrar caja
    payment_id=fields.Many2one('account.payment',string='Pago asociado',help='Pago asociado')
    invoice_ids=fields.Many2many('account.move',string="Facturas")
    account_dif_id=fields.Many2one('account.account',string='Cuenta de diferencia',help='Cuenta de diferencia')
    move_id=fields.Many2one('account.move',string="Partida de Cierre")


    def cerrar_por_liquidacion(self):
        for r in self:
            partida={}
            partida['name']='/'
            partida['ref']='Liquidacion de caja'
            journal_id=r.journal_id.id
            partida['journal_id']=journal_id
            partida['company_id']=self.env.user.company_id.id
            partida['move_type']='entry'
            lines=[]
            total=r.payment_id.amount
            lineap={}
            lineap['name']=r.name
            if r.payment_id:
                lineap['partner_id']=r.payment_id.partner_id.id
            lineap['account_id']=r.payment_id.destination_account_id.id
            lineap['debit']=0
            lineap['credit']=r.payment_id.amount
            linea1=(0,0,lineap)
            lines.append(linea1)
            for f in r.invoice_ids:
                linea={}
                linea['name']=f.tipo_documento_id.name+' '+f.doc_numero
                if f.partner_id:
                    linea['partner_id']=f.partner_id.id                
                linea['account_id']=f.partner_id.property_account_payable_id.id
                linea['debit']=f.amount_residual
                linea['credit']=0.0        
                linea2=(0,0,linea)
                lines.append(linea2)
                total=total-f.amount_residual
            if total>0:
                linead={}
                linead['name']=r.name+ " Remanente"
                linead['account_id']=r.account_dif_id.id
                linead['debit']=total
                linead['credit']=0.0
                linea3=(0,0,linead)
                lines.append(linea3)
            partida['line_ids']=lines
            move=self.env['account.move'].create(partida)
            move.action_post()
            r.move_id=move.id
            r.state='closed'
            for f in r.invoice_ids:
                namef=f.tipo_documento_id.name+' '+f.doc_numero
                for l in move.line_ids:                    
                    if namef==l.name:
                        f.js_assign_outstanding_line(l.id)

    def open_cc(self):
        for cc in self:
            cc.state='open'
            #cc.sv_fecha_apertura=fields.Date.today

    def close_cc(self):
        for cc in self:
            cc.state='closed'
            #cc.sv_fecha_cierre=fields.Date.today
    
    def agrupar_partidas(self):
        for r in self:
            grupo=uuid.uuid4().hex
            for v in r.vale_ids:
                for i in v.factura_ids:
                    move=i.move_id
                    move.grupo=grupo
                for p in v.pago_ids:
                    lst=self.env['account.move.line'].search([('payment_id','=',p.id)])
                    for l in lst:
                        l.move_id.grupo=grupo
    
    
    def refresh(self):
        for r in self:
            r.recalcular=r.recalcular+1
    
    @api.depends('line_ids', 'sv_monto_inicial','recalcular')
    def _end_balance2(self):
        self.ensure_one()
        total=0.0
        for line in self.line_ids:
            if ((line.state!='draft') and (line.state!='cancelled')):
                total=total+line.amount
        self.sv_total = total
        self.sv_saldo = self.sv_monto_inicial - self.sv_total
    
    @api.depends('vale_ids')
    def calcularvales(self):
        for r in self:
            monto=0.0
            for v in r.vale_ids:
                if (v.state=='Presentado') or (v.state=='Autorizado') or (v.state=='Liquidado'):
                    monto=monto+v.monto
            r.monto_comprometido=monto
    
    def agregarvale(self):
        self.ensure_one()
        compose_form = self.env.ref('sv_cajachica.odoosv_vale_form', False)
        ctx = dict(
            default_caja_id=self.id
        )
        return {
            'name': 'Nuevo Vale',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'odoosv.vale_caja',
            'views': [(compose_form.id, 'form')],
            'target': 'new',
            'view_id': 'compose_form.id',
            'flags': {'action_buttons': True},
            'context': ctx
        }
    
    def close_cc(self):
        for cc in self:
            cc.state='closed'
            cc.sv_fecha_cierre=date.today()
            #creando la nueva con los vales no liquidados
            dic={}
            dic['name']=cc.name+' COMPLEMENTO'
            dic['journal_id']=cc.journal_id.id
            dic['user_id']=cc.user_id.id
            dic['partner_id']=cc.partner_id.id
            dic['sv_monto_inicial']=cc.sv_monto_inicial
            dic['sv_fecha_apertura']=cc.sv_fecha_cierre
            nueva=self.env['odoosv.cajachica'].create(dic)
            for l in cc.vale_ids:
                if l.state=='Borrador' or l.state=='Autorizado':
                    if l.monto_ejecutado==0.0:
                        l.write({'caja_id':nueva.id})
    
    
class caja_chica_factura(models.Model):
    """
    Asociacion del vale a la caja chica
    """
    _inherit='account.move'
    vale_id=fields.Many2one(comodel_name='odoosv.vale_caja', string=' Vale Caja chica')



class caja_chica_pago(models.Model):
    """
    Enlaza el pago al vale de caja chica
    """
    _inherit='account.payment'
    vale_id=fields.Many2one(comodel_name='odoosv.vale_caja', string=' Vale Caja chica')
    utiliza_vales=fields.Boolean(string='Utiliza vales',related='journal_id.utiliza_vales')
    sv_caja_chica = fields.Boolean(related='journal_id.sv_caja_chica', store=True, string="Caja chica")
    sv_cajachica_id= fields.Many2one('odoosv.cajachica',string='Caja chica asociada',help='Caja chica asociada')
    #renta=fields.Float('Renta',compute='calcular_renta',store=False)
    total=fields.Float('Total',compute='calcular_renta',store=False)
    
    @api.depends('amount')
    def calcular_renta(self):
        for r in self:
            r.total=r.amount
    
class caja_chica_pago_register(models.TransientModel):
    """
    Modelo transitorio para registrar el pago
    """
    _inherit='account.payment.register'
    sv_caja_chica = fields.Boolean(related='journal_id.sv_caja_chica', store=True, string="Caja chica")
    sv_cajachica_id= fields.Many2one('odoosv.cajachica',string='Caja chica asociada',help='Caja chica asociada')
    vale_id=fields.Many2one(comodel_name='odoosv.vale_caja', string=' Vale Caja chica')
    utiliza_vales=fields.Boolean(string='Utiliza vales',related='journal_id.utiliza_vales')

    def _create_payment_vals_from_wizard(self):
        payment_vals = super(caja_chica_pago_register,self)._create_payment_vals_from_wizard()
        payment_vals['sv_cajachica_id']=self.sv_cajachica_id.id
        if self.vale_id:
            payment_vals['vale_id']=self.vale_id.id
        return payment_vals

    
class caja_chica_journal(models.Model):
    """
    Modifica el diario para especificar si permite vales y que usuarios 
    puede utilizar y aprobar la caja chica
    """
    _inherit='account.journal'
    sv_caja_chica = fields.Boolean("Caja chica")
    pagos_por_liquidacion=fields.Boolean("Pagos por liquidacion")
    usuario_ids=fields.One2many(comodel_name='odoosv.usuario_caja',inverse_name='journal_id', string='Pagos')
    usuarios_permitido_ids=fields.Many2many('res.users', 'journal_user_rel', 'journal_id', 'user_id', 'Usuarios')
    utiliza_vales=fields.Boolean(string='Utiliza vales')
    vale_seq=fields.Many2one(comodel_name='ir.sequence', string='Numeración de vales')
    tipo_partida=fields.Char("Tipo de Partidas")

class caja_chica_user(models.Model):
    """
    Indica que usuarios tienen permitido utilizar una caja chica
    """
    _inherit='res.users'
    caja_permitida_ids=fields.Many2many('account.journal', 'journal_user_rel', 'user_id', 'journal_id', 'Cajas')
    
class caja_usuario(models.Model):
    """
    Indica que usuarios tienen permitido aprobar vales de caja chica y que monto
    """
    _name ='odoosv.usuario_caja'
    name = fields.Char(string="Usuario",related='usuario_id.partner_id.name')
    usuario_id=fields.Many2one(comodel_name='res.users', string='Usuario',track_visibility=True)
    monto=fields.Float("Monto para aprobación")
    journal_id=fields.Many2one(comodel_name='account.journal', string='Journal',track_visibility=True)

    
class vale_caja(models.Model):
    """
    Vales de caja chica
    se enlazan con la caja chica y con los insumos.
    """
    _name ='odoosv.vale_caja'
    _inherit= ['mail.thread']
    name = fields.Char(string="Numero Vale")
    fecha=fields.Date("Fecha",track_visibility=True)
    usuario_id=fields.Many2one(comodel_name='res.users', string='Usuario',track_visibility=True)
    monto=fields.Float("Monto",track_visibility=True)
    observacion=fields.Text("Observacion",track_visibility=True)
    state=fields.Selection(selection=[('Borrador', 'Borrador')
                                    ,('Presentado', 'Presentado')
                                    ,('Autorizado', 'Autorizado')
                                    ,('Rechazado', 'Rechazado')
                                    ,('Liquidado', 'Liquidado')],default='Borrador',string='Estado',track_visibility=True)
    monto_reintegro=fields.Float("Monto a reintegrar",compute='calcular')
    monto_ejecutado=fields.Float("Monto ejecutado",compute='calcular')
    pago_ids=fields.One2many(comodel_name='account.payment',inverse_name='vale_id', string='Pagos')
    factura_ids=fields.One2many(comodel_name='account.move',inverse_name='vale_id', string='Facturas')
    caja_id=fields.Many2one(comodel_name='odoosv.cajachica', string='Caja chica')
    presentar_id=fields.Many2one(comodel_name='odoosv.usuario_caja', string='Presentar',track_visibility=True)
    autoriza_id=fields.Many2one(comodel_name='res.users', string='Autoriza',track_visibility=True)
    monto_letras=fields.Char("Monto en letras",compute='fill_letras')
    #planunidad_id=fields.Many2one(comodel_name='odoosv.planunidad', string='Plan')
    #actividad_id = fields.Many2one(comodel_name='odoosv.poaactividad',required=True, string="Actividad", store = True)
    #bien_id = fields.Many2one(comodel_name='odoosv.insumo', required=True,string="Bien o Servicio")
    #caja_permitida_ids=fields.Many2many('account.journal', related='usuario_id.caja_permitida_ids', string='Cajas')
    #caja_domain = fields.Char(compute="_compute_external_company_domain",readonly=True, store=False)

    @api.onchange('usuario_id')
    def _compute_external_company_domain(self):
        if self.usuario_id:
            lista=[]
            for r in self.usuario_id.caja_permitida_ids:
                lista.append(r.id)
            return {'domain': {'caja_id': [('state', '=', 'open'), ('journal_id', 'in', lista)]}}
        return {}
       
    
    @api.depends('monto')
    def fill_letras(self):
        for r in self:
            r.monto_letras=numero_to_letras(r.monto)
    
    
    
    @api.depends('monto','pago_ids')
    def calcular(self):
        for r in self:
            ejecutado=0.0
            for p in r.pago_ids:
                if ((p.state!='draft') and (p.state!='cancelled')):
                    ejecutado=ejecutado+p.amount
            r.monto_ejecutado=ejecutado
            r.monto_reintegro=r.monto-ejecutado
    
    def presentar(self):
        for r in self:
            r.state='Presentado'
            template = self.env.ref('sv_cajachica.caja_presentar')
            if template:
                self.env['mail.template'].browse(template.id).send_mail(r.id)
    
    def autorizar(self):
        for r in self:
            found=False
            for x in r.caja_id.journal_id.usuario_ids:
                if x.usuario_id.id==self.env.user.id:
                    if x.monto>=r.monto:
                        if r.usuario_id.id!=self.env.user.id:
                            r.state='Autorizado'
                            r.autoriza_id=self.env.user.id
                            found=True
                            r.name=r.caja_id.journal_id.vale_seq.next_by_id()
                        else:
                            raise ValidationError("El usuario que autoriza no puede ser el mismo del vale")
                    else:
                        raise ValidationError("El Monto es superior al que puede autorizar el usuario")
            if found==False:
                raise ValidationError("El Usuario no puede autorizar vales")
    
    def rechazar(self):
        for r in self:
            r.state='Rechazado'
            
    def liquidar(self):
        for r in self:
            r.state='Liquidado'
            for f in r.factura_ids:
                if f.state=='open':
                    dic={}
                    dic['journal_id']=r.caja_id.journal_id.id
                    dic['caja_id']=r.caja_id.id
                    dic['vale_id']=r.id
                    dic['sv_resumen']='Pago '+f.reference
                    dic['amount']=f.amount_total
                    dic['partner_id']=f.partner_id.id
                    dic['payment_type']='outbound'
                    dic['partner_type']='supplier'
                    dic['payment_method_id']=1
                    dic['invoice_ids']=[(6,0,[f.id])]
                    mod = self.env['account.payment']
                    id = mod.create(dic)
                    id.post()
    def abrir(self):
        for r in self:
            r.state='Autorizado'
    
    def agregarfactura(self):
        self.ensure_one()
        compose_form = self.env.ref('account.view_move_form', False)
        ctx = dict(
            default_move_type='in_invoice'
            ,move_type='in_invoice'
            ,journal_type='purchase'
            ,default_vale_id=self.id
        )
        return {
            'name': 'Nueva Factura',
            'type': 'ir.actions.act_window',
            'view_type': 'form',
            'view_mode': 'form',
            'res_model': 'account.move',
            'views': [(compose_form.id, 'form')],
            'target': 'new',
            'view_id': 'compose_form.id',
            'flags': {'action_buttons': True},
            'context': ctx
        }

