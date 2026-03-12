import json
import requests
import re
from mongodb_handler import MongoDBHandler

# Initialize MongoDB handler
try:
    db = MongoDBHandler()
except Exception as e:
    print(f"Warning: MongoDB not available: {e}")
    db = None

SYSTEM_PROMPT = """You are a MongoDB database assistant for an HRIS system.
You have access to the following tools:

1. mongo_search_users(search_text: str)
   - Use this to find users by name or email.
   - Example: CALL: mongo_search_users({"search_text": "Jerome"})

2. mongo_query(collection: str, query: str, limit: int = 5)
   - Use this for general queries (e.g., listing all users, checking shifts).
   - Example: CALL: mongo_query({"collection": "users", "query": "{}", "limit": 5})

3. mongo_collections()
   - List all collections in the database.
   - Example: CALL: mongo_collections()

RULES:
- ONLY call one tool per turn.
- When you get the TOOL RESULT, summarize it for the user and STOP.
- Do NOT perform follow-up queries unless specifically asked.
- For security, password fields are automatically hidden.

FORMAT:
To call a tool, output ONLY: CALL: tool_name({"arg": "val"})
"""

def clean_data(data):
    """Remove sensitive fields like passwords from results."""
    if isinstance(data, list):
        return [clean_data(d) for d in data]
    if isinstance(data, dict):
        return {k: v for k, v in data.items() if k.lower() not in ['password', 'secret', 'token', 'key']}
    return data

def truncate_result(data, max_len=1500):
    cleaned = clean_data(data)
    text = json.dumps(cleaned)
    if len(text) > max_len:
        return text[:max_len] + "... [TRUNCATED]"
    return text

def call_mongo_search_users(search_text=None, **kwargs):
    if not db: return "Error: MongoDB not connected"
    if not search_text: return "Error: Missing search_text"
    try:
        results = db.search_users(search_text, limit=5)
        return truncate_result(results)
    except Exception as e:
        return f"Error: {e}"

def call_mongo_query(collection=None, query=None, limit=5, **kwargs):
    if not db: return "Error: MongoDB not connected"
    if not collection: return "Error: Missing 'collection'"
    try:
        q_dict = json.loads(query) if isinstance(query, str) else (query or {})
        results = db.find_many(collection, q_dict, limit=min(int(limit), 10))
        return truncate_result(results)
    except Exception as e:
        return f"Error: {e}"

def call_mongo_collections():
    if not db: return "Error: MongoDB not connected"
    try:
        return db.get_collections()
    except Exception as e:
        return f"Error: {e}"

TOOL_MAP = {
    "mongo_search_users": call_mongo_search_users,
    "mongo_query": call_mongo_query,
    "mongo_collections": call_mongo_collections
}

def ollama_chat_no_tools(messages, model="minimax-m2.5:cloud", url="http://localhost:11434/api/generate", depth=0):
    if depth > 3:
        return "The request was too complex. Please try a simpler question."

    prompt = SYSTEM_PROMPT + "\n"
    for m in messages[-4:]:
        role = "User" if m["role"] == "user" else "Assistant"
        prompt += f"\n{role}: {m['content']}"
    prompt += "\nAssistant: "

    try:
        # Increased timeout for heavier models like Qwen 2.5
        resp = requests.post(url, json={"model": model, "prompt": prompt, "stream": True}, timeout=300)
        if resp.status_code != 200: return f"API Error: {resp.status_code}"
        
        full_content = ""
        for line in resp.iter_lines():
            if line:
                chunk = json.loads(line)
                if "response" in chunk:
                    content_chunk = chunk["response"]
                    full_content += content_chunk
                    print(content_chunk, end="", flush=True)
                if chunk.get("done"):
                    break
        
        content = full_content.strip()
        print() # New line after stream
        if not content: return "The model returned an empty response. Try asking again."

        match = re.search(r"CALL:\s*(\w+)\((.*)\)", content)
        if match:
            func_name, args_str = match.group(1), match.group(2).strip()
            print(f"🛠️  Calling: {func_name}({args_str})")
            try:
                # Basic JSON fix for common model mistakes
                args_str = args_str.replace("'", '"')
                args = json.loads(args_str) if args_str else {}
                if func_name in TOOL_MAP:
                    result = TOOL_MAP[func_name](**args)
                    messages.append({"role": "assistant", "content": content})
                    messages.append({"role": "user", "content": f"TOOL RESULT: {result}"})
                    return ollama_chat_no_tools(messages, model, url, depth + 1)
            except Exception as e:
                return f"Error parsing tool call from model: {e}\nRaw output: {content}"
        return content
    except Exception as e:
        return f"Connection Error: {e}"

def chat_loop(model="minimax-m2.5:cloud"):
    print(f"\n🤖 HRIS MongoDB Agent (Model: {model})\nType 'exit' to quit\n" + "-"*40)
    messages = []
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() == 'exit': break
            if not user_input: continue
            messages.append({"role": "user", "content": user_input})
            print("\nOllama: ", end="", flush=True)
            response = ollama_chat_no_tools(messages, model=model)
            # Response already printed via streaming
            messages.append({"role": "assistant", "content": response})
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    chat_loop()
