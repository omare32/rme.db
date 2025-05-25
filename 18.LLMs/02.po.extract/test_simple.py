import os
import openai
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_query():
    # Connect to database
    connection = mysql.connector.connect(
        host='10.10.11.242',
        user='omar2',
        password='Omar_54321',
        database='RME_TEST'
    )
    cursor = connection.cursor()
    
    # Get schema
    cursor.execute("DESCRIBE RME_PO_Follow_Up_Report")
    columns = cursor.fetchall()
    schema = "Table: RME_PO_Follow_Up_Report\nColumns:\n"
    for col in columns:
        schema += f"- {col[0]} ({col[1]})\n"
    print("Schema loaded successfully")
    
    # Set up OpenAI
    openai.api_key = os.getenv('OPENAI_API_KEY')
    if not openai.api_key:
        print("Error: OPENAI_API_KEY not found in .env file")
        return
    
    # Calculate dates
    today = datetime.now()
    three_days_ago = today - timedelta(days=3)
    date_example = three_days_ago.strftime("%d-%b-%y").upper()
    
    # Generate query
    prompt = f"""Given this database schema:
{schema}

Write a MySQL query to find the total amount of all POs in the last 3 days.
Important notes:
1. POH_CREATION_DATE is stored as text in 'DD-MON-YY' format (e.g., '25-MAY-23')
2. Today is {today.strftime("%d-%b-%y").upper()}, so include POs from {date_example} onwards
3. Use STR_TO_DATE to convert POH_CREATION_DATE for comparison
4. Sum the LINE_AMOUNT column for the total
5. Return ONLY the SQL query, nothing else"""

    try:
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a SQL query generator. Output only the SQL query, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0
        )
        
        query = response.choices[0].message.content.strip()
        print("\nGenerated Query:")
        print(query)
        
        print("\nExecuting query...")
        cursor.execute(query)
        results = cursor.fetchall()
        print("\nResults:")
        for row in results:
            print(row)
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    test_query()
