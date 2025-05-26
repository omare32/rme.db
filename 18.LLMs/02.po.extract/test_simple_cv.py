import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_query():
    # Initialize OpenAI client
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    print("\nTesting with CV-style prompt...")
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{
                "role": "system",
                "content": """Extract the following information in JSON format:
                    - name: Full name
                    - age: Age in years
                    - city: City of residence"""
            }, {
                "role": "user",
                "content": "John Smith is 25 years old and lives in New York."
            }],
            temperature=0.1,
            max_tokens=100
        )
        
        result = response.choices[0].message.content.strip()
        print("\nGenerated response:")
        print(result)
            
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    test_query()
