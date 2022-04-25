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
    
    
#BALANCE DE COMPROBACION SUMAS Y SALDOS

    def get_balance_details(self, company_id, date_year, date_month, acum):
        data = {}

        sql = """CREATE OR REPLACE VIEW odoosv_financierosv_balance_report AS (
            select S.* 
                ,case when COALESCE(S.signonegativo,False) =true then -1
                else 1 end as TipoCuenta
from (
select aa.code 
    ,aa.name as name
    ,aa.tipo as type
    ,(select acs.x_negativo from x_signos acs where x_company_id={0} and acs.x_name=left(aa.code,1)) as signonegativo
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code||'%' and date_part('month',COALESCE(am1.date,am1.invoice_date))<{2} and am1.state in ('posted')) else 0 end as previo 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code||'%' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as debe     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code||'%'  and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as haber
         

from cuentas aa     
) S
where S.previo<>0 or S.debe<>0 or S.haber<>0 
order by S.code

        )""".format(company_id,date_year,date_month,acum)
        tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_balance_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_financierosv_balance_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data
      

#LIBRO MAYOR
    def get_mayor_details(self, company_id, date_year, date_month, acum):
        data = {}

        sql = """CREATE OR REPLACE VIEW odoosv_financierosv_mayor_report AS (
            select S1.*
                , case when COALESCE(S1.signonegativo,False) =true then -1
                else 1 end as TipoCuenta 
from
(
select aa.code
    ,aa.name
    ,aa.tipo as type
    ,(select acs.x_negativo from x_signos acs where x_company_id={0} and acs.x_name=left(aa.code,1)) as signonegativo
    ,(select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0) 
        from account_move_line aml1
        inner join account_move am1 on aml1.move_id=am1.id
        inner join account_account a1 on aml1.account_id=a1.id
        where am1.company_id= {0} and a1.code like aa.code||'%' and date_part('month',COALESCE(am1.date,am1.invoice_date))< {2}  and am1.state in ('posted')) as previo
    ,(select COALESCE(sum(aml1.debit),0)
        from account_move_line aml1
        inner join account_move am1 on aml1.move_id=am1.id
        inner join account_account a1 on aml1.account_id=a1.id
        where am1.company_id= {0} and a1.code like aa.code||'%' and date_part('month',COALESCE(am1.date,am1.invoice_date))>= {2}   and date_part('month',COALESCE(am1.date,am1.invoice_date))<= {2}   and am1.state in ('posted')) as debe  
    ,(select COALESCE(sum(aml1.credit),0)
        from account_move_line aml1
        inner join account_move am1 on aml1.move_id=am1.id
        inner join account_account a1 on aml1.account_id=a1.id
        where am1.company_id= {0} and a1.code like aa.code||'%' and date_part('month',COALESCE(am1.date,am1.invoice_date))>= {2}  and date_part('month',COALESCE(am1.date,am1.invoice_date))<= {2}    and am1.state in ('posted')) as haber  

from cuentas aa
where aa.company_id= {0}  and length(trim(aa.code))=4
order by aa.code



) S1
where abs(S1.previo)>0.0001 or abs(S1.debe)>0.0001 or abs(S1.haber)>0.0001
order by S1.code

        )""".format(company_id,date_year,date_month,acum)
        tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_mayor_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_financierosv_mayor_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data

#*************libro mayor anexo**************************
    def get_mayor_details1(self, company_id, date_year, date_month, acum):
        data = {}

        sql = """CREATE OR REPLACE VIEW odoosv_financierosv_mayor_report AS (
            select * from ( 
select am.date   
    from account_move_line aml
    inner join account_move am on aml.move_id=am.id
    inner Join account_account aa on aa.id=aml.account_id
    inner join account_group ag on 
    where aa.code like am.code ||'%'  and date_part('month',COALESCE(am.date,am.invoice_date))>= {2} and date_part('month',COALESCE(am.date,am.invoice_date))<={2} and am.company_id={0}  and am.state in ('posted')
from am
)S1
order by S1.date


        )""".format(company_id,date_year,date_month,acum)
        tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_mayor_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_financierosv_mayor_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data

