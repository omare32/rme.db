import os
import mysql.connector
from mysql.connector import Error
from openai import OpenAI
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
    
    # Get just 3 important columns for testing
    cursor.execute("""
        SELECT COLUMN_NAME, DATA_TYPE
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_NAME = 'RME_PO_Follow_Up_Report'
        AND COLUMN_NAME IN ('POH_CREATION_DATE', 'LINE_AMOUNT', 'PO_NUMBER')
        ORDER BY ORDINAL_POSITION
    """)
    
    columns = cursor.fetchall()
    schema = "Table: RME_PO_Follow_Up_Report\nColumns:\n"
    for col in columns:
        schema += f"- {col[0]} ({col[1]})\n"
    print("Schema loaded successfully")
    
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Simple prompt with just schema
    prompt = f"""Given this schema:
{schema}
Write a query to show PO_NUMBER and LINE_AMOUNT for today's POs."""

    print("\nGenerating query...")
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a SQL query generator. Output only the SQL query, no explanations."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=100  # Keep it small
        )
        
        query = response.choices[0].message.content.strip()
        print("\nGenerated query:")
        print(query)
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    test_query()
