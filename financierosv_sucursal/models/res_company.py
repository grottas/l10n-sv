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
	resolucion = fields.Char(string='resolucion')

	# BALANCE DE COMPROBACION SUMAS Y SALDOS
	####
	def get_balance_details(self, company_id, date_year, date_month, acum, fechai, fechaf):
		"""

		:param company_id:
		:param date_year:
		:param date_month:
		:param acum:
		:param fechai:
		:param fechaf:
		:return:
		"""
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_balance_report AS (
            select S.* 
                ,case when COALESCE(S.signonegativo,False) =true then -1
                else 1 end as TipoCuenta
from (
select aa.code 
    ,aa.name as name
    ,date_part('day',CAST('{4}' as date)) as fi
    ,date_part('day',CAST('{5}' as date)) as ff
    ,(select acs.x_negativo from x_signos acs where x_company_id={0} and acs.x_name=left(aa.code,1)) as signonegativo
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code||'%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber
         

from cuentas aa     
) S
where S.previo<>0 or S.debe<>0 or S.haber<>0  
order by S.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_balance_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_balance_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	# ********************LIBRO MAYOR*****************************************************************************

	def get_mayor_details(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_mayor_report AS (
            select *
from
(
select aa.code
    ,aa.name
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
   from account_move_line aml1
        inner join account_move am1 on aml1.move_id=am1.id
        inner join account_account a1 on aml1.account_id=a1.id
        where am1.company_id= {0} and a1.code like aa.code||'%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date)  and am1.state in ('posted')) else 0 end as previo  
    ,(select COALESCE(sum(aml1.debit),0)
        from account_move_line aml1
        inner join account_move am1 on aml1.move_id=am1.id
        inner join account_account a1 on aml1.account_id=a1.id
        where am1.company_id= {0} and a1.code like aa.code||'%'  and COALESCE(am1.date,am1.invoice_date)>=CAST('{4}' as date) and COALESCE(am1.date,am1.invoice_date)<=CAST('{5}' as date)   and am1.state in ('posted')) as debe  
    ,(select COALESCE(sum(aml1.credit),0)
        from account_move_line aml1
        inner join account_move am1 on aml1.move_id=am1.id
        inner join account_account a1 on aml1.account_id=a1.id
        where am1.company_id= {0} and a1.code like aa.code||'%' and COALESCE(am1.date,am1.invoice_date)>=CAST('{4}' as date) and COALESCE(am1.date,am1.invoice_date)<=CAST('{5}' as date)    and am1.state in ('posted')) as haber  
from cuentas aa
where aa.company_id= {0}  and length(trim(aa.code))=4
order by aa.code
) S1
where abs(S1.previo)>0.0001 or abs(S1.debe)>0.0001 or abs(S1.haber)>0.0001
order by S1.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_mayor_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_mayor_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_mayor_details1(self, company_id, date_year, date_month, acum, fechai, fechaf, cuenta):
		data = {}
		cuenta = cuenta + '%'
		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_mayor_report AS (
            SELECT * FROM ( 
				select am1.date, sum(aml.debit) as debit ,sum(aml.credit) as credit
				from account_move_line aml
                inner join account_move am1 on aml.move_id=am1.id
                inner Join account_account aa on aa.id=aml.account_id
                inner Join account_group ag on ag.id=aa.group_id
                where am1.company_id= {0} and 
                	aa.code like ag.code_prefix_start ||'%' and 
                	COALESCE(am1.date,am1.invoice_date)>=CAST('{4}' as date) and 
                	COALESCE(am1.date,am1.invoice_date)<=CAST('{5}' as date) and 
                	am1.state in ('posted')
                and ag.code_prefix_start LIKE '{6}'	
                group by am1.date            
				order by am1.date
			)S
		)""".format(company_id, date_year, date_month, acum, fechai, fechaf, cuenta)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_mayor_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_mayor_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	# ****************************Libro Anexo Mayor***************************************************
	def get_auxiliar_details(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_auxiliar_report AS (
           			SELECT S1.*, case when COALESCE(S1.signonegativo,False) =true then -1 else 1 end as TipoCuenta 
					FROM (select aa.code, aa.id as id, aa.name, aa.internal_type as type,
    					 (select acs.x_negativo from x_signos acs where x_company_id={0} and acs.x_name=left(aa.code,1)) as signonegativo,
     					 case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    						from account_account aa1
        					inner join account_move_line aml1 on aa1.id=aml1.account_id
        					inner join account_move am1 on aml1.move_id=am1.id
        					where aa1.company_id={0} and aa1.code like aa.code||'%' and 
        						COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and 
        						am1.state in ('posted')) else 0 end as previo, 
						(select COALESCE(sum(aml2.debit),0)
        				 from account_account aa2
        				  inner join account_move_line aml2 on aa2.id=aml2.account_id
        				  inner join account_move am2 on aml2.move_id=am2.id
        				 where aa2.company_id={0} and aa2.code like aa.code||'%' and 
        				 COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
        				 COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) 
        				 and am2.state in ('posted') ) as debe,     
						 (select COALESCE(sum(aml2.credit),0) from account_account aa2
        				  inner join account_move_line aml2 on aa2.id=aml2.account_id
        				  inner join account_move am2 on aml2.move_id=am2.id
        				  where aa2.company_id={0} and aa2.code like aa.code||'%' and 
        				  COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
        				  COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
        				  am2.state in ('posted') ) as haber
						  from account_account aa
						  where aa.company_id= {0}  and length(trim(aa.code))>4 and aa.code not in ('110304') and aa.internal_type<>'view'
						order by aa.code	
					) S1
				   where S1.previo<>0 or S1.debe<>0 or S1.haber<>0
        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_auxiliar_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_auxiliar_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_auxiliar_details1(self, company_id, date_year, date_month, acum, fechai, fechaf, id):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_auxiliar_report AS (
					SELECT * FROM( SELECT am.date, am.name as name, am.ref as ref, am.tipo_documento_id as tipo, 
									  aj.name as journal, aml.account_id, aml.name as sv_concepto, 
									  aml.debit as debit, aml.credit as credit
								FROM account_move_line aml
								INNER JOIN account_move am ON aml.move_id = am.id
								INNER JOIN account_journal aj ON aj.id = am.journal_id
								WHERE am.company_id={0} AND aml.account_id = '{6}' AND
									  COALESCE(am.date,am.invoice_date)>=CAST('{4}' as date) AND
									  COALESCE(am.date,am.invoice_date)<=CAST('{5}' as date) AND
									   am.state in ('posted') 
								ORDER BY am.date
					) S
		)""".format(company_id, date_year, date_month, acum, fechai, fechaf, id)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_auxiliar_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_auxiliar_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	# *****************ESTADO DE RESULTADO***********************************************
	def get_resultado_details(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
           select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code and aa.code like '%5101%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%5101%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%5101%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))>4 and length(trim(aa.code))<=6
order by aa.code
)S2
where S2.previo<>0 or S2.debe<>0 or S2.haber<>0  
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_resultado_details1(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
           select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code and aa.code like '%5301%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo1 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%5301%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe1     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code and aa.code like '%5301%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber1

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))>=4 and length(trim(aa.code))<=6
order by aa.code

)S2
where S2.previo1<>0 or S2.debe1<>0 or S2.haber1<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_resultado_details2(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
           select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo2 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe2     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber2

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=2 and aa.code like '41%'
order by aa.code
)S2
where S2.previo2<>0 or S2.debe2<>0 or S2.haber2<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_resultado_details3(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo3 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe3     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber3

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=4 and aa.code between '4100%' and  '4106%'
order by aa.code
)S2
where S2.previo3<>0 or S2.debe3<>0 or S2.haber3<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_resultado_details4(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
          select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo4 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe4     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber4

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=4 and aa.code like '4201%'
order by aa.code
)S2
where S2.previo4<>0 or S2.debe4<>0 or S2.haber4<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_resultado_details5(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo5 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe5     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber5

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=4 and aa.code like '4202%'
order by aa.code
)S2
where S2.previo5<>0 or S2.debe5<>0 or S2.haber5<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_resultado_details6(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo6 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe6     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber6

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=4 and aa.code like '4301'
order by aa.code

)S2
where S2.previo6<>0 or S2.debe6<>0 or S2.haber6<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_resultado_details7(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo7 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe7     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber7

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=1 and aa.code like '5'
order by aa.code

)S2
where S2.previo7<>0 or S2.debe7<>0 or S2.haber7<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_resultado_details8(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo8 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe8     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber8

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=2 and aa.code like '42'
order by aa.code

)S2
where S2.previo8<>0 or S2.debe8<>0 or S2.haber8<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_resultado_details9(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo9 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe9     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber9

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=2 and aa.code like '43'
order by aa.code

)S2
where S2.previo9<>0 or S2.debe9<>0 or S2.haber9<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_resultado_details10(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo10 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe10     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber10

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=1 and aa.code like '4'
order by aa.code

)S2
where S2.previo10<>0 or S2.debe10<>0 or S2.haber10<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_resultado_details11(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_resultado_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo11 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe11     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber11

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=2 and aa.code like '45'
order by aa.code

)S2
where S2.previo11<>0 or S2.debe11<>0 or S2.haber11<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_resultado_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	# **************************************BALANCE GENERAL...!!!************************************************
	def get_general_details(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and am1.state in ('posted')) else 0 end as previo 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))<=2 and aa.code like '11%'
