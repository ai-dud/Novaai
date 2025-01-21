import requests
import json
import socket
import time

class OllamaClient:
    def __init__(self, base_url="http://192.168.31.184:11434"):
        self.base_urls = [
            "http://localhost:11434",
            "http://127.0.0.1:11434",
            "http://192.168.31.184:11434"
        ]
        self.base_url = self.find_working_server()
        self.timeout = 60  # Increased timeout to 60 seconds
        self.max_retries = 3
        self.retry_delay = 2

    def make_request(self, method, endpoint, **kwargs):
        """Make a request with retry logic"""
        for attempt in range(self.max_retries):
            try:
                if attempt > 0:
                    print(f"Retry attempt {attempt + 1}/{self.max_retries}")
                    time.sleep(self.retry_delay)
                
                if not self.is_running():
                    self.base_url = self.find_working_server()
                    if not self.base_url:
                        continue

                # Set shorter timeout for initial connection
                kwargs['timeout'] = (5, kwargs.get('timeout', self.timeout))
                
                url = f"{self.base_url}/{endpoint.lstrip('/')}"
                response = requests.request(method, url, **kwargs)
                
                if response.status_code == 200:
                    return response
                
                print(f"Request failed with status {response.status_code}: {response.text}")
                
            except requests.exceptions.Timeout:
                print(f"Request timed out on attempt {attempt + 1}")
                if attempt == self.max_retries - 1:
                    return None
                continue
            
        return None

    def find_working_server(self):
        """Try different URLs to find a working Ollama server"""
        for url in self.base_urls:
            try:
                response = requests.get(f"{url}/api/version", timeout=2)
                if response.status_code == 200:
                    print(f"Connected to Ollama at {url}")
                    return url
            except:
                continue
        print("Warning: Could not connect to any Ollama server")
        return None

    def is_running(self):
        """Check if Ollama server is running"""
        try:
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            return response.status_code == 200
        except:
            return False

    def generate(self, prompt, model="llama3.2"):
        """Generate response using Ollama"""
        if not prompt:
            return "Please provide a question or prompt."

        if not self.base_url:
            return "Cannot connect to Ollama server. Please check if it's running."

        try:
            print(f"Sending request to model {model}...")
            response = self.make_request(
                'post',
                'api/generate',
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "top_k": 40,
                        "num_predict": 100  # Limit response length
                    }
                },
                timeout=30  # Shorter timeout for generation
            )

            if response:
                result = response.json()
                if 'response' in result:
                    return result['response'].strip()
            
            return "I apologize, but I'm having trouble connecting to my knowledge base right now. Please try again in a moment."
            
        except Exception as e:
            print(f"Error in generate: {str(e)}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."

def main():
    # Create client instance
    client = OllamaClient()
    
    try:        
        # First, let's check available models
        print("\nChecking available models...")
        models = client.get_models()
        if models:
            print("Available models:", models)
            # Try to use the 1b model as it's smaller
            model_to_use = "llama3.2" if "llama3.2" in models else models[0]
            print(f"Using model: {model_to_use}")
        else:
            print("No models found. Cannot proceed.")
            return
        
        # Example usage
        questions = [
            "Who was the first President of India?",
            "What is artificial intelligence?",
            "Tell me about Python programming"
        ]
        
        for prompt in questions:
            print(f"\nAsking: {prompt}")
            response = client.generate(prompt, model=model_to_use)
            print(f"Response: {response}")
            print("-" * 50)
        
    except Exception as e:
        print(f"Error in main: {str(e)}")

if __name__ == "__main__":
    main()
