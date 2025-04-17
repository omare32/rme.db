import pyodbc
import pandas as pd
from datetime import datetime

# Database connection parameters
SERVER = '10.10.11.242'
DATABASE = 'RME_TEST'
USERNAME = 'omar2'
PASSWORD = 'Omar_54321'

# Excel file path
EXCEL_FILE = r"D:\OneDrive\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db\03.warehouse\12.trial_balance\SWD_Periods_Trial_Balance___De_170425.xlsx"

# Create connection string
conn_str = (
    f'DRIVER={{SQL Server}};'
    f'SERVER={SERVER};'
    f'DATABASE={DATABASE};'
    f'UID={USERNAME};'
    f'PWD={PASSWORD};'
)

def connect_to_database():
    """Establish connection to the database"""
    try:
        conn = pyodbc.connect(conn_str)
        print("Successfully connected to the database!")
        return conn
    except Exception as e:
        print(f"Error connecting to database: {str(e)}")
        return None

def truncate_trial_balance(conn):
    """Delete all records from Trial_Balance table"""
    try:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM Trial_Balance")
        conn.commit()
        print("Successfully deleted existing data from Trial_Balance table")
    except Exception as e:
        print(f"Error deleting data: {str(e)}")
        conn.rollback()
        raise

def import_excel_data(conn):
    """Import data from Excel file to Trial_Balance table"""
    try:
        # Read Excel file
        print(f"Reading Excel file: {EXCEL_FILE}")
        df = pd.read_excel(EXCEL_FILE)
        print("\nExcel data preview:")
        print(df.head())
        print(f"\nTotal rows to import: {len(df)}")

        # Add Year column with current year
        current_year = datetime.now().year
        df.insert(0, 'Year', current_year)

        # Prepare data for import
        cursor = conn.cursor()
        
        # Insert data row by row
        for index, row in df.iterrows():
            sql = """
            INSERT INTO Trial_Balance (
                Year, [Account Code], [Account Name], Level, 
                CLARIFICATION, [Sub Account], [Value]
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            
            values = (
                row['Year'],
                row['Account Code'],
                row['Account Name'],
                row['Level'],
                row['CLARIFICATION'],
                row['Sub Account'],
                row['Value']
            )
            
            cursor.execute(sql, values)
            
            # Commit every 1000 rows
            if (index + 1) % 1000 == 0:
                conn.commit()
                print(f"Imported {index + 1} rows...")
        
        # Final commit
        conn.commit()
        print(f"\nSuccessfully imported {len(df)} rows into Trial_Balance table")
        
    except Exception as e:
        print(f"Error importing data: {str(e)}")
        conn.rollback()
        raise

def main():
    # Connect to the database
    conn = connect_to_database()
    if conn is None:
        return
    
    try:
        # Delete existing data
        truncate_trial_balance(conn)
        
        # Import new data
        import_excel_data(conn)
        
    except Exception as e:
        print(f"An error occurred: {str(e)}")
    finally:
        conn.close()

if __name__ == "__main__":
    main() 