import sys
sys.path.insert(1, '/home/PMO/airflow/dags')
from pyspark.sql import SparkSession
from pyspark import SparkConf, conf
from pyspark.sql.types import *
import pandas as pd
from datetime import * 
import Connections as conn
import ETLFunctions as fx
from time import * 
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
import random 
import sys 
import pendulum

load_connection_string = "jdbc:mysql://10.10.11.242:3306/RME_TEST?useUnicode=true&characterEncoding=UTF-8"


SubContractor_query="""(
   SELECT
	RME_DEV.RME_PRJ_CONT_PKG.get_Deduction(d.po_header_id,
	'SITE_DEDUCTION') Site_Deduction,
	RME_DEV.RME_PRJ_CONT_PKG.get_Deduction(d.po_header_id,
	'DEBIT_MEMO') DEBIT_MEMO,
	RME_DEV.RME_PRJ_CONT_PKG.get_Deduction(d.po_header_id,
	'OTHER_DEDUCTION') OTHER_DEDUCTION,
	RME_DEV.RME_PRJ_CONT_PKG.get_Deduction(d.po_header_id,
	'DEDUCTION_RETURN') DEDUCTION_RETURN,
	RME_DEV.RME_PRJ_CONT_PKG.get_Deduction(d.po_header_id,
	'Material_on_site') Material_on_site,
	D.SEGMENT1 SC_NO,
	(
	SELECT
		grp_name
	FROM
		apps.rme_awt_grp_v AWT
	WHERE
		awt.po_header_id = d.po_header_id) Deduction_Name,
	(
	SELECT
		SUM(WITHOLDING_TAX_AMNT)
	FROM
		APPS.RME_PRJ_CONT_WC
	WHERE
		K_HEADER_ID = D.PO_HEADER_ID
		AND IPC_STATUS IN 'APPROVED') WITHOLDING_TAX_AMNT,
	(
	SELECT
		SUM(LABOUR_OFFICE_AMNT)
	FROM
		APPS.RME_PRJ_CONT_WC
	WHERE
		K_HEADER_ID = D.PO_HEADER_ID
		AND IPC_STATUS IN 'APPROVED') LABOUR_OFFICE_AMNT,
	(
	SELECT
		SUM(SOCIAL_INSURANCE_AMNT)
	FROM
		APPS.RME_PRJ_CONT_WC
	WHERE
		K_HEADER_ID = D.PO_HEADER_ID
		AND IPC_STATUS IN 'APPROVED') SOCIAL_INSURANCE_AMNT,
	(
	SELECT
		SUM(LABOUR_OFFICE)
	FROM
		APPS.RME_PRJ_CONT_WC
	WHERE
		K_HEADER_ID = D.PO_HEADER_ID
		AND IPC_STATUS IN 'APPROVED') LABOUR_OFFICE,
	(
	SELECT
		SUM(BID_RETENTION_AMNT)
	FROM
		APPS.RME_PRJ_CONT_WC
	WHERE
		K_HEADER_ID = D.PO_HEADER_ID
		AND IPC_STATUS IN 'APPROVED') BID_RETENTION_AMNT,
	(
	SELECT
		SUM(PERFORM_RETENTION_AMNT)
	FROM
		APPS.RME_PRJ_CONT_WC
	WHERE
		K_HEADER_ID = D.PO_HEADER_ID
		AND IPC_STATUS IN 'APPROVED') PERFORM_RETENTION_AMNT,
	(
	SELECT
		SUM(ss.TAX_AMOUNT)
	FROM
		apps.rme_prj_cont_lines ss,
		apps.rme_prj_cont_wc wc
	WHERE
		ss.wc_id = wc.wc_id
		AND ss.DISTRIBUTION_ID = c.po_DISTRIBUTION_ID
		AND WC.K_HEADER_ID = D.PO_HEADER_ID
           ) TAX,
	C.PO_DISTRIBUTION_ID,
	((
	SELECT
		ss.TAX
	FROM
		apps.rme_prj_cont_lines ss,
		apps.rme_prj_cont_wc wc
	WHERE
		ss.wc_id = wc.wc_id
		AND ss.DISTRIBUTION_ID = c.po_DISTRIBUTION_ID
		AND ss.DISTRIBUTION_ID = c.po_DISTRIBUTION_ID
		AND WC.K_HEADER_ID = D.PO_HEADER_ID
		AND ROWNUM = 1
            )) TAX_RATE,
	D.PO_HEADER_ID,
	D.REVISION_NUM,
	D.COMMENTS SC_MANUAL,
	E.VENDOR_NAME SUPPLIER_NAME,
	E.SEGMENT1 SUPP_CODE,
	F.VENDOR_SITE_CODE VENDOR_SITE_CODE,
	(
	SELECT
		O.ORGANIZATION_NAME
	FROM
		apps.ORG_ORGANIZATION_DEFINITIONS O
	WHERE
		O.ORGANIZATION_ID = PLL.SHIP_TO_ORGANIZATION_ID
		AND ROWNUM = 1) PROJECT_NAME,
	D.AUTHORIZATION_STATUS,
	apps.PO_INQ_SV.GET_PO_TOTAL('STANDARD',
	D.PO_HEADER_ID,
	NULL) TOTAL_SC,
	D.CURRENCY_CODE,
	TO_CHAR(D.CREATION_DATE,'YYYY-MM-DD') CREATION_DATE,
	(
	SELECT
		P.FULL_NAME
	FROM
		apps.PER_ALL_PEOPLE_F P
	WHERE
		P.PERSON_ID = D.AGENT_ID
		AND (SYSDATE BETWEEN P.EFFECTIVE_START_DATE AND
               P.EFFECTIVE_END_DATE)) BUYER_NAME,
	G.LINE_NUM,
	G.ITEM_DESCRIPTION,
	G.CATEGORY_ID,
	--       (SELECT SEGMENT1 || '-' || SEGMENT2
	--          FROM MTL_CATEGORIES_B
	--         WHERE CATEGORY_ID = G.CATEGORY_ID)
	--          CATEGORY,
	G.AMOUNT PRICE,
	TO_CHAR(PLL.NEED_BY_DATE,'YYYY-MM-DD') NEED_BY_DATE,
	--       PLL.SHIPMENT_NUM,
	PLL.PAYMENT_TYPE,
	PLL.DESCRIPTION,
	PLL.QUANTITY,
	PLL.PRICE_OVERRIDE,
	DECODE(PLL.AMOUNT,
              NULL,
              NVL(PLL.QUANTITY, 0) * NVL(PLL.PRICE_OVERRIDE, 0),
              PLL.AMOUNT) AMOUNT,
	NVL(PLL.QUANTITY, 0) * NVL(PLL.PRICE_OVERRIDE, 0) AMOUNT_OLD,
	(
	SELECT
		PPA.NAME
	FROM
		apps.PA_PROJECTS_ALL PPA
	WHERE
		PPA.PROJECT_ID = C.PROJECT_ID) PROJECT,
	(
	SELECT
		PT.TASK_NUMBER
	FROM
		apps.PA_TASKS PT
	WHERE
		PT.PROJECT_ID = C.PROJECT_ID
		AND PT.TASK_ID = C.TASK_ID) TASK,
	C.EXPENDITURE_TYPE,
	TO_CHAR(C.EXPENDITURE_ITEM_DATE,'YYYY-MM-DD') EXPENDITURE_ITEM_DATE,
	(
	SELECT
		O.ORGANIZATION_NAME
	FROM
		apps.ORG_ORGANIZATION_DEFINITIONS O
	WHERE
		O.ORGANIZATION_ID = C.EXPENDITURE_ORGANIZATION_ID
		AND ROWNUM = 1) EXPENDITURE_ORGANIZATION,
	ROUND(
    DECODE(
        PLL.PAYMENT_TYPE,
        'RATE',
        CASE 
            WHEN PLL.QUANTITY * PLL.PRICE_OVERRIDE = 0 THEN 0
            ELSE ((PLL.QUANTITY_RECEIVED * PLL.PRICE_OVERRIDE) / 
                  (PLL.QUANTITY * PLL.PRICE_OVERRIDE)) * 100
        END,
        CASE 
            WHEN PLL.AMOUNT = 0 THEN 0
            ELSE (PLL.AMOUNT_RECEIVED / PLL.AMOUNT) * 100
        END
		),
		2
	) AS PROGRESS,
	(
	SELECT
		DISTINCT inv.Invoice_Amount
	FROM
		apps.rme_prj_cont_lines ss,
		apps.rme_prj_cont_wc wc,
		apps.RME_AP_INVOICES_INTERFACE inv
	WHERE
		ss.wc_id = wc.wc_id
		AND ss.header_id = d.po_header_id
		AND ss.DISTRIBUTION_ID = c.po_DISTRIBUTION_ID
		AND wc.IPC_NO(+) = inv.IPC_NO
		AND wc.K_HEADER_ID(+) = inv.ATTRIBUTE5
		AND inv.wc_id = ss.wc_id(+)
		AND ROWNUM = 1) INVOICE_AMT_INT,
	NVL((SELECT DISTINCT SUM(ss.Total)
             FROM apps.rme_prj_cont_lines ss, apps.rme_prj_cont_wc wc
            WHERE ss.wc_id = wc.wc_id
              AND ss.DISTRIBUTION_ID = c.po_DISTRIBUTION_ID
              AND ss.creation_date =
                  (SELECT MAX(creation_date)
                     FROM apps.rme_prj_cont_lines wc1
                    WHERE DISTRIBUTION_ID = ss.DISTRIBUTION_ID)),
           (SELECT DECODE(PLL.PAYMENT_TYPE,
                          'LUMPSUM',
                          SUM(VV.AMOUNT_RECEIVED),
                          SUM(VV.QUANTITY_RECEIVED))
              FROM apps.PO_LINE_LOCATIONS_MERGE_V VV
             WHERE VV.PO_HEADER_ID = D.PO_HEADER_ID
               AND VV.LINE_LOCATION_ID = PLL.LINE_LOCATION_ID
               AND ROWNUM = 1)) QUANTITY_RECEIVED,
	(
	SELECT
		DISTINCT SUM(ss.current_qty)
	FROM
		apps.rme_prj_cont_lines ss,
		apps.rme_prj_cont_wc wc
	WHERE
		ss.wc_id = wc.wc_id
		AND ss.DISTRIBUTION_ID = c.po_DISTRIBUTION_ID) cumulative_qty,
	DECODE(PLL.PAYMENT_TYPE,
              'RATE',
              (PLL.QUANTITY_BILLED * PLL.PRICE_OVERRIDE),
              PLL.AMOUNT_BILLED) INVOICE_AMT,
	E.SEGMENT1 VENDOR_NUM,
	to_char((
	SELECT
		MAX(RSH.REQUEST_DATE)
	FROM
		apps.RCV_SHIPMENT_HEADERS RSH,
		apps.RCV_SHIPMENT_LINES RSL,
		apps.AP_SUPPLIERS POV,
		apps.AP_SUPPLIER_SITES_ALL PVS,
		apps.PO_HEADERS_ALL POH,
		apps.PO_DOC_STYLE_HEADERS PDSH
	WHERE
		RSH.SHIPMENT_HEADER_ID = RSL.SHIPMENT_HEADER_ID
		AND RSH.ASN_TYPE = 'WC'
		AND RSL.PO_HEADER_ID = POH.PO_HEADER_ID
		AND POV.VENDOR_ID = RSH.VENDOR_ID
		AND PVS.VENDOR_SITE_ID = RSH.VENDOR_SITE_ID
		--
           AND RSL.PO_HEADER_ID = D.PO_HEADER_ID
		AND E.VENDOR_ID = RSH.VENDOR_ID
		AND F.VENDOR_SITE_ID = RSH.VENDOR_SITE_ID),'YYYY-MM-DD') LAST_WC,
	PLL.UNIT_MEAS_LOOKUP_CODE PAY_ITEM_UOM,
	D.ATTRIBUTE14 WRK_PKG,
	(
	SELECT
		DECODE(PLL.PAYMENT_TYPE,
                      'LUMPSUM',
                      SUM(VV.AMOUNT_RECEIVED),
                      SUM(VV.QUANTITY_RECEIVED))
	FROM
		apps.PO_LINE_LOCATIONS_MERGE_V VV
	WHERE
		VV.PO_HEADER_ID = D.PO_HEADER_ID
		AND VV.LINE_LOCATION_ID = PLL.LINE_LOCATION_ID) *
       PLL.PRICE_OVERRIDE Billed_Amount,
	NVL((SELECT SUM(ss.REMANING_AMOUNT)
             FROM apps.rme_prj_cont_lines ss, apps.rme_prj_cont_wc wc
            WHERE ss.wc_id = wc.wc_id
              AND ss.header_id = d.po_header_id
              AND ss.DISTRIBUTION_ID = c.po_DISTRIBUTION_ID),
           (SELECT DECODE(PLL.PAYMENT_TYPE,
                          'LUMPSUM',
                          SUM(VV.AMOUNT_RECEIVED),
                          SUM(VV.QUANTITY_RECEIVED))
              FROM apps.PO_LINE_LOCATIONS_MERGE_V VV
             WHERE VV.PO_HEADER_ID = D.PO_HEADER_ID
               AND VV.LINE_LOCATION_ID = PLL.LINE_LOCATION_ID) *
           PLL.PRICE_OVERRIDE) Net_Amount,
	NVL(NVL((SELECT SUM(REMANING_AMOUNT)
                 FROM apps.rme_prj_cont_lines ss, apps.rme_prj_cont_wc wc
                WHERE ss.wc_id = wc.wc_id
                  AND ss.header_id = d.po_header_id
                  AND ss.DISTRIBUTION_ID = c.po_DISTRIBUTION_ID),
               0) + NVL((SELECT DECODE(PLL.PAYMENT_TYPE,
                                       'LUMPSUM',
                                       SUM(VV.AMOUNT_RECEIVED),
                                       SUM(VV.QUANTITY_RECEIVED))
                           FROM apps.PO_LINE_LOCATIONS_MERGE_V VV
                          WHERE VV.PO_HEADER_ID = D.PO_HEADER_ID
                            AND VV.LINE_LOCATION_ID = PLL.LINE_LOCATION_ID) *
                        PLL.PRICE_OVERRIDE,
                        0),
           0) wc_amnt,
	PLL.ATTRIBUTE2 AREA
FROM
	apps.PO_DISTRIBUTIONS_ALL C,
	apps.PO_HEADERS_ALL D,
	apps.PO_VENDORS E,
	apps.PO_VENDOR_SITES_ALL F,
	apps.PO_LINES_ALL G,
	apps.PO_LINE_LOCATIONS_ALL PLL
WHERE
	C.PO_HEADER_ID = D.PO_HEADER_ID(+)
	AND E.VENDOR_ID(+) = D.VENDOR_ID
	AND F.VENDOR_SITE_ID(+) = D.VENDOR_SITE_ID
	AND D.PO_HEADER_ID = G.PO_HEADER_ID
	AND C.PO_LINE_ID = G.PO_LINE_ID
	AND D.ORG_ID = G.ORG_ID
	AND D.ORG_ID = C.ORG_ID
	----------------------------------------
	AND D.STYLE_ID = 100
	AND PLL.PO_HEADER_ID = D.PO_HEADER_ID(+)
	AND PLL.PO_LINE_ID = G.PO_LINE_ID(+)
	AND PLL.LINE_LOCATION_ID(+) = C.LINE_LOCATION_ID
)  temp """


def SubContractor_ETL():
    spark = fx.spark_app('RME_SubContractor','12g','4')
    RES = fx.connection(spark,'RES','RMEDB',SubContractor_query,'TEMP','ERP')
    fx.WriteFunction(RES ,load_connection_string,'RME_SubContractor_Report','overwrite',conn.mysql_username,conn.mysql_password)    

local_tz = pendulum.timezone("Europe/Helsinki")
default_args = {'owner' : 'gamal',
                'start_date' : datetime(2024,11,14, tzinfo=local_tz),"retries": 1,
                 "retry_delay": timedelta(minutes=30),'email': ['mohamed.Ghassan@rowad-rme.com'],
                  'email_on_failure': True,
                  'email_on_retry': False,}
dag = DAG('SubContractor',catchup=False,default_args=default_args,schedule_interval='0 5 * * *',tags=['4'])


SubContractorTask= PythonOperator(dag=dag,
                task_id = 'SubContractor',
                python_callable=SubContractor_ETL) 


SubContractorTask
