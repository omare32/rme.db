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
    
    # Get schema (much simpler now)
    schema = """Table: po_followup_for_gpt
Columns:
- po_number (VARCHAR): Purchase Order number
- creation_date (DATE): When the PO was created
- line_amount (DECIMAL): Amount for this line item
- vendor_name (VARCHAR): Name of the vendor"""
    
    print("Using simplified schema")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Calculate dates
    today = datetime.now()
    three_days_ago = today - timedelta(days=3)
    
    # Create prompt (much simpler now)
    prompt = f"""Using this schema:
{schema}

Write a MySQL query that:
1. Shows POs created in the last 3 days (from {three_days_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')})
2. Groups by vendor_name
3. Shows total amount per vendor
4. Orders by total amount descending"""

    print("\nGenerating query...")
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a SQL query generator. Output only the SQL query, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=200  # Much smaller now
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