order by aa.code

)S2
where S2.previo<>0 or S2.debe<>0 or S2.haber<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details1(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am2 on aml1.move_id=am2.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)<CAST('{4}' as date) and am2.state in ('posted')) else 0 end as previo1 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe1     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber1

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=2 and aa.code like '12%'
order by aa.code

)S2
where S2.previo1<>0 or S2.debe1<>0 or S2.haber1<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details2(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am2 on aml1.move_id=am2.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)<CAST('{4}' as date) and am2.state in ('posted')) else 0 end as previo2
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe2     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber2

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=2 and aa.code like '21%'
order by aa.code

)S2
where S2.previo2<>0 or S2.debe2<>0 or S2.haber2<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details3(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am2 on aml1.move_id=am2.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)<CAST('{4}' as date) and am2.state in ('posted')) else 0 end as previo3 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe3     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber3

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=2 and aa.code like '22%'
order by aa.code

)S2
where S2.previo3<>0 or S2.debe3<>0 or S2.haber3<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details4(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am2 on aml1.move_id=am2.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)<CAST('{4}' as date) and am2.state in ('posted')) else 0 end as previo4
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe4     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber4

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=2 and aa.code like '31%'
order by aa.code

)S2
where S2.previo4<>0 or S2.debe4<>0 or S2.haber4<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details5(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am2 on aml1.move_id=am2.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)<CAST('{4}' as date) and am2.state in ('posted')) else 0 end as previo5
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe5     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber5

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=4 and aa.code between '1100%' and  '1106%'
order by aa.code

)S2
where S2.previo5<>0 or S2.debe5<>0 or S2.haber5<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details6(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am2 on aml1.move_id=am2.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)<CAST('{4}' as date) and am2.state in ('posted')) else 0 end as previo6
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe6     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber6

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=4 and aa.code between '1200%' and  '1210%'
order by aa.code

)S2
where S2.previo6<>0 or S2.debe6<>0 or S2.haber6<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details7(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am2 on aml1.move_id=am2.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)<CAST('{4}' as date) and am2.state in ('posted')) else 0 end as previo7
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe7     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber7

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=4 and aa.code between '2100%' and  '2110%'
order by aa.code

)S2
where S2.previo7<>0 or S2.debe7<>0 or S2.haber7<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details8(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
            select * from ( 
    select aa.code 
    ,aa.name as name
    
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am2 on aml1.move_id=am2.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)<CAST('{4}' as date) and am2.state in ('posted')) else 0 end as previo8
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'  and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as debe8     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%'and COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and am2.state in ('posted') ) as haber8

