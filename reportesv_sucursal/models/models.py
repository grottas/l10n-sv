import logging
from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import tools
import pytz
from pytz import timezone
from datetime import datetime, date, time, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo import exceptions
_logger = logging.getLogger(__name__)

class calculo_iva(models.Model):
	_name = "reportesv_sucursal.calculo_iva"
	_inherit = "mail.thread"
	_description='Calculo de impuestos'
	name=fields.Char("Calculo")
	anio=fields.Integer("Año")
	mes=fields.Selection(selection=[('1','Enero'),('2','Febrero'),('3','Marzo'),('4','Abril'),('5','Mayo'),('6','Junio'),('7','Julio'),('8','Agosto'),('9','Septiembre'),('10','Octubre'),('11','Noviembre'),('12','Diciembre')],string="Mes")
	fecha=fields.Date("Fecha de Cálculo")
	company_id=fields.Many2one(comodel_name='res.company', string='Empresa')
	compras=fields.One2many(comodel_name='reportesv_sucursal.iva_compras', string='Compras',inverse_name='calculo_id')
	contribuyentes=fields.One2many(comodel_name='reportesv_sucursal.iva_contribuyente', string='Contribuyentes',inverse_name='calculo_id')
	consumidores=fields.One2many(comodel_name='reportesv_sucursal.iva_consumidor', string='Consumidores',inverse_name='calculo_id')
	consumidores_full=fields.One2many(comodel_name='reportesv_sucursal.iva_consumidor_full', string='Consumidores Detalle',inverse_name='calculo_id')
	percibido=fields.One2many(comodel_name='reportesv_sucursal.iva_percibido', string='Percibido',inverse_name='calculo_id')
	percibido1=fields.One2many(comodel_name='reportesv_sucursal.iva_percibido1', string='Percibido1',inverse_name='calculo_id')

	def calcular(self):
		for r in self:
			r.write({'fecha':datetime.now()})
			company=self.env['res.company'].browse(r.company_id.id)
			self.env['reportesv_sucursal.iva_compras'].search([('anio','=',r.anio),('mes','=',r.mes)]).unlink()
			lst=company.get_purchase_details1(r.company_id.id,r.anio,r.mes)
			i=1
			for l in lst:
				dic={}
				dic['anio']=r.anio
				dic['mes']=r.mes
				dic['factura_id']=l.get('factura_id')
				dic['calculo_id']=r.id
				dic['correlativo']=i
				dic['dui']=l.get('dui')
				dic['nit']=l.get('nit')
				dic['nrc']=l.get('nrc')
				dic['fecha']=l.get('fecha')
				dic['numero']=l.get('factura')
				dic['proveedor']=l.get('proveedor')
				dic['nrc']=l.get('nrc')
				dic['importacion_bienes']=0.0
				customer=self.env['res.partner'].search([('vat','=',l.get('nrc'))],limit=1)
				if customer:
					dic['nit']=customer.nit
				if l.get('importacion') == True:
					dic['exento_interno']=0.0
					dic['exento_importacion']=l.get('exento')
					dic['gravado_interno']=0.0
					dic['gravado_importacion']=l.get('gravado')
				else:
					dic['exento_interno']=l.get('exento')
					dic['exento_importacion']=0.0
					dic['gravado_interno']=l.get('gravado')
					dic['gravado_importacion']=0.0
				dic['credito_fiscal']=l.get('iva')
				dic['retenido']=l.get('retenido')
				dic['percibido']=l.get('percibido')
				dic['excluido']=l.get('excluido')
				dic['terceros']=l.get('retencion3')
				dic['total_compra']=l.get('exento')+l.get('gravado')+l.get('iva')+l.get('retenido')+l.get('percibido')
				dic['tipo_documento_emitido']=l.get('tipod')

				dic['anexo']='3'
				dic['clase_doc']='1. Impreso por Imprenta o Ticket'
				factura=self.env['account.move'].browse(l.get('factura_id'))
			#	if factura:
			#		dic['tipo_documento_emitido']='05. Nota de Credito' if factura.move_type=='out_refund' else '03. Comprobante de Credito Fiscal'
			#	else:
			#		dic['tipo_documento_emitido']='03. Comprobante de Credito Fiscal' 

				self.env['reportesv_sucursal.iva_compras'].create(dic)
				i=i+1
			self.env['reportesv_sucursal.iva_contribuyente'].search([('anio','=',r.anio),('mes','=',r.mes)]).unlink()
			self.env['reportesv_sucursal.iva_consumidor'].search([('anio','=',r.anio),('mes','=',r.mes)]).unlink()
			self.env['reportesv_sucursal.iva_consumidor_full'].search([('anio','=',r.anio),('mes','=',r.mes)]).unlink()
			self.env['reportesv_sucursal.iva_percibido'].search([('anio','=',r.anio),('mes','=',r.mes)]).unlink()
			self.env['reportesv_sucursal.iva_percibido1'].search([('anio','=',r.anio),('mes','=',r.mes)]).unlink()

			lst=company.get_taxpayer_details(r.company_id.id,r.anio,r.mes,0)
			i=1
			for l in lst:
				dic={}
				dic['anio']=r.anio
				dic['mes']=r.mes
				dic['factura_id']=l.get('factura_id')
				dic['calculo_id']=r.id
				dic['sucursal']=''
				dic['correlativo']=i
				dic['correlativo']=i
				dic['fecha']=l.get('fecha')
				dic['numero']=l.get('factura')
				dic['serie']=l.get('serie')              #l.get('serie')
				dic['nit']=l.get('nit')
				dic['dui']=l.get('dui')
				dic['cliente']=l.get('cliente')
				dic['nrc']=l.get('nrc')
				dic['debito3']=0.0
				dic['venta3']=0.0
				customer=self.env['res.partner'].search([('vat','=',l.get('nrc'))],limit=1)
				if customer:
					dic['nit']=customer.nit
				dic['exento']=l.get('exento')
				dic['gravado']=l.get('gravado')
				dic['debito']=l.get('iva')
				dic['total_venta']=l.get('gravado')+l.get('exento')+l.get('iva')
				dic['retenido']=l.get('retenido')
				dic['percibido']=l.get('percibido')
				dic['total']=l.get('exento')+l.get('gravado')+l.get('iva')+l.get('retenido')+l.get('percibido')



				dic['anexo']='1'
				dic['clase_doc']='1. Impreso por Imprenta o Ticket'
				dic['numero_cortado']=l.get('factura')[8:len(l.get('factura'))] if (l.get('factura') and  len(l.get('factura'))>8) else l.get('factura')
				dic['numero_interno']=dic['numero_cortado']
				dic['resolucion']=''
				if factura:
					dic['tipo_documento_emitido']='05. Nota de Credito' if factura.move_type=='out_refund' else '03. Comprobante de Credito Fiscal'
				else:
					dic['tipo_documento_emitido']='03. Comprobante de Credito Fiscal' 
				self.env['reportesv_sucursal.iva_contribuyente'].create(dic)
				i=i+1
			
			lst=company.get_consumerfull_details(r.company_id.id,r.anio,r.mes,0)
			i=1
			for l in lst:
				dic={}
				dic['anio']=r.anio
				dic['mes']=r.mes
				dic['factura_id']=l.get('factura_id')
				dic['calculo_id']=r.id
				dic['sucursal']=''
				dic['correlativo']=i
				dic['fecha']=l.get('fecha')
				dic['numero']=l.get('factura')
				dic['cliente']=l.get('cliente')
				#dic['nrc']=l.get('nrc')
				customer=self.env['res.partner'].search([('vat','=',l.get('nrc'))],limit=1)
				if customer:
					dic['nit']=customer.nit
				dic['exento']=l.get('exento')
				dic['gravado']=l.get('gravado')
				dic['debito']=l.get('iva')
				dic['total_venta']=l.get('gravado')+l.get('exento')+l.get('iva')
				dic['retenido']=l.get('retenido')
				dic['percibido']=l.get('percibido')
				dic['total']=l.get('exento')+l.get('gravado')+l.get('iva')+l.get('retenido')+l.get('percibido')
				self.env['reportesv_sucursal.iva_consumidor_full'].create(dic)
				i=i+1
			
			lst=company.get_consumer_details(r.company_id.id,r.anio,r.mes,8,0)
			i=1
			for l in lst:
				dic={}
				dic['anio']=r.anio
				dic['mes']=r.mes
				dic['calculo_id']=r.id
				dic['sucursal']=''
				dic['correlativo']=i
				dic['fecha']=l.get('fecha')
				dic['inicial']=l.get('delnum')
				dic['final']=l.get('alnum')
				dic['exento']=l.get('exento')
				dic['serie']=l.get('serie')      #l.get('delnum')[:8]
				dic['local']=l.get('gravadolocal')
				dic['exportacion']=l.get('gravadoexportacion')
				dic['retencion']=l.get('retenido')
				dic['total_venta']=l.get('gravadolocal')+l.get('gravadoexportacion')+l.get('exento')+l.get('retenido')
				if factura:
					dic['caja']='' if factura.move_type=='out_refund' else '01'
				dic['anexo']='2'
				dic['clase_doc']='1. Impreso por Imprenta o Ticket'
				dic['numero_final']=l.get('alnum')
				dic['numero_inicial']=l.get('delnum')
				dic['resolucion']='121212'
				dic['tipo_documento_emitido']='01. Factura' 
				
				self.env['reportesv_sucursal.iva_consumidor'].create(dic)
				i=i+1
