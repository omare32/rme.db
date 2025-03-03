from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def print_message():
    print("Hello, this is the print_message task!")

def calculate_square(number):
    result = number ** 2
    print(f"The square of {number} is {result}")



default_args = {
    'owner': 'your_name',
    'start_date': datetime(2024, 2, 27),
    'retries': 1,
}

dag = DAG(
    'simple_dag',
    default_args=default_args,
    schedule_interval=None
)

print_message_task = PythonOperator(
    task_id='print_message_task',
    python_callable=print_message,
    dag=dag,
)

number_to_calculate = 5

calculate_square_task = PythonOperator(
    task_id='calculate_square_task',
    python_callable=calculate_square,
    op_kwargs={'number': number_to_calculate},
    dag=dag,
)



print_message_task >> calculate_square_task
