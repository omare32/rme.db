import os
from openai import OpenAI
import httpx
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
    print("\nTrying to load API key from .env...")
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"API key loaded: {'Yes' if api_key else 'No'}")
    if api_key:
        # Print first and last 4 chars of key
        print(f"Key starts with: {api_key[:4]}...{api_key[-4:]}")
    # Try without proxy first
    client = OpenAI(
        api_key=api_key,
        timeout=10.0,  # 10 second timeout
        max_retries=1
    )
    if not api_key:
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
1. POH_CREATION_DATE is stored in 'YYYY-MM-DD' format (e.g., '2023-05-25')
2. Today is {today.strftime('%Y-%m-%d')}, so include POs from {three_days_ago.strftime('%Y-%m-%d')} onwards
3. POH_CREATION_DATE can be compared directly with dates since it's in standard format
4. Sum the LINE_AMOUNT column for the total
5. Return ONLY the SQL query, nothing else"""

    print("\nGenerating query...")
    try:
        print("Calling OpenAI API...")
        try:
            print("Making API request...")
            try:
                print("Creating request...")
                request = client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a SQL query generator. Output only the SQL query, no explanations."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0,
                    stream=True  # Let's try streaming to see if we get better error info
                )
                print("Request created, starting stream...")
                
                # Process the stream
                response_text = ""
                try:
                    for chunk in request:
                        if chunk and chunk.choices and chunk.choices[0].delta.content:
                            response_text += chunk.choices[0].delta.content
                    print("Stream completed successfully")
                except Exception as stream_error:
                    print(f"Stream error: {str(stream_error)}")
                    raise
                    
                print("Got response from OpenAI")
                response = response_text
            except Exception as inner_error:
                print(f"Inner API Error: {str(inner_error)}")
                import traceback
                traceback.print_exc()
                raise
        except Exception as e:
            print(f"OpenAI API Error: {str(e)}")
            import traceback
            traceback.print_exc()
            return
        
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