#percibido 2%
			self.env['reportesv_sucursal.iva_percibido'].search([('anio','=',r.anio),('mes','=',r.mes)]).unlink()
			lst=company.get_percepcion2_details(r.company_id.id,r.anio,r.mes)
			i=1
			for l in lst:
				dic={}
				dic['anio']=r.anio
				dic['mes']=r.mes
				dic['factura_id']=l.get('factura_id')
				dic['calculo_id']=r.id
				dic['correlativo']=i
				dic['nit']=l.get('nit')
				dic['fecha']=l.get('fecha')
				dic['serie']=l.get('serie') #creado
				dic['numero']=l.get('factura')
				dic['dui']=l.get('dui') #creado
				dic['monto']=l.get('monto') #creado
				dic['percibido']=l.get('percibido')
				dic['proveedor']=l.get('proveedor')
				dic['nrc']=l.get('nrc')
				customer=self.env['res.partner'].search([('vat','=',l.get('nrc'))],limit=1)
				if customer:
					dic['nit']=customer.nit
				if l.get('importacion') == True:
					dic['exento_interno']=0.0
					dic['exento_importacion']=l.get('exento')
					dic['gravado_interno']=0.0
					dic['gravado_importacion']=l.get('gravado')
				else:
					dic['exento_interno']=l.get('exento')
					dic['exento_importacion']=0.0
					dic['gravado_interno']=l.get('gravado')
					dic['gravado_importacion']=0.0
				dic['credito_fiscal']=l.get('iva')
				dic['retenido']=l.get('retenido')
				dic['percibido']=l.get('percibido')
				dic['excluido']=l.get('excluido')
				dic['terceros']=l.get('retencion3')
				dic['total_compra']=l.get('exento')+l.get('gravado')+l.get('iva')+l.get('retenido')+l.get('percibido')

				dic['anexo']='6'
				dic['clase_doc']='1'
				factura=self.env['account.move'].browse(l.get('factura_id'))
				if factura:
					dic['tipo_documento_emitido']='05' if factura.move_type=='out_refund' else '03'
				else:
					dic['tipo_documento_emitido']='03' 

				self.env['reportesv_sucursal.iva_percibido'].create(dic)
				i=i+1
			
