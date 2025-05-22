import requests
import json

# Ollama API URL
OLLAMA_API_URL = "http://10.10.12.202:11434"

def check_available_models():
    """Check what models are available in Ollama"""
    try:
        response = requests.get(f"{OLLAMA_API_URL}/api/tags")
        if response.status_code == 200:
            print("Successfully connected to Ollama API!")
            print("\nAvailable models:")
            models = response.json().get("models", [])
            for model in models:
                print(f"- {model['name']}")
            return True
        else:
            print(f"Error: Ollama API returned status code {response.status_code}")
            return False
    except Exception as e:
        print(f"Error connecting to Ollama API: {str(e)}")
        return False

def test_generate_api():
    """Test if we can generate text with the mistral model"""
    try:
        response = requests.post(
            f"{OLLAMA_API_URL}/api/generate",
            json={
                "model": "mistral",
                "prompt": "Hello, are you working?",
                "stream": False
            }
        )
        
        if response.status_code == 200:
            print("\nSuccessfully generated text with mistral model!")
            print(f"Response: {response.json().get('response', '')}")
            return True
        else:
            print(f"\nError: Generate API returned status code {response.status_code}")
            print(f"Response: {response.text}")
            return False
    except Exception as e:
        print(f"\nError calling generate API: {str(e)}")
        return False

if __name__ == "__main__":
    print("Testing Ollama API Connection")
    print("=" * 50)
    
    # Check available models
    models_available = check_available_models()
    
    # Test generate API if models are available
    if models_available:
        test_generate_api()
    
    print("\nTest completed.")
