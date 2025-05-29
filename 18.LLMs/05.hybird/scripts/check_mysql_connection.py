"""
MySQL Connection Test Script

This script tests the MySQL connection using the configuration from config.py
and counts the number of records in the po.pdfs table.
"""
import sys
import os

# Add the parent directory to the path to make the config module importable
script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, script_dir)

# Import configuration
from config import MYSQL_CONFIG
import mysql.connector
from mysql.connector import Error

def test_mysql_connection():
    """Test MySQL connection and count records in po.pdfs"""
    try:
        # Create connection using config
        conn = mysql.connector.connect(**MYSQL_CONFIG)
        
        if conn.is_connected():
            cursor = conn.cursor()
            
            # Count records in po.pdfs
            cursor.execute("SELECT COUNT(*) FROM `po.pdfs`")
            count = cursor.fetchone()[0]
            print(f"✅ Successfully connected to MySQL database: {MYSQL_CONFIG['database']}")
            print(f"📊 Total records in po.pdfs table: {count}")
            
            # Get table structure for verification
            cursor.execute("DESCRIBE `po.pdfs`")
            columns = cursor.fetchall()
            print("\nTable structure (po.pdfs):")
            for col in columns:
                print(f"- {col[0]}: {col[1]}")
            
            cursor.close()
            conn.close()
            return True
            
    except Error as e:
        print(f"❌ Error connecting to MySQL: {e}")
        return False
    
    return False

if __name__ == "__main__":
    print("🔍 Testing MySQL connection and checking po.pdfs table...")
    print(f"🔗 Connection details: mysql://{MYSQL_CONFIG['user']}@{MYSQL_CONFIG['host']}/{MYSQL_CONFIG['database']}")
    
    success = test_mysql_connection()
    
    if not success:
        print("\n❌ Connection failed. Please check:")
        print("1. MySQL server is running")
        print("2. Host, username, and password are correct")
        print("3. User has proper permissions")
        print("4. Table 'po.pdfs' exists in the database")
        print("\nCurrent configuration:", MYSQL_CONFIG)