#percibido 1%
			self.env['reportesv_sucursal.iva_percibido1'].search([('anio','=',r.anio),('mes','=',r.mes)]).unlink()
			lst=company.get_percepcion1_details(r.company_id.id,r.anio,r.mes)
			i=1
			for l in lst:
				dic={}
				dic['anio']=r.anio
				dic['mes']=r.mes
				dic['factura_id']=l.get('factura_id')
				dic['calculo_id']=r.id
				dic['correlativo']=i
				dic['nit']=l.get('nit')
				dic['fecha']=l.get('fecha')
				dic['serie']=l.get('serie') #creado
				dic['numero']=l.get('factura')
				dic['dui']=l.get('dui') #creado
				dic['monto']=l.get('monto') #creado
				dic['proveedor']=l.get('proveedor')
				dic['nrc']=l.get('nrc')
				customer=self.env['res.partner'].search([('vat','=',l.get('nrc'))],limit=1)
				if customer:
					dic['nit']=customer.nit
				if l.get('importacion') == True:
					dic['exento_interno']=0.0
					dic['exento_importacion']=l.get('exento')
					dic['gravado_interno']=0.0
					dic['gravado_importacion']=l.get('gravado')
				else:
					dic['exento_interno']=l.get('exento')
					dic['exento_importacion']=0.0
					dic['gravado_interno']=l.get('gravado')
					dic['gravado_importacion']=0.0
				dic['credito_fiscal']=l.get('iva')
				dic['retenido']=l.get('retenido')
				dic['percibido']=l.get('percibido')
				dic['excluido']=l.get('excluido')
				dic['terceros']=l.get('retencion3')
				dic['total_compra']=l.get('exento')+l.get('gravado')+l.get('iva')+l.get('retenido')+l.get('percibido')

				dic['anexo']='8'
				dic['clase_doc']='1'
				factura=self.env['account.move'].browse(l.get('factura_id'))
				if factura:
					dic['tipo_documento_emitido']='05' if factura.move_type=='out_refund' else '03'
				else:
					dic['tipo_documento_emitido']='03' 

				self.env['reportesv_sucursal.iva_percibido1'].create(dic)
				i=i+1
			

