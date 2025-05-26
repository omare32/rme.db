import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_query():
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    # Simple test with minimal SQL prompt
    print("\nTesting with minimal prompt...")
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a SQL query generator."},
                {"role": "user", "content": "Write a simple SQL query to select all columns from a table named 'users'"}
            ],
            temperature=0.1,
            max_tokens=50  # Much smaller limit
        )
        
        query = response.choices[0].message.content.strip()
        print("\nGenerated query:")
        print(query)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_query()
