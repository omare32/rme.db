from airflow import DAG
from airflow.operators.email import EmailOperator
from airflow.operators.python import PythonOperator
from airflow.providers.sqlite.hooks.sqlite import SqliteHook
from datetime import datetime
import csv

default_args = {
    'owner': 'your_name',
    'depends_on_past': False,
    'start_date': datetime(2024, 2, 27),
    'retries': 1,
}


dag = DAG(
    'sqlite_query_email_dag',
    default_args=default_args,
    schedule_interval=None,
    catchup=False,
)

# Define the SQL query
select_data_query = "SELECT * FROM example_table"
output_file_path = "/mnt/d/Airflow_Outputs/query_results.csv" 

def execute_and_save_query_to_csv(sql,conn_id, output_file,**kwargs):
    # Establish connection to SQLite database using sqlite_default connection
    sqlite_hook = SqliteHook(sqlite_conn_id=conn_id)

    # Execute the SQL query
    connection = sqlite_hook.get_conn()
    cursor = connection.cursor()
    cursor.execute(sql)

    # Fetch all rows from the query result
    rows = cursor.fetchall()

    # Close the cursor and connection
    cursor.close()
    connection.close()

    # Write query results to a CSV file
    with open(output_file, 'w', newline='') as csvfile:
        csv_writer = csv.writer(csvfile)
        csv_writer.writerows(rows)



# Define tasks using PythonOperator
select_data_task = PythonOperator(
    task_id='select_data_task',
    python_callable=execute_and_save_query_to_csv,
    op_kwargs={'sql': select_data_query, 'conn_id': 'sqlite_default', 'output_file': output_file_path},
    dag=dag,
)



# Define task for sending email
email_subject = "Query Results from SQLite Database"
email_body = "Please find the query results attached."

email_task = EmailOperator(
    task_id='send_email_task',
    to='ahmedhassanezz02@gmail.com',
    subject=email_subject,
    html_content=email_body,
    files=['/mnt/d/Airflow_Outputs/query_results.csv'],  # Attach the query results here
    dag=dag,
)

# Set task dependencies
select_data_task >> email_task
