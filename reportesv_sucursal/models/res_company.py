import logging
from odoo import fields, models, api, SUPERUSER_ID, _
from odoo.tools import DEFAULT_SERVER_DATETIME_FORMAT
from odoo import tools
import pytz
from pytz import timezone
from datetime import datetime, date, timedelta
from odoo.exceptions import UserError, ValidationError
from odoo import exceptions
_logger = logging.getLogger(__name__)

class res_company(models.Model):
    _name = "res.company"
    _inherit = "res.company"
    resolucion=fields.Char(string='resolucion')
    propina=fields.Many2one(comodel_name='product.product', string='propina')
    
    

    def get_purchase_details(self, company_id, date_year, date_month):
        data = {}
        

        sql = """CREATE OR REPLACE VIEW odoosv_reportesv_purchase_report AS (
            select * from (
select ai.id as id,ai.invoice_date as fecha
	,ai.doc_numero as factura
	,(case when ai.tipo_documento_id='10' then '05. Nota de Credito' else '03. Comprobante de Credito Fiscal' end) as tipod
	,rp.name as proveedor
	,rp.nrc as NRC
	,rp.nit as nit
	,ai.x_serie as serie
	,0.0 as monto
	,rp.dui as dui
	,False as Importacion
	,/*Calculando el gravado (todo lo que tiene un impuesto aplicado de iva)*/
     (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code) = 'iva')
      ) as Gravado,
      /*Calculando el excento que no tiene iva*/
      (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code) = 'exento')
      ) as exento,
      /*Calculando el iva*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'iva'
       ) as Iva
	   ,/*Calculando el retenido*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'retencion'
       ) as Retenido
	    ,/*Calculando el percibido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'percepcion'
       ) as Percibido
         ,/*Calculando el excluido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'nosujeto'
       ) as nosujeto
	   ,/*Calculando el retencion a terceros*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'excluido'
       ) as excluido
        ,/*Calculando el retencion a terceros*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'otros'
       ) as otros
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id =doc.id
where ai.company_id= {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ai.move_type='in_invoice' 
	and ai.state in ('posted')  
	and doc.contribuyente = true
	and ((doc.requiere_poliza is null) or (doc.requiere_poliza = false))
	and ((ai.nofiscal is not null and ai.nofiscal = False)or (ai.nofiscal is null))
	
	union all
	
	select ai.id as id,ai.invoice_date as fecha
	,ai.doc_numero as factura
	,(case when ai.tipo_documento_id='10' then '05. Nota de Credito' else '03. Comprobante de Credito Fiscal' end) as tipod
	,rp.name as proveedor
	,rp.nrc as NRC
	,rp.nit as nit
	,ai.x_serie as serie
	,0.0 as monto
	,rp.dui as dui
	,False as Importacion
	,/*Calculando el gravado (todo lo que tiene un impuesto aplicado de iva)*/
      (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code) = 'iva')
      )*-1 as Gravado,
      /*Calculando el excento que no tiene iva*/
      (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code) = 'exento')
      )*-1 as exento,
      /*Calculando el iva*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'iva'
       ) as Iva
	   ,/*Calculando el retenido*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'retencion'
       ) as Retenido
	    ,/*Calculando el percibido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'percepcion'
       ) as Percibido
         ,/*Calculando el excluido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'nosujeto'
       ) as nosujeto
	   ,/*Calculando el retencion a terceros*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'excluido'
       ) as excluido
         ,/*Calculando el retencion a terceros*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'otros'
       ) as otros
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id =doc.id
where ai.company_id= {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ai.move_type='in_refund' 
	and doc.contribuyente = true 
	and ((doc.requiere_poliza is null) or (doc.requiere_poliza = false))
	and ai.state in ('posted') 
	and ((ai.nofiscal is not null and ai.nofiscal = False)or (ai.nofiscal is null))
	


union all

select  ai.id as id,ai.invoice_date as fecha
	,ai.doc_numero as factura
	,(case when ai.tipo_documento_id='10' then '05. Nota de Credito' else '03. Comprobante de Credito Fiscal' end) as tipod
	,rp.name as proveedor
	,rp.nrc as NRC
	,rp.nit as nit
	,ai.x_serie as serie
	,0.0 as monto
	,rp.dui as dui
	,True as Importacion
               ,(ai.amount_total*100/13) as  Gravado
               ,0.0  Exento
               ,ai.amount_total as  Iva
               ,0.0 as  Retenido
               ,0.0 as  Percibido
               ,0.0 as  nosujeto
               ,0.0 as  excluido
                 ,0.0 as  otros
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id =doc.id
where ai.company_id= {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ai.move_type='in_invoice' 
	and doc.contribuyente = true 
	and doc.requiere_poliza = true
	and ai.state in ('posted') 
	and ((ai.nofiscal is not null and ai.nofiscal = False)or (ai.nofiscal is null))

	/*Agregando percepcion al campo retenido*/
	 
	 union all

	 select  ai.id as id,ai.date as fecha
	,ai.doc_numero as factura
	,(case when ai.tipo_documento_id='10' then '05. Nota de Credito' else '03. Comprobante de Credito Fiscal' end) as tipod
	,rp.name as proveedor
	,rp.nrc as NRC
	,rp.nit as nit
	,ai.x_serie as serie
	,(aml.debit/2*100) as monto
	,rp.dui as dui
	,True as Importacion
               ,0.0 as  Gravado
               ,0.0  Exento
               ,0.0 as  Iva
               ,aml.debit as  Retenido
               ,0.0 as  percibido
               ,0.0 as  nosujeto
               ,0.0 as  excluido
                 ,0.0 as  otros
from account_move ai
	inner join account_move_line aml on aml.move_id=ai.id
	inner join res_partner rp on aml.partner_id=rp.id
	
where ai.company_id= {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ai.move_type='entry' 
    and aml.account_id=3489
	and ai.state in ('posted') 

) S
order by s.Fecha, s.Factura,S.nrc,s.nit
        )""".format(company_id,date_year,date_month)
        tools.drop_view_if_exists(self._cr, 'odoosv_reportesv_purchase_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_reportesv_purchase_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data

# ********************QUERY PARA EL ANEXO COMPRAS*************************************
    def get_purchase_details1(self, company_id, date_year, date_month):
        data = {}
        

        sql = """CREATE OR REPLACE VIEW odoosv_reportesv_purchase_report AS (
            select * from (
select ai.id as id,ai.invoice_date as fecha
	,ai.doc_numero as factura
	,(case when ai.tipo_documento_id='10' then '05. Nota de Credito' else '03. Comprobante de Credito Fiscal' end) as tipod
	,rp.name as proveedor
	,rp.nrc as NRC
	,rp.nit as nit
	,ai.x_serie as serie
	,0.0 as monto
	,rp.dui as dui
	,False as Importacion
	,/*Calculando el gravado (todo lo que tiene un impuesto aplicado de iva)*/
     (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code) = 'iva')
      ) as Gravado,
      /*Calculando el excento que no tiene iva*/
      (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code) = 'exento')
      ) as exento,
      /*Calculando el iva*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'iva'
       ) as Iva
	   ,/*Calculando el retenido*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'retencion'
       ) as Retenido
	    ,/*Calculando el percibido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'percepcion'
       ) as Percibido
         ,/*Calculando el excluido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'nosujeto'
       ) as nosujeto
	   ,/*Calculando el retencion a terceros*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'excluido'
       ) as excluido
        ,/*Calculando el retencion a terceros*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'otros'
       ) as otros
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id =doc.id
where ai.company_id= {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ai.move_type='in_invoice' 
	and ai.state in ('posted')  
	and doc.contribuyente = true
	and ((doc.requiere_poliza is null) or (doc.requiere_poliza = false))
	and ((ai.nofiscal is not null and ai.nofiscal = False)or (ai.nofiscal is null))
	
	union all
	
	select ai.id as id,ai.invoice_date as fecha
	,ai.doc_numero as factura
	,(case when ai.tipo_documento_id='10' then '05. Nota de Credito' else '03. Comprobante de Credito Fiscal' end) as tipod
	,rp.name as proveedor
	,rp.nrc as NRC
	,rp.nit as nit
	,ai.x_serie as serie
	,0.0 as monto
	,rp.dui as dui
	,False as Importacion
	,/*Calculando el gravado (todo lo que tiene un impuesto aplicado de iva)*/
      (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code) = 'iva')
      ) as Gravado,
      /*Calculando el excento que no tiene iva*/
      (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code) = 'exento')
      ) as exento,
      /*Calculando el iva*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'iva'
       )*-1 as Iva
	   ,/*Calculando el retenido*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'retencion'
       ) as Retenido
	    ,/*Calculando el percibido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'percepcion'
       ) as Percibido
         ,/*Calculando el excluido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'nosujeto'
       ) as nosujeto
	   ,/*Calculando el retencion a terceros*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'excluido'
       ) as excluido
         ,/*Calculando el retencion a terceros*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'otros'
       ) as otros
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id =doc.id
where ai.company_id= {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ai.move_type='in_refund' 
	and doc.contribuyente = true 
	and ((doc.requiere_poliza is null) or (doc.requiere_poliza = false))
	and ai.state in ('posted') 
	and ((ai.nofiscal is not null and ai.nofiscal = False)or (ai.nofiscal is null))
	


union all

select  ai.id as id,ai.invoice_date as fecha
	,ai.doc_numero as factura
	,(case when ai.tipo_documento_id='10' then '05. Nota de Credito' else '03. Comprobante de Credito Fiscal' end) as tipod
	,rp.name as proveedor
	,rp.nrc as NRC
	,rp.nit as nit
	,ai.x_serie as serie
	,0.0 as monto
	,rp.dui as dui
	,True as Importacion
               ,(ai.amount_total*100/13) as  Gravado
               ,0.0  Exento
               ,ai.amount_total as  Iva
               ,0.0 as  Retenido
               ,0.0 as  Percibido
               ,0.0 as  nosujeto
               ,0.0 as  excluido
                 ,0.0 as  otros
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id =doc.id
where ai.company_id= {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ai.move_type='in_invoice' 
	and doc.contribuyente = true 
	and doc.requiere_poliza = true
	and ai.state in ('posted') 
	and ((ai.nofiscal is not null and ai.nofiscal = False)or (ai.nofiscal is null))

	/*Agregando percepcion al campo retenido*/
	 
	 union all

	 select  ai.id as id,ai.date as fecha
	,ai.doc_numero as factura
	,(case when ai.tipo_documento_id='10' then '05. Nota de Credito' else '03. Comprobante de Credito Fiscal' end) as tipod
	,rp.name as proveedor
	,rp.nrc as NRC
	,rp.nit as nit
	,ai.x_serie as serie
	,(aml.debit/2*100) as monto
	,rp.dui as dui
	,True as Importacion
               ,0.0 as  Gravado
               ,0.0  Exento
               ,0.0 as  Iva
               ,aml.debit as  Retenido
               ,0.0 as  percibido
               ,0.0 as  nosujeto
               ,0.0 as  excluido
                 ,0.0 as  otros
from account_move ai
	inner join account_move_line aml on aml.move_id=ai.id
	inner join res_partner rp on aml.partner_id=rp.id
	
where ai.company_id= {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ai.move_type='entry' 
	and aml.account_id=920
	and ai.state in ('posted') 

) S
where S.Gravado <> 0
order by s.Fecha, s.Factura,S.nrc,s.nit
        )""".format(company_id,date_year,date_month)
        tools.drop_view_if_exists(self._cr, 'odoosv_reportesv_purchase_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_reportesv_purchase_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data



    def get_percepcion2_details(self, company_id, date_year, date_month):
        data = {}
        

        sql = """CREATE OR REPLACE VIEW odoosv_reportesv_percepcion2_report AS (
            select * from (

select  ai.id as id,ai.date as fecha
	,ai.doc_numero as factura
	,rp.name as proveedor
	,rp.nrc as NRC
	,rp.nit as nit
	,ai.x_serie as serie
	,(aml.debit/2*100) as monto
	,rp.dui as dui
	,True as Importacion
               ,0.0 as  Gravado
               ,0.0  Exento
               ,0.0 as  Iva
               ,0.0 as  Retenido
               ,aml.debit as  percibido
               ,0.0 as  nosujeto
               ,0.0 as  excluido
                 ,0.0 as  otros
from account_move ai
	inner join account_move_line aml on aml.move_id=ai.id
	inner join res_partner rp on aml.partner_id=rp.id
	
where ai.company_id= {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ai.move_type='entry' 
	and aml.account_id=920
	and ai.state in ('posted') 
	

	

) S
order by s.Fecha, s.Factura,S.nrc,s.nit
        )""".format(company_id,date_year,date_month)
        tools.drop_view_if_exists(self._cr, 'odoosv_reportesv_percepcion2_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_reportesv_percepcion2_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data

#PERCEPCION1%
    def get_percepcion1_details(self, company_id, date_year, date_month):
        data = {}
        

        sql = """CREATE OR REPLACE VIEW odoosv_reportesv_percepcion1_report AS (
            select * from (
select ai.id as id,ai.invoice_date as fecha
	,ai.doc_numero as factura
	,rp.name as proveedor
	,rp.nrc as NRC
	,rp.nit as nit
	,ai.x_serie as serie
	,rp.dui as dui
	,False as Importacion
	,/*Calculando el gravado (todo lo que tiene un impuesto aplicado de iva)*/
     (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code) = 'iva')
      ) as Gravado,
      /*Calculando el excento que no tiene iva*/
      (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code) = 'exento')
      ) as exento,
      /*Calculando el iva*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'iva'
       ) as Iva
	   ,/*Calculando el retenido*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'retencion'
       ) as Retenido
	    ,/*Calculando el percibido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'percepcion'
       ) as Percibido
         ,/*Calculando el excluido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'nosujeto'
       ) as nosujeto
	   ,/*Calculando el retencion a terceros*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'excluido'
       ) as excluido
        ,/*Calculando el retencion a terceros*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'otros'
       ) as otros
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id =doc.id
where ai.company_id= {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ai.move_type='in_invoice' 
	and ai.state in ('posted')  
	and doc.contribuyente = true
	and ((doc.requiere_poliza is null) or (doc.requiere_poliza = false))
	and ((ai.nofiscal is not null and ai.nofiscal = False)or (ai.nofiscal is null))


	union all
	
	select ai.id as id,ai.invoice_date as fecha
	,ai.doc_numero as factura
	,rp.name as proveedor
	,rp.nrc as NRC
	,rp.nit as nit
	,ai.x_serie as serie
	,rp.dui as dui
	,False as Importacion
	,/*Calculando el gravado (todo lo que tiene un impuesto aplicado de iva)*/
      (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code) = 'iva')
      ) as Gravado,
      /*Calculando el excento que no tiene iva*/
      (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code) = 'exento')
      ) as exento,
      /*Calculando el iva*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'iva'
       ) as Iva
	   ,/*Calculando el retenido*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'retencion'
       ) as Retenido
	    ,/*Calculando el percibido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'percepcion'
       ) as Percibido
         ,/*Calculando el excluido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'nosujeto'
       ) as nosujeto
	   ,/*Calculando el retencion a terceros*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'excluido'
       ) as excluido
         ,/*Calculando el retencion a terceros*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code) = 'otros'
       ) as otros
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id =doc.id
where ai.company_id= {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ai.move_type='in_refund' 
	and doc.contribuyente = true 
	and ((doc.requiere_poliza is null) or (doc.requiere_poliza = false))
	and ai.state in ('posted') 
	and ((ai.nofiscal is not null and ai.nofiscal = False)or (ai.nofiscal is null))

    union all

select  ai.id as id,ai.invoice_date as fecha
	,ai.doc_numero as factura
	,rp.name as proveedor
	,rp.nrc as NRC
	,rp.nit as nit
	,ai.x_serie as serie
	,rp.dui as dui
	,True as Importacion
               ,(ai.amount_total) as  Gravado
               ,0.0  Exento
               ,ai.amount_total as  Iva
               ,0.0 as  Retenido
               ,0.0 as  Percibido
               ,0.0 as  nosujeto
               ,0.0 as  excluido
                 ,0.0 as  otros
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id =doc.id
where ai.company_id= {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ai.move_type='in_invoice' 
	and doc.contribuyente = true 
	and doc.requiere_poliza = true
	and ai.state in ('posted') 
	and ((ai.nofiscal is not null and ai.nofiscal = False)or (ai.nofiscal is null))	
) S
where S.Gravado<>0 and S.Percibido<>0
order by s.Fecha, s.Factura,S.nrc,s.nit
        )""".format(company_id,date_year,date_month)
        tools.drop_view_if_exists(self._cr, 'odoosv_reportesv_percepcion1_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_reportesv_percepcion1_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data


	
    def get_taxpayer_details(self, company_id, date_year, date_month, stock_id):
        data = {}
        sql = """CREATE OR REPLACE VIEW odoosv_reportesv_taxpayer_report AS (
            select * from(
    select COALESCE(ai.date,ai.invoice_date) as fecha
    ,1 as sucursal
    ,ai.id as factura_id
	,ai.doc_numero as factura
	,rp.name as cliente
	,rp.nrc as NRC	
	,rp.nit as nit
	,ai.x_serie as serie
	,rp.dui as dui
	,ai.state as estado
	,/*Calculando el gravado (todo lo que tiene un impuesto aplicado de iva)*/
     (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code)='iva')
      )*(case when ai.move_type='out_refund' then -1 else 1 end) as Gravado,
      /*Calculando el excento que no tiene iva*/
     (Select coalesce(sum(ail.price_subtotal),0.00)
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and not exists(select ailt.account_tax_id 
						 from account_move_line_account_tax_rel ailt
				             inner join account_tax atx on ailt.account_tax_id=atx.id
				             inner join account_tax_group atg on atx.tax_group_id=atg.id
			             where ailt.account_move_line_id=ail.id and lower(atg.code) IN ('iva','nosujeto'))            
      )*(case when ai.move_type='out_refund' then -1 else 1 end) as Exento
      ,/*Calculando el gravado (todo lo que tiene un impuesto aplicado de iva)*/
     (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code)='nosujeto')
      )*(case when ai.move_type='out_refund' then -1 else 1 end) as NoSujeto
      ,/*Calculando el iva*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code)='iva'
       ) as Iva
	   ,/*Calculando el retenido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code)='retencion'
       ) as Retenido
	    ,/*Calculando el percibido*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code)='percepcion'
       ) as Percibido
       
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id=doc.id
	where ai.company_id=  {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ((ai.move_type='out_invoice') or (ai.move_type='out_refund'))
	and doc.codigo='CCF' 
	and ai.state in ('posted')
	
union 

select COALESCE(ai.date,ai.invoice_date) as fecha
    ,1 as sucursal
    ,ai.id as factura_id
	,ai.doc_numero as factura
	,'Anulado' as cliente
	,rp.nrc as NRC	
	,rp.nit as nit
	,ai.x_serie as serie
	,rp.dui as dui	
	,ai.state as estado
	,0.0 as Gravado
	,0.0 as Exento
	,0.0 as NoSujeto
    ,0.0 as Iva
	,0.0 as Retenido
	,0.0 as Percibido        
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id=doc.id
where ai.company_id=  {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=   {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=    {2} 
	and ((ai.move_type='out_invoice') or (ai.move_type='out_refund'))
	and doc.codigo='CCF' 
	and ai.state in ('cancel')
	and ((ai.nofiscal is not null and ai.nofiscal = False)or (ai.nofiscal is null))
)S
order by s.fecha, s.factura
            )""".format(company_id,date_year,date_month)
        tools.drop_view_if_exists(self._cr, 'odoosv_reportesv_taxpayer_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_reportesv_taxpayer_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data


    def get_consumerfull_details(self, company_id, date_year, date_month, stock_id):
        data = {}
        sql = """CREATE OR REPLACE VIEW odoosv_reportesv_fullconsumer_report AS (
            select * from(
    select COALESCE(ai.date,ai.invoice_date) as fecha
    ,1 as sucursal
    ,ai.id as factura_id
	,ai.doc_numero as factura
	,rp.name as cliente
	,ai.x_serie as serie
	,rp.nrc as NRC	
	,rp.nit as NIT	
	,ai.state as estado
	,/*Calculando el gravado (todo lo que tiene un impuesto aplicado de iva)*/
     (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code)='iva')
      )*(case when ai.move_type='out_refund' then -1 else 1 end) as Gravado,
      /*Calculando el excento que no tiene iva*/
     (Select coalesce(sum(ail.price_subtotal),0.00)
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and not exists(select ailt.account_tax_id 
						 from account_move_line_account_tax_rel ailt
				             inner join account_tax atx on ailt.account_tax_id=atx.id
				             inner join account_tax_group atg on atx.tax_group_id=atg.id
			             where ailt.account_move_line_id=ail.id and lower(atg.code) IN ('iva','nosujeto'))            
      )*(case when ai.move_type='out_refund' then -1 else 1 end) as Exento
      ,/*Calculando el gravado (todo lo que tiene un impuesto aplicado de iva)*/
     (select coalesce(sum(ail.price_subtotal),0.00) 
      from account_move_line ail
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code)='nosujeto')
      )*(case when ai.move_type='out_refund' then -1 else 1 end) as NoSujeto
      ,/*Calculando el iva*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code)='iva'
       ) as Iva
	   ,/*Calculando el retenido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code)='retencion'
       ) as Retenido
	    ,/*Calculando el percibido*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code)='percepcion'
       ) as Percibido
       
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id=doc.id
	where ai.company_id=  {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=  {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}
	and ((ai.move_type='out_invoice') or (ai.move_type='out_refund'))
	and doc.codigo='Factura' 
	and ai.state in ('posted')
	
union 

select COALESCE(ai.date,ai.invoice_date) as fecha
    ,1 as sucursal
    ,ai.id as factura_id
	,ai.doc_numero as factura
	,'Anulado' as cliente
	,rp.nrc as NRC	
	,rp.nit as nit	
	,ai.x_serie as serie
	,ai.state as estado
	,0.0 as Gravado
	,0.0 as Exento
	,0.0 as NoSujeto
    ,0.0 as Iva
	,0.0 as Retenido
	,0.0 as Percibido        
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id=doc.id
where ai.company_id=  {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=   {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=    {2} 
	and ((ai.move_type='out_invoice') or (ai.move_type='out_refund'))
	and doc.codigo='Factura' 
	and ai.state in ('cancel')
	and ((ai.nofiscal is not null and ai.nofiscal = False)or (ai.nofiscal is null))
)S
order by s.fecha, s.factura
            )""".format(company_id,date_year,date_month)
        tools.drop_view_if_exists(self._cr, 'odoosv_reportesv_fullconsumer_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_reportesv_fullconsumer_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data


    def get_consumer_details(self, company_id, date_year, date_month, sv_invoice_serie_size, stock_id):
        data = {}
        if sv_invoice_serie_size == None or sv_invoice_serie_size < 8:
            sv_invoice_serie_size = 8
        sql = """CREATE OR REPLACE VIEW odoosv_reportesv_consumer_report AS (
            Select
	SS.Fecha
    ,0 as sucursal
	,min(SS.Factura) as delnum
	,max(SS.Factura) as alnum
	,sum(SS.exento) as Exento
	,sum(SS.GravadoLocal) as GravadoLocal
	,sum(SS.GravadoExportacion) as GravadoExportacion
	,Sum(SS.ivaLocal) as IvaLocal
	,Sum(SS.ivaexportacion) as IvaExportacion
	,Sum(SS.retenido) as Retenido
	,0.0 as nosujeto
	,estado
	,tipod
	,serie
FROM (
select S.fecha
	,S.factura
	,S.estado
	,S.grupo
	,S.exento
	,S.tipod
	,S.serie
	,case 
		when S.tipo_localidad='Local' then S.Gravado 
		else 0.00 end as GravadoLocal
	,case 
		when S.tipo_localidad!='Local' then S.Gravado 
		else 0.00 end as GravadoExportacion
	,case 
		when S.tipo_localidad='Local' then S.Iva 
		else 0.00 end as IvaLocal
	,case 
		when S.tipo_localidad!='Local' then S.Iva 
		else 0.00 end as IvaExportacion
	,S.Retenido
from(
select ai.invoice_date as fecha
	,coalesce(ai.doc_numero,cast(ai.id as varchar)) as factura
	,'Valida' as estado
	,ai.serie as serie
	,(case when ai.tipo_documento_id='1' then 'F' else 'T' end) as tipod
	,FG.grupo	
	,case when doc.codigo='Exportacion' then 'nolocal' else 'Local' end as tipo_localidad
	,/*Calculando el gravado (todo lo que tiene un impuesto aplicado de iva)*/
     (select coalesce(sum(ail.price_total),0.00) 
      from account_move_line ail
	  inner join product_product pp on ail.product_id=pp.id
      where ail.move_id=ai.id
      	  and ail.exclude_from_invoice_tab=False
		  and ail.product_id <> 5731	 
	      and exists(select ailt.account_tax_id 
					from account_move_line_account_tax_rel ailt
				        inner join account_tax atx on ailt.account_tax_id=atx.id
				        inner join account_tax_group atg on atx.tax_group_id=atg.id
			         where ailt.account_move_line_id=ail.id and lower(atg.code)='iva')
      ) as Gravado,
      /*Calculando el excento que no tiene iva*/
     (Select coalesce(sum(ail.price_subtotal),0.00)
      from account_move_line ail
	  inner join res_company rc on ail.company_id=rc.id
      where ail.move_id=ai.id
	      and (ail.product_id is null or ail.product_id <> rc.propina)
      	  and ail.exclude_from_invoice_tab=False 
	      and not exists(select ailt.account_tax_id 
						 from account_move_line_account_tax_rel ailt
				             inner join account_tax atx on ailt.account_tax_id=atx.id
				             inner join account_tax_group atg on atx.tax_group_id=atg.id
			             where ailt.account_move_line_id=ail.id and lower(atg.code)='iva')            
      ) as Exento
      ,/*Calculando el iva*/
      (Select coalesce(sum(ait.credit-ait.debit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code)='Exento'
       ) as Iva
	   ,/*Calculando el retenido*/
      (Select coalesce(sum(ait.debit-ait.credit),0.00)
       from account_move_line ait 
 	       inner join account_tax atx on ait.tax_line_id=atx.id
	       inner join account_tax_group atg on atx.tax_group_id=atg.id
       where ait.move_id=ai.id
	       and lower(atg.code)='retencion'
       ) as Retenido
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id =doc.id
	inner join (select * from FacturasAgrupadas( {0}, {2} , {1} , 8 )) FG on ai.id=FG.invoice_id
where ai.company_id=   {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=    {1}  
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=  {2}  
	and ai.move_type='out_invoice' 
	and doc.codigo in ('Factura','Exportacion')
	and ai.state in ('posted')
	
union all 

select COALESCE(ai.date,ai.invoice_date) as fecha
	,coalesce(ai.doc_numero,cast(ai.id as varchar)) as factura		
	,'Valida' as estado
	,ai.serie as serie
	,(case when ai.tipo_documento_id='1' then 'F' else 'T' end) as tipod
	,FG.grupo
	,case when doc.codigo='Exportacion' then 'nolocal' else 'Local' end as sv_region
	,0.0 as Gravado
	,0.0 as Exento
    ,0.0 as Iva
	,0.0 as Retenido
from account_move ai
	inner join res_partner rp on ai.partner_id=rp.id
	inner join odoosv_fiscal_document doc on ai.tipo_documento_id =doc.id
	inner join (select * from FacturasAgrupadas( {0} , {2}, {1} , 8)) FG on ai.id=FG.invoice_id
where ai.company_id=   {0} 
	and date_part('year',COALESCE(ai.date,ai.invoice_date))=    {1} 
	and date_part('month',COALESCE(ai.date,ai.invoice_date))=   {2} 
	and ai.move_type='out_invoice' 
	and doc.codigo in ('Factura','Exportacion')
	and ai.state in ('cancel')
	and (ai.nofiscal is null or ai.nofiscal = False)
)S
)SS
group by SS.fecha, SS.estado,SS.tipod,SS.serie
order by SS.fecha
            )""".format(company_id,date_year,date_month,sv_invoice_serie_size)
        tools.drop_view_if_exists(self._cr, 'odoosv_reportesv_consumer_report')
        self._cr.execute(sql) #Query for view"
        self._cr.execute("SELECT * FROM public.odoosv_reportesv_consumer_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data

    def get_ticket_details(self, company_id, date_year, date_month, stock_id):
        data = {}
        sql = """CREATE OR REPLACE VIEW odoosv_reportesv_ticket_report AS (Select
        SS.Fecha
        ,SS.sucursal
        ,min(SS.factura) as DELNum
        ,max(SS.factura) as ALNum
        ,sum(SS.exento) as Exento
        ,sum(SS.GravadoLocal) as GravadoLocal
        ,sum(0.00) as GravadoExportacion
        ,Sum(SS.ivaLocal) as IvaLocal
        ,Sum(0.00) as IvaExportacion
        ,Sum(0.00) as Retenido
        FROM(select S.fecha
        ,S.sucursal
        ,S.factura
        ,S.exento
        ,S.Gravado as GravadoLocal
        ,0.00 as GravadoExportacion
        ,S.Iva as IvaLocal
        ,0.00 as IvaExportacion
        ,S.Retenido
        from(
        select date(po.date_order) as fecha
        ,po.location_id as sucursal
        ,coalesce(po.ticket_number,cast(right(po.pos_reference,4) as Integer)) as factura
        ,/*Calculando el gravado (todo lo que tiene un impuesto aplicado de iva)*/
        case when afp.sv_clase='Gravado' then
	       (case when ((po.amount_tax < 0) or (po.amount_total < 0)) = TRUE then
	        po.amount_total
            else po.amount_total - po.amount_tax end)
	    else 0.00 end as Gravado
        ,/*Calculando el excento que no tiene iva*/
        case when afp.sv_clase='Exento' then
	       po.amount_total
	    else 0.00 end as Exento
        ,/*Calculando el iva*/
        case when afp.sv_clase='Gravado' then
        po.amount_tax
        else 0.00 end as Iva
        ,/*Calculando el retenido*/
        (0.00) as Retenido
        from pos_order po inner join account_fiscal_position afp on po.fiscal_position_id=afp.id
        where po.company_id= {0}
        and date_part('year',COALESCE(po.create_date,po.date_order))= {1}
        and date_part('month',COALESCE(po.create_date,po.date_order))=  {2}
        and po.invoice_id is null
        and po.state in ('done','paid')
        )S)SS group by SS.fecha, SS.sucursal order by SS.fecha,SS.sucursal)""".format(company_id,date_year,date_month)
        tools.drop_view_if_exists(self._cr, 'odoosv_reportesv_ticket_report')
        self._cr.execute(sql) #Query for view"
        if stock_id:
            data = "SELECT * FROM public.odoosv_reportesv_ticket_report where sucursal = {0}".format(stock_id) #Query que extrae la data de la sucursal solicitada
            self._cr.execute(data)
        else:
            self._cr.execute("SELECT * FROM public.odoosv_reportesv_ticket_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data

    def get_month_str(self, month):
        m = "No especificado"
        if self and month>0:
            months = {1: "Enero", 2: "Febrero",
                    3: "Marzo", 4: "Abril",
                    5: "Mayo", 6: "Junio",
                    7: "Julio", 8: "Agosto",
                    9: "Septiembre", 10: "Octubre",
                    11: "Noviembre", 12: "Diciembre"}
            m = months[month]
            return m
        else:
            return m

    def get_stock_name(self, stock_location_id):
        sucursal= " "
        if self and stock_location_id:
            sucursal = self.env['stock.warehouse'].search([('lot_stock_id','=',stock_location_id)],limit=1).name
            return sucursal
        else:
            return sucursal
