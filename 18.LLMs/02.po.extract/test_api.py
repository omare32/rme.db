import os
from openai import OpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api():
    # Get API key
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("Error: No API key found in .env file")
        return
        
    print(f"API key starts with: {api_key[:4]}...")
    
    try:
        # Create client with short timeout
        client = OpenAI(
            api_key=api_key,
            timeout=5.0,
            max_retries=0
        )
        
        # Try a simple API call
        print("\nTesting API connection...")
        response = client.models.list()
        print("Success! Available models:")
        for model in response:
            print(f"- {model.id}")
            
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_api()