#*****************ESTADO DE RESULTADO***********************************************
    def get_resultado_details(self, company_id, date_year, date_month, acum):
        data = {}

        sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
           select * from ( 
    select aa.code 
    ,aa.name as name
    ,aa.tipo as type
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code and aa.code like '%5101%' and date_part('month',COALESCE(am1.date,am1.invoice_date))={2} and am1.state in ('posted')) else 0 end as previo 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%5101%' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as debe     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%5101%' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as haber

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))>4 and length(trim(aa.code))<=6
order by aa.code
)S2
where S2.previo<>0 or S2.debe<>0 or S2.haber<>0  
order by S2.code

        )""".format(company_id,date_year,date_month,acum)
        tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data

    def get_resultado_details1(self, company_id, date_year, date_month, acum):
        data = {}

        sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
           select * from ( 
    select aa.code 
    ,aa.name as name
    ,aa.tipo as type
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code and aa.code like '%5301%' and date_part('month',COALESCE(am1.date,am1.invoice_date))={2} and am1.state in ('posted')) else 0 end as previo1 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%5301%' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as debe1     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%5301%' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as haber1

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))>=4 and length(trim(aa.code))<=6
order by aa.code

)S2
where S2.previo1<>0 or S2.debe1<>0 or S2.haber1<>0 
order by S2.code

        )""".format(company_id,date_year,date_month,acum)
        tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data

    def get_resultado_details2(self, company_id, date_year, date_month, acum):
        data = {}

        sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
           select * from ( 
    select aa.code 
    ,aa.name as name
    ,aa.tipo as type
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%' and date_part('month',COALESCE(am1.date,am1.invoice_date))={2} and am1.state in ('posted')) else 0 end as previo2 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as debe2     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as haber2

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=4 and aa.code like '41%'
order by aa.code
)S2
where S2.previo2<>0 or S2.debe2<>0 or S2.haber2<>0 
order by S2.code

        )""".format(company_id,date_year,date_month,acum)
        tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data

    def get_resultado_details3(self, company_id, date_year, date_month, acum):
        data = {}

        sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
           select * from ( 
    select aa.code 
    ,aa.name as name
    ,aa.tipo as type
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code and aa.code like '%4102' and date_part('month',COALESCE(am1.date,am1.invoice_date))={2} and am1.state in ('posted')) else 0 end as previo3 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%4102' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as debe3     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%4102' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as haber3

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))>4 and length(trim(aa.code))<=6
order by aa.code

)S2
where S2.previo3<>0 or S2.debe3<>0 or S2.haber3<>0 
order by S2.code

        )""".format(company_id,date_year,date_month,acum)
        tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data

    def get_resultado_details4(self, company_id, date_year, date_month, acum):
        data = {}

        sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
           select * from ( 
    select aa.code 
    ,aa.name as name
    ,aa.tipo as type
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}   and aa.code like '4201' and date_part('month',COALESCE(am1.date,am1.invoice_date))={2} and am1.state in ('posted')) else 0 end as previo4 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0}  and aa.code like '4201' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as debe4     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0}  and aa.code like '4201' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as haber4

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))>=4 and length(trim(aa.code))<6
order by aa.code

)S2
where S2.previo4<>0 or S2.debe4<>0 or S2.haber4<>0 
order by S2.code

        )""".format(company_id,date_year,date_month,acum)
        tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data

    def get_resultado_details5(self, company_id, date_year, date_month, acum):
        data = {}

        sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
           select * from ( 
    select aa.code 
    ,aa.name as name
    ,aa.tipo as type
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code and aa.code like '%4202%' and date_part('month',COALESCE(am1.date,am1.invoice_date))={2} and am1.state in ('posted')) else 0 end as previo5
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%4202%' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as debe5     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%4202%' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as haber5

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))>=4 and length(trim(aa.code))<6
order by aa.code

)S2
where S2.previo5<>0 or S2.debe5<>0 or S2.haber5<>0 
order by S2.code

        )""".format(company_id,date_year,date_month,acum)
        tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data  

    def get_resultado_details6(self, company_id, date_year, date_month, acum):
        data = {}

        sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
           select * from ( 
    select aa.code 
    ,aa.name as name
    ,aa.tipo as type
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code and aa.code like '%4301%' and date_part('month',COALESCE(am1.date,am1.invoice_date))={2} and am1.state in ('posted')) else 0 end as previo6 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%4301%' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as debe6     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%4301%' and date_part('month',COALESCE(am2.date,am2.invoice_date))={2} and am2.state in ('posted') ) as haber6

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))>=4 and length(trim(aa.code))<6
order by aa.code

)S2
where S2.previo6<>0 or S2.debe6<>0 or S2.haber6<>0 
order by S2.code

        )""".format(company_id,date_year,date_month,acum)
        tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data                  
       

    def get_balance1_details(self, company_id, date_year, date_month):
        data = {}
        

        sql = """CREATE OR REPLACE VIEW odoosv_financierosv_balance_report AS (
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
	and aml.account_id=920
	and ai.state in ('posted') 

) S
order by s.Fecha, s.Factura,S.nrc,s.nit
        )""".format(company_id,date_year,date_month)
        tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_balance_report')
        self._cr.execute(sql)
        self._cr.execute("SELECT * FROM public.odoosv_financierosv_balance_report")
        if self._cr.description: #Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
            data = self._cr.dictfetchall()
        return data