from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=4 and aa.code between '2200%' and  '2209%'
order by aa.code

)S2
where S2.previo8<>0 or S2.debe8<>0 or S2.haber8<>0 
order by S2.code

        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details9(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
    select * from ( select aa.code,aa.name as name, case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%' and 
        COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and 
        am1.state in ('posted')) else 0 end as previo9 
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
        COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
        COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
        am2.state in ('posted') ) as debe9     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
        COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
        COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
        am2.state in ('posted') ) as haber9
from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=4 and aa.code between '3100%' and  '3109%'
order by aa.code)S2
where S2.previo9<>0 or S2.debe9<>0 or S2.haber9<>0 
order by S2.code)""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details10(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}
		acum = 1

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
           select * from ( 
    select aa.code 
    ,aa.name as name 
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%' and 
	 	COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and 
		am1.state in ('posted')) else 0 end as previo10
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
  		am2.state in ('posted') ) as debe10     
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
  		am2.state in ('posted') ) as haber10
from cuentas aa 
where aa.company_id={0} and length(trim(aa.code))=2 and aa.code like '41%'
order by aa.code)S2
where S2.previo10<>0 or S2.debe10<>0 or S2.haber10<>0 
order by S2.code
        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details11(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}
		acum = 1
		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
           select * from ( 
    select aa.code 
    ,aa.name as name 
    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
    from account_account aa1
        inner join account_move_line aml1 on aa1.id=aml1.account_id
        inner join account_move am1 on aml1.move_id=am1.id
        where aa1.company_id={0}  and aa1.code like aa.code ||'%' and 
	 	COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and 
		am1.state in ('posted')) else 0 end as previo11
