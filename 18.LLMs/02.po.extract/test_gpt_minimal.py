import os
from openai import OpenAI
from dotenv import load_dotenv

def test_gpt():
    # Remove any existing proxy settings
    if 'HTTP_PROXY' in os.environ:
        del os.environ['HTTP_PROXY']
    if 'HTTPS_PROXY' in os.environ:
        del os.environ['HTTPS_PROXY']
    
    # Load API key
    load_dotenv()
    api_key = os.getenv('OPENAI_API_KEY')
    
    if not api_key:
        print("No API key found in .env file")
        return
        
    print(f"API key loaded (starts with: {api_key[:4]})")
    
    try:
        # Create OpenAI client with just the API key
        client = OpenAI(
            api_key=api_key
        )
        
        print("\nTesting API with simple message...")
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Say hi"}],
            max_tokens=10  # Keep it very short
        )
        
        print(f"\nResponse received: {response.choices[0].message.content}")
        print("API connection successful!")
        
    except Exception as e:
        print(f"\nError: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_gpt()
