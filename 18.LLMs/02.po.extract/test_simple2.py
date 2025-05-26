import os
import mysql.connector
from mysql.connector import Error
from openai import OpenAI
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_query():
    # Connect to database
    try:
        connection = mysql.connector.connect(
            host='10.10.11.242',
            user='omar2',
            password='Omar_54321',
            database='RME_TEST'
        )
    except Error as e:
        print(f"Error connecting to database: {e}")
        return
    
    cursor = connection.cursor()
    
    # Get schema
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'RME_PO_Follow_Up_Report'
        ORDER BY ORDINAL_POSITION
    """)
    
    columns = cursor.fetchall()
    schema = "Table: RME_PO_Follow_Up_Report\nColumns:\n"
    for col in columns:
        schema += f"- {col[0]} ({col[1]})\n"
    print("Schema loaded successfully")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Calculate dates
    today = datetime.now()
    three_days_ago = today - timedelta(days=3)
    
    # Create prompt
    prompt = f"""Given this database schema:
{schema}

Generate a MySQL query that:
1. Shows all POs from the last 3 days
2. Today is {today.strftime('%Y-%m-%d')}, so include POs from {three_days_ago.strftime('%Y-%m-%d')} onwards
3. POH_CREATION_DATE can be compared directly with dates since it's in standard format
4. Some date fields can be NULL, but POH_CREATION_DATE is always populated
5. Sum the LINE_AMOUNT column for the total
6. Return ONLY the SQL query, nothing else"""

    print("\nGenerating query...")
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a SQL query generator. Output only the SQL query, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        query = response.choices[0].message.content.strip()
        print("\nGenerated query:")
        print(query)
        
        print("\nExecuting query...")
        cursor.execute(query)
        rows = cursor.fetchall()
        print("\nResults:")
        for row in rows:
            print(row)
            
    except Exception as e:
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    test_query()