,(select COALESCE(sum(aml2.debit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
  		am2.state in ('posted') ) as debe11   
,(select COALESCE(sum(aml2.credit),0)
        from account_account aa2
        inner join account_move_line aml2 on aa2.id=aml2.account_id
        inner join account_move am2 on aml2.move_id=am2.id
        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
  		am2.state in ('posted') ) as haber11
from cuentas aa 
where aa.company_id= {0} and length(trim(aa.code))=4  and aa.code between '4100%' and '4102%'
order by aa.code

)S2
where S2.previo11<>0 or S2.debe11<>0 or S2.haber11<>0 
order by S2.code
		        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details12(self, company_id, date_year, date_month, acum, fechai, fechaf):
		"""
		 Obtiene el resumen de los GASTOS OPERACIONALES del anio fiscal
		"""
		data = {}
		acum = 3
		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
	           select * from ( 
	    select aa.code 
	    ,aa.name as name 
	    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
	    from account_account aa1
	        inner join account_move_line aml1 on aa1.id=aml1.account_id
	        inner join account_move am1 on aml1.move_id=am1.id
	        where aa1.company_id={0}  and aa1.code like aa.code ||'%' and 
		 	COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and 
			am1.state in ('posted')) else 0 end as previo12
	,(select COALESCE(sum(aml2.debit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as debe12   
	,(select COALESCE(sum(aml2.credit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as haber12
	from cuentas aa 
	where aa.company_id={0} and length(trim(aa.code))=2  and aa.code like '42%'
	order by aa.code

	)S2
	where S2.previo12<>0 or S2.debe12<>0 or S2.haber12<>0 
	order by S2.code
			        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details13(self, company_id, date_year, date_month, acum, fechai, fechaf):
		"""
		Obtiene los GASTOS OPERACIONALES del anio fiscal
		"""
		acum = 3

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
	           select * from ( 
	    select aa.code 
	    ,aa.name as name 
	    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
	    from account_account aa1
	        inner join account_move_line aml1 on aa1.id=aml1.account_id
	        inner join account_move am1 on aml1.move_id=am1.id
	        where aa1.company_id={0}  and aa1.code like aa.code ||'%' and 
		 	COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and 
			am1.state in ('posted')) else 0 end as previo13
	,(select COALESCE(sum(aml2.debit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as debe13   
	,(select COALESCE(sum(aml2.credit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as haber13
	from cuentas aa 
	where aa.company_id={0} and length(trim(aa.code))=4  and aa.code like '42%'
	order by aa.code

	)S2
	where S2.previo13<>0 or S2.debe13<>0 or S2.haber13<>0 
	order by S2.code
			        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details14(self, company_id, date_year, date_month, acum, fechai, fechaf):
		""" GASTOS NO OPERACIONALES """
		acum = 3
		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
	           select * from ( 
	    select aa.code 
	    ,aa.name as name 
	    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
	    from account_account aa1
	        inner join account_move_line aml1 on aa1.id=aml1.account_id
	        inner join account_move am1 on aml1.move_id=am1.id
	        where aa1.company_id={0}  and aa1.code like aa.code ||'%' and 
		 	COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and 
			am1.state in ('posted')) else 0 end as previo14
	,(select COALESCE(sum(aml2.debit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as debe14   
	,(select COALESCE(sum(aml2.credit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as haber14
	from cuentas aa 
	where aa.company_id={0} and length(trim(aa.code))=2  and aa.code like '43%'
	order by aa.code

	)S2
	where S2.previo14<>0 or S2.debe14<>0 or S2.haber14<>0 
	order by S2.code
			        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details15(self, company_id, date_year, date_month, acum, fechai, fechaf):
		""" GASTOS NO OPERACIONALES """
		acum = 3

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
	           select * from ( 
	    select aa.code 
	    ,aa.name as name 
	    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
	    from account_account aa1
	        inner join account_move_line aml1 on aa1.id=aml1.account_id
	        inner join account_move am1 on aml1.move_id=am1.id
	        where aa1.company_id={0}  and aa1.code like aa.code ||'%' and 
		 	COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and 
			am1.state in ('posted')) else 0 end as previo15
	,(select COALESCE(sum(aml2.debit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as debe15
	,(select COALESCE(sum(aml2.credit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as haber15
	from cuentas aa 
	where aa.company_id={0} and length(trim(aa.code))=4  and aa.code like '4301%'
	order by aa.code

	)S2
	where S2.previo15<>0 or S2.debe15<>0 or S2.haber15<>0 
	order by S2.code
			        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()

		return data

	def _get_descuento_ventas(self, company_id, date_year, date_month, acum, fechai, fechaf):
		""" Se obtiene el Ingreso del año Fiscal. """
		data = {}
		year = datetime.now().year
		fechai = datetime.strptime(str(year) + '-01-01', '%Y-%m-%d')

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
	           select * from ( 
	    select aa.code 
	    ,aa.name as name 
	    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
	    from account_account aa1
	        inner join account_move_line aml1 on aa1.id=aml1.account_id
	        inner join account_move am1 on aml1.move_id=am1.id
	        where aa1.company_id={0}  and aa1.code like aa.code ||'%' and 
		 	COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and 
			am1.state in ('posted')) else 0 end as previo
	,(select COALESCE(sum(aml2.debit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as debe
	,(select COALESCE(sum(aml2.credit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as haber
	from cuentas aa 
	where aa.company_id={0} and length(trim(aa.code))=2  and aa.code like '53%'
	order by aa.code )S2
	where S2.previo<>0 or S2.debe<>0 or S2.haber<>0 
	order by S2.code
			        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()

		descuento = data[0].get('previo') + data[0].get('debe') - data[0].get('haber')

		return descuento

	def get_general_details16(self, company_id, date_year, date_month, acum, fechai, fechaf):
		""" Se obtiene el Ingreso del año Fiscal. """
		data = {}
		year = datetime.now().year
		fechai = datetime.strptime(str(year) + '-01-01', '%Y-%m-%d')

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
	           select * from ( 
	    select aa.code 
	    ,aa.name as name 
	    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
	    from account_account aa1
	        inner join account_move_line aml1 on aa1.id=aml1.account_id
	        inner join account_move am1 on aml1.move_id=am1.id
	        where aa1.company_id={0} and aa1.code like aa.code ||'%' and 
		 	COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and 
			am1.state in ('posted')) else 0 end as previo16
	,(select COALESCE(sum(aml2.debit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as debe16   
	,(select COALESCE(sum(aml2.credit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as haber16
	from cuentas aa 
	where aa.company_id={0} and length(trim(aa.code))=2  and aa.code like '51%'
	order by aa.code )S2
	where S2.previo16<>0 or S2.debe16<>0 or S2.haber16<>0 
	order by S2.code
			        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()

		descuento = self._get_descuento_ventas(company_id, date_year, date_month, acum, fechai, fechaf)
		ingreso = data[0].get('previo16') + data[0].get('haber16') - data[0].get('debe16')
		data[0]['previo16'] = ingreso - descuento
		data[0]['haber16'] = 0
		data[0]['debe16'] = 0
		return data

	def get_general_details17(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}
		year = datetime.now().year
		fechai = datetime.strptime(str(year) + '-01-01', '%Y-%m-%d')

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
	           select * from ( 
	    select aa.code 
	    ,aa.name as name 
	    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
	    from account_account aa1
	        inner join account_move_line aml1 on aa1.id=aml1.account_id
	        inner join account_move am1 on aml1.move_id=am1.id
	        where aa1.company_id={0} and aa1.code like aa.code ||'%' and 
		 	COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and 
			am1.state in ('posted')) else 0 end as previo17
	,(select COALESCE(sum(aml2.debit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as debe17
	,(select COALESCE(sum(aml2.credit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as haber17
	from cuentas aa 
	where aa.company_id={0} and length(trim(aa.code))=4  and aa.code between '5100%' and '5301%'
	order by aa.code )S2
	where S2.previo17<>0 or S2.debe17<>0 or S2.haber17<>0 
	order by S2.code
			        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details18(self, company_id, date_year, date_month, acum, fechai, fechaf):
		""" GASTOS NO OPERACIONALES """
		acum = 3
		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
	           select * from ( 
	    select aa.code 
	    ,aa.name as name 
	    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
	    from account_account aa1
	        inner join account_move_line aml1 on aa1.id=aml1.account_id
	        inner join account_move am1 on aml1.move_id=am1.id
	        where aa1.company_id={0} and aa1.code like aa.code ||'%' and 
		 	COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and 
			am1.state in ('posted')) else 0 end as previo18
	,(select COALESCE(sum(aml2.debit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as debe18   
	,(select COALESCE(sum(aml2.credit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as haber18
	from cuentas aa 
	where aa.company_id={0} and length(trim(aa.code))=2  and aa.code like '45%'
	order by aa.code

	)S2
	where S2.previo18<>0 or S2.debe18<>0 or S2.haber18<>0 
	order by S2.code
			        )""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_general_details19(self, company_id, date_year, date_month, acum, fechai, fechaf):
		""" GASTOS NO OPERACIONALES """
		acum = 3

		sql = """CREATE OR REPLACE VIEW odoosv_financierosv_general_report AS (
	           select * from ( 
	    select aa.code 
	    ,aa.name as name 
	    ,case when {3}=1 then  (select COALESCE(sum(aml1.debit),0) - COALESCE(sum(aml1.credit),0)
	    from account_account aa1
	        inner join account_move_line aml1 on aa1.id=aml1.account_id
	        inner join account_move am1 on aml1.move_id=am1.id
	        where aa1.company_id={0} and aa1.code like aa.code ||'%' and 
		 	COALESCE(am1.date,am1.invoice_date)<CAST('{4}' as date) and 
			am1.state in ('posted')) else 0 end as previo19
	,(select COALESCE(sum(aml2.debit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as debe19
	,(select COALESCE(sum(aml2.credit),0)
	        from account_account aa2
	        inner join account_move_line aml2 on aa2.id=aml2.account_id
	        inner join account_move am2 on aml2.move_id=am2.id
	        where aa2.company_id={0} and aa2.code like aa.code ||'%' and 
	  		COALESCE(am2.date,am2.invoice_date)>=CAST('{4}' as date) and 
	  		COALESCE(am2.date,am2.invoice_date)<=CAST('{5}' as date) and 
	  		am2.state in ('posted') ) as haber19
	from cuentas aa 
	where aa.company_id={0} and length(trim(aa.code))=4  and aa.code like '4501%'
	order by aa.code

	)S2
	where S2.previo19<>0 or S2.debe19<>0 or S2.haber19<>0 
	order by S2.code)""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_general_report')
		self._cr.execute(sql)
		self._cr.execute("SELECT * FROM public.odoosv_financierosv_general_report")
		if self._cr.description:  # Verify whether or not the query generated any tuple before fetching in order to avoid PogrammingError: No results when fetching
			data = self._cr.dictfetchall()
		return data

	def get_reserva_legal(self, company_id, date_year, date_month, acum, fechai, fechaf):
		data = {}
		sql = """SELECT aa.name, aml.debit, aml.credit, aml.balance
        		 FROM account_account aa
        			INNER JOIN account_move_line aml on aa.id=aml.account_id
        			INNER JOIN account_move am on aml.move_id=am.id
				WHERE aml.company_id={0} AND aa.code LIKE '310301' AND move_name LIKE 'CIERRE%' AND
					 COALESCE(am.date,am.invoice_date)>=CAST('{4}' as date) AND 
				     COALESCE(am.date,am.invoice_date)<=CAST('{5}' as date) AND am.state in ('posted') 
		""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		# tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute(sql)
		if self._cr.description:
			data = self._cr.dictfetchall()
		return data

	def get_impuesto_renta(self, company_id, date_year, date_month, acum, fechai, fechaf):
		"""
		 Gets the Income Tax data for the account 21060401 and the journal name that starts with CIERRE
		"""
		data = {}
		sql = """SELECT aa.name, aml.debit, aml.credit, aml.balance
        		 FROM account_account aa
        			INNER JOIN account_move_line aml on aa.id=aml.account_id
        			INNER JOIN account_move am on aml.move_id=am.id
				WHERE aml.company_id={0} AND aa.code LIKE '21060401' AND move_name LIKE 'CIERRE%' AND
					 COALESCE(am.date,am.invoice_date)>=CAST('{4}' as date) AND 
				     COALESCE(am.date,am.invoice_date)<=CAST('{5}' as date) AND am.state in ('posted') 
		""".format(company_id, date_year, date_month, acum, fechai, fechaf)
		# tools.drop_view_if_exists(self._cr, 'odoosv_financierosv_resultado_report')
		self._cr.execute(sql)
		self._cr.execute(sql)
		if self._cr.description:
			data = self._cr.dictfetchall()

		return data

	def get_type_account(self, account_code):
		"""
		Given the code of the account, it returns the internal group of the same
		:param account_code: account code
		:return: internal group account
		"""
		account = self.env['account.account'].search([('code', 'like', '%s%%' % account_code)], limit=1)

		return account.internal_group
