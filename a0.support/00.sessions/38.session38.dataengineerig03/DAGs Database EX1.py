from airflow import DAG
from airflow.providers.sqlite.operators.sqlite import SqliteOperator
from datetime import datetime

default_args = {
    'owner': 'your_name',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 27),
    'retries': 1,
}

dag = DAG(
    'sqlite_query_dag',
    default_args=default_args,
    description='A DAG for executing SQL queries on SQLite',
    schedule_interval=None,
    catchup=False,
)

# Define the SQL queries
create_table_query = """
CREATE TABLE IF NOT EXISTS example_table (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(50),
    age INT
)
"""

insert_data_query = """
INSERT INTO example_table (name, age) VALUES
    ('Alice', 28),
    ('Bob', 32),
    ('Charlie', 25)
"""

select_data_query = "SELECT * FROM example_table"

# Define tasks using SqliteOperator
create_table_task = SqliteOperator(
    task_id='create_table_task',
    sqlite_conn_id='sqlite_default',  # Connection ID configured in Airflow
    sql=create_table_query,
    dag=dag,
)

insert_data_task = SqliteOperator(
    task_id='insert_data_task',
    sqlite_conn_id='sqlite_default',
    sql=insert_data_query,
    dag=dag,
)

select_data_task = SqliteOperator(
    task_id='select_data_task',
    sqlite_conn_id='sqlite_default',
    sql=select_data_query,
    dag=dag,
)

# Set task dependencies
create_table_task >> insert_data_task >> select_data_task
