import pandas as pd
import numpy as np
import os
import sys
import subprocess
from datetime import datetime

# Install required packages if not available
try:
    import openpyxl
except ImportError:
    print("Installing missing dependency: openpyxl")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "openpyxl"])
    print("openpyxl installed successfully.")

try:
    import sqlalchemy
    from sqlalchemy import create_engine, text, types
except ImportError:
    print("Installing missing dependency: sqlalchemy")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "sqlalchemy"])
    print("sqlalchemy installed successfully.")
    from sqlalchemy import create_engine, text, types

try:
    import psycopg2
except ImportError:
    print("Installing missing dependency: psycopg2")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "psycopg2-binary"])
    print("psycopg2 installed successfully.")

# Define the path to the Excel file
excel_path = r"C:\Users\Omar Essam2\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db\18.llms\07.sql.ai\01.erp.table\RME_PO_Follow_up_180625.xlsx"

# PostgreSQL connection parameters - MODIFY THESE TO MATCH YOUR DATABASE
DB_PARAMS = {
    'host': 'localhost',     # Your PostgreSQL server address
    'port': '5432',         # Default PostgreSQL port
    'user': 'postgres',     # Your PostgreSQL username
    'password': 'admin',    # Your PostgreSQL password
    'database': 'postgres', # Your PostgreSQL database name
    'schema': 'public'      # Schema where you want to create the table
}

# Table name for the imported data
TABLE_NAME = "po_followup_from_erp"

# Function to create database connection
def get_db_connection():
    try:
        # Create connection string
        conn_string = f"postgresql://{DB_PARAMS['user']}:{DB_PARAMS['password']}@{DB_PARAMS['host']}:{DB_PARAMS['port']}/{DB_PARAMS['database']}"
        engine = create_engine(conn_string)
        return engine
    except Exception as e:
        print(f"Error connecting to database: {e}")
        sys.exit(1)

# Check if the file exists
if not os.path.exists(excel_path):
    print(f"Error: The file {excel_path} does not exist.")
    sys.exit(1)

# Main function to process Excel file and import to PostgreSQL
def import_data_to_postgres():
    try:
        print("Reading Excel file...")
        df = pd.read_excel(excel_path)
        print(f"Successfully read Excel file with {df.shape[0]} rows and {df.shape[1]} columns.")

        # Clean column names - replace spaces with underscores and convert to lowercase
        df.columns = [col.strip().lower().replace(' ', '_').replace('-', '_').replace('.', '').replace('(', '').replace(')', '') for col in df.columns]

        print("\nCleaned column names:")
        for i, col in enumerate(df.columns):
            print(f"{i+1}. {col}")

        # Define date columns
        date_columns = ['creation_date', 'approved_date']

        # Convert date columns to proper datetime format
        for col in date_columns:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
                print(f"Converted {col} to datetime")

        # Replace NaN values with None for proper SQL NULL handling
        df = df.replace({np.nan: None})

        # Define data types for SQLAlchemy
        dtype_mapping = {}
        for col in df.columns:
            if col in date_columns:
                dtype_mapping[col] = types.DateTime()
            elif df[col].dtype == 'int64':
                dtype_mapping[col] = types.BigInteger()
            elif df[col].dtype == 'float64':
                dtype_mapping[col] = types.Float()
            elif col in ['description', 'po_comments']:
                # Use Text type for potentially long text fields
                dtype_mapping[col] = types.Text()
            else:
                dtype_mapping[col] = types.String(length=255)

        # Create database connection
        engine = get_db_connection()
        schema_name = DB_PARAMS['schema']

        print(f"Using schema: {schema_name} and table: {TABLE_NAME}")

        # First drop the table if it exists
        with engine.connect() as connection:
            try:
                connection.execute(text(f"DROP TABLE IF EXISTS {schema_name}.{TABLE_NAME}"))
                connection.commit()
                print(f"Dropped existing table {schema_name}.{TABLE_NAME}")
            except Exception as e:
                print(f"Warning when dropping table: {e}")
                connection.rollback()

        # Then create the table and import data
        print(f"Creating new table with {len(df.columns)} columns and importing {len(df)} rows...")
        df.to_sql(
            name=TABLE_NAME,
            con=engine,
            schema=schema_name,
            if_exists='replace',
            index=False,
            dtype=dtype_mapping,
            chunksize=1000  # Import in chunks to avoid memory issues
        )

        # Add a primary key and create indexes
        with engine.connect() as connection:
            try:
                connection.execute(text(f"ALTER TABLE {schema_name}.{TABLE_NAME} ADD COLUMN id SERIAL PRIMARY KEY"))
                connection.commit()
                print("Added SERIAL PRIMARY KEY column 'id'")

                # Create indexes on common query columns
                for col in ['po_num', 'vendor', 'creation_date']:
                    if col in df.columns:
                        connection.execute(text(f"CREATE INDEX idx_{TABLE_NAME}_{col.replace('.', '_')} ON {schema_name}.{TABLE_NAME} ({col})"))
                        connection.commit()
                        print(f"Created index on column '{col}'")
            except Exception as e:
                print(f"Error when adding primary key or indexes: {e}")
                connection.rollback()

        # Print table summary
        with engine.connect() as connection:
            # Get row count
            result = connection.execute(text(f"SELECT COUNT(*) FROM {schema_name}.{TABLE_NAME}"))
            row_count = result.scalar()
            print(f"\nTotal rows in table: {row_count}")

            # Sample query to show data was imported correctly
            print("\nSample data from imported table (first 3 rows):")
            result = connection.execute(text(f"""
                SELECT po_num, vendor, description, amount_egp, creation_date 
                FROM {schema_name}.{TABLE_NAME} 
                LIMIT 3
            """))
            columns = result.keys()
            rows = result.fetchall()

            # Print column headers
            header = "| " + " | ".join(str(col) for col in columns) + " |"
            print(header)
            print("-" * len(header))

            # Print rows
            for row in rows:
                print("| " + " | ".join(str(val)[:20] + ("..." if val and len(str(val)) > 20 else "") for val in row) + " |")

        print(f"\nSuccessfully imported {df.shape[0]} rows to table '{TABLE_NAME}' in schema '{schema_name}'.")
        print("\nSuggested SQL for rev.19 AI:")
        print(f"""
        SELECT 
            po_num, project_name, vendor, description, 
            quantity, unit_price, amount_egp, creation_date, 
            po_status, qty_received, qty_delivered
        FROM {schema_name}.{TABLE_NAME}
        WHERE creation_date >= '2024-01-01'
        ORDER BY creation_date DESC
        LIMIT 100;
        """)

        print("\nImport process completed successfully.")

    except Exception as e:
        print(f"Error during import process: {e}")
        import traceback
        print(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    import_data_to_postgres()