class calculo_compras(models.Model):
	_name = "reportesv_sucursal.iva_compras"
	anio=fields.Integer("Año")
	mes=fields.Integer("Mes")
	calculo_id=fields.Many2one(comodel_name='reportesv_sucursal.calculo_iva', string='Calculo id')
	name=fields.Char("Name")
	anexo=fields.Char("Número del Anexo")
	clase_doc=fields.Char("Clase de documento")
	correlativo=fields.Integer("Correlativo")
	credito_fiscal=fields.Float("Crédito Fiscal")
	excluido=fields.Float("Sujeto Excluido")
	exento_importacion=fields.Float("Importaciones Exentas y/o no sujetas")
	exento_internaciones=fields.Float("Internaciones Exentas y/o no sujetas")
	exento_interno=fields.Float("Compras internas exentas")
	factura_id=fields.Many2one(comodel_name='account.move', string='Factura id')
	fecha=fields.Date("Fecha de Emisión del Documento")
	gravado_importacion=fields.Float("Gravado importación")
	gravado_interno=fields.Float("Compras Internas Gravadas")
	importacion_servicios=fields.Float("Importaciones Gravadas de servicios")
	importacion_bienes=fields.Float("Importaciones Gravadas de Bienes")
	internaciones=fields.Float("Internaciones Gravadas de Bienes")
	nit=fields.Char("NIT del Proveedor")
	nrc=fields.Char("NRC")
	numero=fields.Char("Número de documento")
	percibido=fields.Float("Percibido")
	proveedor=fields.Char("Nombre del Proveedor")
	retenido=fields.Float("Retenido")
	terceros=fields.Float("Compras por terceros")
	tipo_documento_emitido=fields.Char("Tipo documento")
	total_compra=fields.Float("Total de Compras")
	dui=fields.Char("DUI del Proveedor")
	

