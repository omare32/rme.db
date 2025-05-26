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
    try:
        connection = mysql.connector.connect(
            host='10.10.11.242',
            user='omar2',
            password='Omar_54321',
            database='RME_TEST'
        )
        cursor = connection.cursor()
    except Error as e:
        print(f"Database error: {e}")
        return
        
    # Calculate dates
    today = datetime.now()
    three_days_ago = today - timedelta(days=3)
    
    # Create a simple text prompt
    prompt = f"""Write a MySQL query to show total purchase amounts by vendor and project from {three_days_ago.strftime('%Y-%m-%d')} to {today.strftime('%Y-%m-%d')}. Show only top 10 vendors.

The table name is 'po_followup_for_gpt' and it has these columns:
- creation_date: when the purchase was made (it's a DATE)
- vendor_name: who we bought from
- line_amount: how much we paid
- po_number: the purchase order number
- project_name: which project this purchase was for

I want to:
1. Look at purchases from May 22nd onwards
2. Add up all amounts for each vendor AND project combination
3. Show the vendor name, project name, and total amount
4. Sort by total amount from highest to lowest"""

    print("Sending prompt to GPT...")
    
    # Set OpenAI key
    openai.api_key = os.getenv('OPENAI_API_KEY')
    
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "user",
                "content": prompt
            }],
            temperature=0.1,
            max_tokens=100
        )
        
        query = response.choices[0].message.content.strip()
        
        # Clean the query by removing markdown code blocks
        query = query.replace('```sql', '').replace('```', '').strip()
        print("\nGPT suggested this query:")
        print(query)
        
        # Execute the query
        print("\nExecuting query...")
        cursor.execute(query)
        rows = cursor.fetchall()
        
        # Print results
        print("\nResults:")
        print("Vendor Name | Project Name | Total Amount")
        print("-" * 80)
        for row in rows:
            print(f"{row[0]} | {row[1]} | {row[2]:,.2f}")
            
    except Exception as e:
        print(f"Error: {str(e)}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    test_query()
