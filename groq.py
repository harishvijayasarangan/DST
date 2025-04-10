import requests
import os
import argparse

# Try to load from .env file if available, but don't require it
try:
    from dotenv import load_dotenv
    load_dotenv()  # This will not fail if .env doesn't exist
except ImportError:
    pass  # dotenv is not required if environment variables are set directly

# Get the API key from the environment
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    print("Warning: GROQ_API_KEY environment variable not found")

def query_groq(prompt, model="llama3-70b-8192"):
    headers = {
        'Authorization': f'Bearer {GROQ_API_KEY}',
        'Content-Type': 'application/json'
    }

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ]
    }

    response = requests.post('https://api.groq.com/openai/v1/chat/completions', headers=headers, json=data)
    return response.json()['choices'][0]['message']['content']

def list_available_models():
    print("Available Groq Models:")
    print("- llama3-70b-8192 (Default)")
    print("- llama3-8b-8192")
    print("- mixtral-8x7b-32768")
    print("- gemma-7b-it")
    print("- gemma-2-9b-it")
    print("- gemma-2-27b-it")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Query Groq API with your prompt')
    parser.add_argument('prompt', nargs='?', default="Explain quantum computing in simple terms.", 
                        help='The prompt to send to Groq API')
    parser.add_argument('--model', '-m', default="llama3-70b-8192", 
                        help='The model to use (default: llama3-70b-8192)')
    parser.add_argument('--list-models', '-l', action='store_true', 
                        help='List available models')
    
    args = parser.parse_args()
    
    if args.list_models:
        list_available_models()
    else:
        result = query_groq(args.prompt, args.model)
        print(result)