class calculo_contribuyente(models.Model):
	_name = "reportesv_sucursal.iva_contribuyente"
	anio=fields.Integer("Año")
	mes=fields.Integer("Mes")
	calculo_id=fields.Many2one(comodel_name='reportesv_sucursal.calculo_iva', string='Calculo id')
	name=fields.Char("Nombre Razón Social o Denominación")
	anexo=fields.Char("Número de Anexo")
	clase_doc=fields.Char("Clase de Documento")
	cliente=fields.Char("Cliente")
	correlativo=fields.Integer("Correlativo")
	debito=fields.Float("Debito Fiscal")
	exento=fields.Float("Ventas Exentas")
	factura_id=fields.Many2one(comodel_name='account.move', string='Factura id')
	fecha=fields.Date("Fecha de Emisión del Documento")
	gravado=fields.Float("Ventas Gravadas Locales")
	nit=fields.Char("NIT o RNC del Cliente")
	dui=fields.Char("DUI del Cliente")
	no_sujeto=fields.Float("Ventas No Sujetas")
	nrc=fields.Char("NRC")
	numero=fields.Char("Número de Documento")
	numero_cortado=fields.Char("Numero Correlativo de documento/Numero de control")
	numero_interno=fields.Char("Número de control Interno")
	percibido=fields.Float("Percibido")
	resolucion=fields.Char("Número de Resolución")
	debito3=fields.Float("Debito fiscal de cuentas por ventas a Terceros")
	retenido=fields.Float("Retenido")
	venta3=fields.Float("Ventas a Cuentas de Terceros")
	serie=fields.Char("Serie de Documento")
	sucursal=fields.Char("Sucursal")
	tercero_no_domiciliciados=fields.Float("Ventas a Cuenta de Terceros no Domiciliados")
	terceros_debito=fields.Float("Debito Fiscal por Ventas a Cuentas de Terceros")
	tipo_documento_emitido=fields.Char("Tipo de Documento")
	total=fields.Float("Total")
	total_venta=fields.Float("Total de Ventas")
	

class calculo_consumidor(models.Model):
	_name = "reportesv_sucursal.iva_consumidor"
	anio=fields.Integer("Año")
	mes=fields.Integer("Mes")
	calculo_id=fields.Many2one(comodel_name='reportesv_sucursal.calculo_iva', string='Calculo id')
	name=fields.Char("Name")
	anexo=fields.Char("Número del Anexo")
	clase_doc=fields.Char("Clase de Documento")
	cliente=fields.Char("Cliente")
	correlativo=fields.Integer("Correlativo")
	exento=fields.Float("Ventas Exentas")
	exento_p=fields.Float("Ventas Internas Exentas no Sujetas a Proporcionalidad")
	export_np_ca=fields.Float("Exportaciones Fuera del Área Centro América")
	export_servicios=fields.Float("Exportaciones de Servicios")
	exportacion=fields.Float("Exportaciones Dentro del Área de Centro América")
	fecha=fields.Date("Fecha de Emisión")
	final=fields.Char("Número de Documento (Al)")
	inicial=fields.Char("Número de Documento (Del)")
	local=fields.Float("Ventas Gravadas Locales")
	nosujeto=fields.Float("Ventas no Sujetas")
	numero_final=fields.Char("Numero de Control Interno(al)")
	numero_inicial=fields.Char("Numero de Control Interno(del)")
	resolucion=fields.Char("Número de Resolución")
	retencion=fields.Float("Retencion")
	serie=fields.Char("Serie de Documento")
	sucursal=fields.Char("Sucursal")
	caja=fields.Char("Número de Maquina Registradora")
	terceros=fields.Float("Venta a Cuenta de Terceros no Domiciliados")
	tipo_documento_emitido=fields.Char("Tipo de Documento")
	total_venta=fields.Float("Total de Ventas")
	venta_zf=fields.Float("Ventas a Zonas Francas y DPA(tasa cero)")
	

class calculo_consumidor_full(models.Model):
	_name = "reportesv_sucursal.iva_consumidor_full"
	anio=fields.Integer("Año")
	mes=fields.Integer("Mes")
	calculo_id=fields.Many2one(comodel_name='reportesv_sucursal.calculo_iva', string='Calculo id')
	name=fields.Char("Name")
	cliente=fields.Char("Cliente")
	correlativo=fields.Integer("Correlativo")
	debito=fields.Float("Debito")
	exento=fields.Float("Exento")
	factura_id=fields.Many2one(comodel_name='account.move', string='Factura id')
	fecha=fields.Date("Fecha")
	gravado=fields.Float("Gravado")
	nit=fields.Char("NIT")
	numero=fields.Char("Numero")
	percibido=fields.Float("Percibido")
	retenido=fields.Float("Retenido")
	sucursal=fields.Char("Sucursal")
	total=fields.Float("Total")
	total_venta=fields.Float("Total venta")


