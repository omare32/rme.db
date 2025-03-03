from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

def calculate_square(number):
    result = number ** 2
    print(f"The square of {number} is {result}")

def generate_tasks(numbers):
    dag = DAG(
        'dynamic_dag',
        default_args=default_args,
        schedule_interval=None,
        catchup=False,
    )

    tasks = []
    for num in numbers:
        task = PythonOperator(
            task_id=f'calculate_square_task_{num}',
            python_callable=calculate_square,
            op_args=[num],
            dag=dag,
        )
        tasks.append(task)

    return dag

default_args = {
    'owner': 'your_name',
    'start_date': datetime(2024, 2, 27),
    'retries': 1,
}

number_list = [2, 4, 6, 8, 10, 17]  # Change this list to your desired numbers

dynamic_dag = generate_tasks(number_list)
