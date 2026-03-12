import requests

def test_ollama():
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": "phi3:mini",
        "prompt": "Say hello world in 3 words.",
        "stream": False
    }
    
    print("Connecting to Ollama at http://localhost:11434...")
    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        print("Response:", resp.json().get("response"))
    except Exception as e:
        print(f"Error: {e}")
        print("\nMake sure Ollama is running and you have pulled the model with 'ollama pull llama3'")

if __name__ == "__main__":
    test_ollama()