#percepcion 2
class calculo_percibido2(models.Model):
	_name = "reportesv_sucursal.iva_percibido"
	anio=fields.Integer("Año")
	mes=fields.Integer("Mes")
	calculo_id=fields.Many2one(comodel_name='reportesv_sucursal.calculo_iva', string='Calculo id')
	name=fields.Char("Name")
	anexo=fields.Char("Número del Anexo")
	clase_doc=fields.Char("Clase de documento")
	correlativo=fields.Integer("Correlativo")
	credito_fiscal=fields.Float("Credito Fiscal")
	excluido=fields.Float("Sujeto Excluido")
	exento_importacion=fields.Float("Importaciones Exentas y/o no sujetas")
	exento_internaciones=fields.Float("Internaciones Exentas y/o no sujetas")
	exento_interno=fields.Float("Compras internas exentas y/o no sujetas")
	factura_id=fields.Many2one(comodel_name='account.move', string='Factura id')
	fecha=fields.Date("Fecha de Emisión")
	gravado_importacion=fields.Float("Gravado importación")
	gravado_interno=fields.Float("Gravado interno")
	importacion_servicios=fields.Float("Importaciones Gravadas de servicios")
	internaciones=fields.Float("Internaciones Gravadas de Bienes")
	nit=fields.Char("NIT Agente que le Efectuó el Anticipo a Cuenta")
	nrc=fields.Char("NRC")
	numero=fields.Char("Número de Documento")
	percibido=fields.Float("Monto del Anticipo a Cuenta de IVA 2%")
	proveedor=fields.Char("Porveedor")
	retenido=fields.Float("Retenido")
	terceros=fields.Float("Compras por terceros")
	tipo_documento_emitido=fields.Char("Tipo documento emitido")
	total_compra=fields.Float("Total compras")
	serie=fields.Char("Serie de Documento")
	dui=fields.Char("DUI del Agente")
	monto=fields.Float("Monto Sujeto")


#percibido 1%
class calculo_percibido1(models.Model):
	_name = "reportesv_sucursal.iva_percibido1"
	anio=fields.Integer("Año")
	mes=fields.Integer("Mes")
	calculo_id=fields.Many2one(comodel_name='reportesv_sucursal.calculo_iva', string='Calculo id')
	name=fields.Char("Name")
	anexo=fields.Char("Número del Anexo")
	clase_doc=fields.Char("Clase de documento")
	correlativo=fields.Integer("Correlativo")
	credito_fiscal=fields.Float("Credito Fiscal")
	excluido=fields.Float("Sujeto Excluido")
	exento_importacion=fields.Float("Importaciones Exentas y/o no sujetas")
	exento_internaciones=fields.Float("Internaciones Exentas y/o no sujetas")
	exento_interno=fields.Float("Compras internas exentas y/o no sujetas")
	factura_id=fields.Many2one(comodel_name='account.move', string='Factura id')
	fecha=fields.Date("Fecha de Emisión")
	gravado_importacion=fields.Float("Gravado importación")
	gravado_interno=fields.Float("Monto Sujeto")
	importacion_servicios=fields.Float("Importaciones Gravadas de servicios")
	internaciones=fields.Float("Internaciones Gravadas de Bienes")
	nit=fields.Char("NIT Agente")
	nrc=fields.Char("NRC")
	numero=fields.Char("Número de Documento")
	percibido=fields.Float("Monto de la Percepción 1%")
	proveedor=fields.Char("Porveedor")
	retenido=fields.Float("Retenido")
	terceros=fields.Float("Compras por terceros")
	tipo_documento_emitido=fields.Char("Tipo Documento")
	total_compra=fields.Float("Monto Sujeto") #cambio de nombre por Total compra
	serie=fields.Char("Serie de Documento")
	dui=fields.Char("DUI del Agente")
	monto=fields.Float("Monto Sujeto")