import pandas as pd
import numpy as np
import os
import psycopg2
from sqlalchemy import create_engine, types
from datetime import datetime
import sys
from django.conf import settings
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

# Get database connection parameters from Django settings
db_settings = settings.DATABASES['default']

# Define the path to the Excel file
excel_path = r"C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db\18.llms\07.sql.ai\01.erp.table\RME_PO_Follow_up_180625.xlsx"

# Function to create database connection
def get_db_connection():
    try:
        conn_string = f"postgresql://{db_settings['USER']}:{db_settings['PASSWORD']}@{db_settings['HOST']}:{db_settings['PORT']}/{db_settings['NAME']}"
        engine = create_engine(conn_string)
        return engine
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

# Check if the file exists
if not os.path.exists(excel_path):
    print(f"Error: The file {excel_path} does not exist.")
    sys.exit(1)

# Read the Excel file
try:
    print("Reading Excel file...")
    df = pd.read_excel(excel_path)
    print(f"Successfully read Excel file with {df.shape[0]} rows and {df.shape[1]} columns.")

    # Clean column names - replace spaces with underscores and convert to lowercase
    df.columns = [col.strip().lower().replace(' ', '_').replace('-', '_') for col in df.columns]

    # Handle potential data type issues
    # Convert date columns to proper datetime format
    date_columns = [col for col in df.columns if 'date' in col.lower()]
    for col in date_columns:
        df[col] = pd.to_datetime(df[col], errors='coerce')

    # Replace NaN values with None for proper SQL NULL handling
    df = df.replace({np.nan: None})

    # Create database connection
    engine = get_db_connection()

    # Define data types for SQLAlchemy
    dtype_mapping = {}
    for col in df.columns:
        if col in date_columns:
            dtype_mapping[col] = types.DateTime()
        elif df[col].dtype == 'int64':
            dtype_mapping[col] = types.BigInteger()
        elif df[col].dtype == 'float64':
            dtype_mapping[col] = types.Float()
        else:
            dtype_mapping[col] = types.String(length=255)

    # Create table and import data
    print("Importing data to PostgreSQL...")
    table_name = "po_followup_from_erp"
    schema_name = db_settings.get('OPTIONS', {}).get('options', '-c search_path=public').split('=')[1]

    # First drop the table if it exists
    with engine.connect() as connection:
        connection.execute(f"DROP TABLE IF EXISTS {schema_name}.{table_name};")
        connection.commit()

    # Then create the table and import data
    df.to_sql(
        name=table_name,
        con=engine,
        schema=schema_name,
        if_exists='replace',
        index=False,
        dtype=dtype_mapping
    )

    # Add a primary key
    with engine.connect() as connection:
        connection.execute(f"ALTER TABLE {schema_name}.{table_name} ADD COLUMN id SERIAL PRIMARY KEY;")
        connection.commit()

    print(f"Successfully imported {df.shape[0]} rows to table '{table_name}' in schema '{schema_name}'.")

except Exception as e:
    print(f"Error during import process: {e}")
    sys.exit(1)

print("Import process completed successfully.")
