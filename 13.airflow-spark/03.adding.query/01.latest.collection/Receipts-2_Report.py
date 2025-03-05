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
from pyspark.sql.functions import to_date, col

load_connection_string = "jdbc:mysql://10.10.11.242:3306/RME_TEST?useUnicode=true&characterEncoding=UTF-8"

Receipts_2_Report_query = """ 
  SELECT DISTINCT
    ACR.cash_receipt_id AS receipt_id,
    ACR.receipt_number,
    trx_head.org_id,
    ppa.name AS receipt_prj_name,
    acr.attribute1 AS receipt_prj_code,
    ACR.amount AS receipt_amount,
    acr.RECEIPT_DATE,
    trx_head.CUSTOMER_TRX_ID,
    TRX_HEAD.TRX_NUMBER AS Inv_num,
    ARA.AMOUNT_APPLIED,
    ARA.attribute1,
    
    -- Aggregated Adjustments
    COALESCE((SELECT SUM(AMOUNT) FROM AR_ADJUSTMENTS_ALL adj
              JOIN AR_RECEIVABLES_TRX_all RT ON ADJ.RECEIVABLES_TRX_ID = RT.RECEIVABLES_TRX_ID
              WHERE TRX_HEAD.CUSTOMER_TRX_ID = adj.CUSTOMER_TRX_ID
              AND adj.status NOT IN ('R', 'U')
              AND RT.NAME IN ('With Holding Tax')), 0) AS With_Holding_Tax,
              
    COALESCE((SELECT SUM(AMOUNT) FROM AR_ADJUSTMENTS_ALL adj
              JOIN AR_RECEIVABLES_TRX_all RT ON ADJ.RECEIVABLES_TRX_ID = RT.RECEIVABLES_TRX_ID
              WHERE TRX_HEAD.CUSTOMER_TRX_ID = adj.CUSTOMER_TRX_ID
              AND adj.status NOT IN ('R', 'U')
              AND RT.NAME IN ('Stamps', 'Stamp Tax')), 0) AS Stamp,

    -- Other Aggregations
    TRX_HEAD.INVOICE_CURRENCY_CODE AS CURRENCY,

    -- Transaction Amount Calculation
    (SELECT SUM(NVL(tl.QUANTITY_INVOICED, 0) * NVL(tl.UNIT_SELLING_PRICE, 1))
     FROM RA_CUSTOMER_TRX_LINES_ALL TL
     WHERE tl.CUSTOMER_TRX_ID = TRX_HEAD.CUSTOMER_TRX_ID) AS Transaction_Amount,

    -- Tax Amount Calculation
    (SELECT SUM(NVL(tax_amt, 0)) 
     FROM ZX_LINES_V 
     WHERE APPLICATION_ID = '222' 
     AND ENTITY_CODE = 'TRANSACTIONS' 
     AND EVENT_CLASS_CODE = 'INVOICE' 
     AND TRX_ID = TRX_HEAD.CUSTOMER_TRX_ID 
     AND TRX_LEVEL_TYPE = 'LINE') AS Tax_Amount,

    -- Total After Tax Calculation
    (SELECT SUM(NVL(tl.QUANTITY_INVOICED, 0) * NVL(tl.UNIT_SELLING_PRICE, 1)) 
     FROM RA_CUSTOMER_TRX_LINES_ALL TL 
     WHERE tl.CUSTOMER_TRX_ID = TRX_HEAD.CUSTOMER_TRX_ID)
     + (SELECT SUM(NVL(tax_amt, 0)) 
        FROM ZX_LINES_V 
        WHERE APPLICATION_ID = '222' 
        AND ENTITY_CODE = 'TRANSACTIONS' 
        AND EVENT_CLASS_CODE = 'INVOICE' 
        AND TRX_ID = TRX_HEAD.CUSTOMER_TRX_ID 
        AND TRX_LEVEL_TYPE = 'LINE') AS TOTAL_After_Tax,

    -- Additional Aggregations
    ARA.status,
    NVL(TRX_HEAD.EXCHANGE_RATE, 1) AS RATE,
    TO_CHAR(TRX_HEAD.TRX_DATE, 'DD-MM-YYYY') AS TRX_DATE,
    ARA.apply_date,
    TO_DATE(TRX_HEAD.ATTRIBUTE2, 'YYYY/MM/DD HH24:MI:SS') AS DUE_DATE_DFF,

    -- Customer Details
    hcaa.ACCOUNT_NUMBER AS Customer_No,
    hcaa.ACCOUNT_NAME AS Customer_Name

FROM AR_CASH_RECEIPTS_ALL ACR
JOIN pa_projects_all ppa ON ppa.segment1 = acr.attribute1
LEFT JOIN AR_RECEIVABLE_APPLICATIONS_ALL ARA ON acr.cash_receipt_id = ara.cash_receipt_id
LEFT JOIN RA_CUSTOMER_TRX_ALL TRX_HEAD ON TRX_HEAD.CUSTOMER_TRX_ID = ara.APPLIED_CUSTOMER_TRX_ID
LEFT JOIN HZ_CUST_ACCOUNTS HCAA ON HCAA.CUST_ACCOUNT_ID = TRX_HEAD.BILL_TO_CUSTOMER_ID
LEFT JOIN HR_OPERATING_UNITS HRO ON acr.org_id = hro.organization_id

-- Apply organization filter
WHERE acr.org_id = 83

GROUP BY 
    ACR.cash_receipt_id, ACR.receipt_number, trx_head.org_id, ppa.name, acr.attribute1, 
    ACR.amount, acr.RECEIPT_DATE, ara.apply_date, trx_head.CUSTOMER_TRX_ID, 
    ara.APPLIED_CUSTOMER_TRX_ID, ara.cash_receipt_id, TRX_HEAD.INTERFACE_HEADER_ATTRIBUTE1,
    ARA.AMOUNT_APPLIED, ara.attribute1, ara.status, TRX_HEAD.EXCHANGE_RATE, 
    TRX_HEAD.CUST_TRX_TYPE_ID, TRX_HEAD.TRX_NUMBER, TRX_HEAD.TRX_DATE, 
    TRX_HEAD.INVOICE_CURRENCY_CODE, TRX_HEAD.ATTRIBUTE2, hcaa.ACCOUNT_NUMBER, 
    hcaa.ACCOUNT_NAME, ara.APPLIED_PAYMENT_SCHEDULE_ID, TRX_HEAD.TERM_ID;
"""


def Receipts_2_Report_ETL():
    spark = fx.spark_app('Receipts-2_Report', '2g', '2')
    RES = fx.connection(spark, 'RES', 'RMEDB', Receipts_2_Report_query, 'TEMP', 'ERP')
    
    if RES is not None:
        RES = RES.withColumn("DUE_DATE_DFF", to_date(col("DUE_DATE_DFF"), "yyyy-MM-dd"))
        fx.WriteFunction(RES, load_connection_string, 'Receipts-2_Report', 'overwrite', conn.mysql_username, conn.mysql_password)    

local_tz = pendulum.timezone("Europe/Helsinki")
default_args = {
    'owner': 'sama',
    'start_date': datetime(2024, 11, 14, tzinfo=local_tz),
    "retries": 1,
}

dag = DAG(
    'Receipts-2_Report',
    catchup=False,
    default_args=default_args,
    schedule_interval='0 1 * * *',
    tags=['5']
)

Receipts_2_Report_Task = PythonOperator(
    dag=dag,
    task_id='Receipts-2_Report',
    python_callable=Receipts_2_Report_ETL
)

Receipts_2_Report_Task
