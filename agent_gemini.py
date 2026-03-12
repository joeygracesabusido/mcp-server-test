import os
import json
import google.generativeai as genai
from mongodb_handler import MongoDBHandler

# Initialize MongoDB handler
try:
    db = MongoDBHandler()
except Exception as e:
    print(f"Warning: MongoDB not available: {e}")
    db = None

# Define MongoDB tools for Gemini
def mongo_query(collection: str, query: str):
    """Query MongoDB collection. query is a JSON string."""
    if not db: return "Error: MongoDB not connected"
    try:
        query_dict = json.loads(query)
        results = db.find_many(collection, query_dict, limit=10)
        return results
    except Exception as e:
        return f"Error: {e}"

def mongo_insert(collection: str, document: str):
    """Insert document into MongoDB collection. document is a JSON string."""
    if not db: return "Error: MongoDB not connected"
    try:
        doc_dict = json.loads(document)
        doc_id = db.insert_one(collection, doc_dict)
        return f"Inserted document with ID: {doc_id}"
    except Exception as e:
        return f"Error: {e}"

def mongo_collections():
    """Get all collections in the MongoDB database."""
    if not db: return "Error: MongoDB not connected"
    try:
        return db.get_collections()
    except Exception as e:
        return f"Error: {e}"

# Map tool names to functions
TOOLS = {
    "mongo_query": mongo_query,
    "mongo_insert": mongo_insert,
    "mongo_collections": mongo_collections
}

def setup_gemini():
    api_key = os.getenv("GOOGLE_API_KEY")
    if not api_key:
        raise ValueError("GOOGLE_API_KEY environment variable is not set")
    
    genai.configure(api_key=api_key)
    
    # We pass the functions directly to the model
    model = genai.GenerativeModel(
        model_name=os.getenv("GEMINI_MODEL", "gemini-1.5-flash"),
        tools=[mongo_query, mongo_insert, mongo_collections]
    )
    return model

def chat_loop():
    try:
        model = setup_gemini()
        chat = model.start_chat(enable_automatic_function_calling=True)
        
        print("\n🤖 Gemini Agent (with MongoDB access)")
        print("You can ask things like: 'Show me all users', 'What collections do we have?'")
        print("Type 'exit' to quit")
        print("-" * 40)
        
        while True:
            user_input = input("\nYou: ").strip()
            if user_input.lower() == 'exit':
                break
            if not user_input:
                continue
                
            response = chat.send_message(user_input)
            print(f"\nGemini: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    chat_loop()
