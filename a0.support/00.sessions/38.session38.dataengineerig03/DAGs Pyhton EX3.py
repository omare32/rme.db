from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def extract_data():
    print('Extracting Data')


def tranform_data():
    print('Transforming Data')


def load_data():
    print('Loading Data')


default_args = {
    'owner': 'your_name',
    'start_date': datetime(2024, 2, 27),
    'retries': 1,
}


dag = DAG(
    'data_processing_dag',
    default_args=default_args,
    schedule_interval='@daily',
    catchup=False,
)

extract_task = PythonOperator(
    task_id='extract_task',
    python_callable=extract_data,
    dag=dag,
)


transform_task = PythonOperator(
    task_id='transform_task',
    python_callable=tranform_data,
    dag=dag,
)


load_task = PythonOperator(
    task_id='load_task',
    python_callable=load_data,
    dag=dag,
)

extract_task>>transform_task>>load_task


