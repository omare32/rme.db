import mysql.connector as mysql
import pandas as pd
import numpy as np
from mysql.connector import Error

# Database connection parameters
HOST = '10.10.11.242'
DATABASE = 'RME_TEST'
USERNAME = 'omar2'
PASSWORD = 'Omar_54321'

# Excel file path
EXCEL_FILE = r"D:\OneDrive\OneDrive - Rowad Modern Engineering\x004 Data Science\03.rme.db\00.repo\rme.db\03.warehouse\12.trial_balance\SWD_Periods_Trial_Balance___De_170425.xlsx"

def get_excel_totals():
    """Get totals from Excel file for Jan-Apr"""
    try:
        print("\nReading Excel file...")
        df = pd.read_excel(EXCEL_FILE)
        
        # Calculate totals for each month
        totals = {}
        for month in ['Jan', 'Feb', 'Mar', 'Apr']:
            # Convert to numeric and sum, ignoring NaN values
            total = pd.to_numeric(df[month], errors='coerce').sum()
            totals[month] = total
            print(f"Excel {month} total: {total:,.2f}")
        
        return totals
    
    except Exception as e:
        print(f"Error reading Excel file: {str(e)}")
        return None

def get_mysql_totals():
    """Get totals from MySQL database for Jan-Apr"""
    try:
        # Connect to database
        conn = mysql.connect(
            host=HOST,
            user=USERNAME,
            password=PASSWORD,
            database=DATABASE
        )
        
        cursor = conn.cursor(dictionary=True)
        
        # Calculate totals for each month
        totals = {}
        for month in ['Jan', 'Feb', 'Mar', 'Apr']:
            cursor.execute(f"""
                SELECT SUM(CAST({month} AS DECIMAL(20,2))) as total
                FROM Trial_Balance
            """)
            result = cursor.fetchone()
            total = float(result['total']) if result['total'] else 0
            totals[month] = total
            print(f"MySQL {month} total: {total:,.2f}")
        
        return totals
    
    except Error as e:
        print(f"Error querying database: {str(e)}")
        return None
    finally:
        if 'conn' in locals() and conn.is_connected():
            cursor.close()
            conn.close()

def compare_totals(excel_totals, mysql_totals):
    """Compare totals between Excel and MySQL"""
    if not excel_totals or not mysql_totals:
        print("\nCannot compare totals due to errors")
        return
    
    print("\nComparing totals:")
    print("-" * 60)
    print(f"{'Month':<10} {'Excel Total':>15} {'MySQL Total':>15} {'Difference':>15}")
    print("-" * 60)
    
    all_match = True
    for month in ['Jan', 'Feb', 'Mar', 'Apr']:
        excel_total = excel_totals[month]
        mysql_total = mysql_totals[month]
        difference = abs(excel_total - mysql_total)
        
        # Use a small threshold for float comparison
        matches = difference < 0.01
        
        print(f"{month:<10} {excel_total:>15,.2f} {mysql_total:>15,.2f} {difference:>15,.2f} {'✓' if matches else '❌'}")
        
        if not matches:
            all_match = False
    
    print("\nVerification Result:")
    if all_match:
        print("✅ All totals match between Excel and MySQL!")
    else:
        print("❌ Some totals do not match. Please check the differences above.")

def main():
    print("Verifying totals between Excel and MySQL...")
    
    # Get totals from both sources
    excel_totals = get_excel_totals()
    mysql_totals = get_mysql_totals()
    
    # Compare the totals
    compare_totals(excel_totals, mysql_totals)

if __name__ == "__main__":
    main() 