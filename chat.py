#!/usr/bin/env python3
"""
Simple chat interface for the MCP Server
Supports both Gemini, Ollama, and MongoDB
"""

import sys
import os
import json
from mongodb_handler import MongoDBHandler

def chat_with_gemini_agent():
    """Interactive chat with Gemini Agent (Tool Calling)"""
    import agent_gemini
    agent_gemini.chat_loop()

def chat_with_ollama_agent(model="minimax-m2.5:cloud"):
    """Interactive chat with Ollama Agent (Manual Tool Calling)"""
    import agent_ollama
    agent_ollama.chat_loop(model=model)

def chat_with_gemini():
    """Interactive chat with Gemini (Standard)"""
    from main import gemini_chat

def chat_with_ollama(model: str = "minimax-m2.5:cloud"):
    """Interactive chat with Ollama"""
    print(f"🤖 Ollama Chat with model: {model} (type 'exit' to quit)")
    print("Make sure Ollama is running on http://localhost:11434")
    print("MongoDB commands: /mongo <command> <args>")
    print("-" * 40)
    
    while True:
        try:
            user_input = input("\nYou: ").strip()
            if user_input.lower() == 'exit':
                print("Goodbye!")
                break
            if not user_input:
                continue
            
            # Handle MongoDB commands
            if user_input.startswith('/mongo'):
                handle_mongo_command(user_input[6:].strip())
                continue
            
            print("Ollama: ", end="", flush=True)
            response = ollama_chat(user_input, model=model)
            print(response)
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


def handle_mongo_command(command: str):
    """Handle MongoDB commands"""
    if db is None:
        print("❌ MongoDB not connected")
        return
    
    parts = command.split(maxsplit=1)
    if not parts:
        print_mongo_help()
        return
    
    cmd = parts[0].lower()
    args = parts[1] if len(parts) > 1 else ""
    
    if cmd == "query":
        # Format: /mongo query collection {"field": "value"}
        query_parts = args.split(maxsplit=1)
        if len(query_parts) < 2:
            print("Usage: /mongo query <collection> <json_query>")
            return
        collection = query_parts[0]
        try:
            query = json.loads(query_parts[1])
            results = db.find_many(collection, query, limit=10)
            print(f"\n📊 Found {len(results)} document(s):")
            print(json.dumps(results, indent=2))
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif cmd == "insert":
        # Format: /mongo insert collection {"field": "value"}
        insert_parts = args.split(maxsplit=1)
        if len(insert_parts) < 2:
            print("Usage: /mongo insert <collection> <json_document>")
            return
        collection = insert_parts[0]
        try:
            doc = json.loads(insert_parts[1])
            doc_id = db.insert_one(collection, doc)
            print(f"✅ Inserted with ID: {doc_id}")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif cmd == "update":
        # Format: /mongo update collection {"_id": "..."} {"field": "new_value"}
        update_parts = args.split(maxsplit=2)
        if len(update_parts) < 3:
            print("Usage: /mongo update <collection> <json_query> <json_update>")
            return
        collection = update_parts[0]
        try:
            query = json.loads(update_parts[1])
            update = json.loads(update_parts[2])
            modified = db.update_one(collection, query, update)
            print(f"✅ Modified {modified} document(s)")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif cmd == "delete":
        # Format: /mongo delete collection {"_id": "..."}
        delete_parts = args.split(maxsplit=1)
        if len(delete_parts) < 2:
            print("Usage: /mongo delete <collection> <json_query>")
            return
        collection = delete_parts[0]
        try:
            query = json.loads(delete_parts[1])
            deleted = db.delete_one(collection, query)
            print(f"✅ Deleted {deleted} document(s)")
        except json.JSONDecodeError as e:
            print(f"❌ Invalid JSON: {e}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif cmd == "collections":
        try:
            collections = db.get_collections()
            print(f"📚 Collections in database:")
            for col in collections:
                print(f"  - {col}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    elif cmd == "help":
        print_mongo_help()
    
    else:
        print(f"Unknown command: {cmd}")
        print_mongo_help()


def print_mongo_help():
    """Print MongoDB command help"""
    print("""
📚 MongoDB Commands:
  /mongo query <collection> <json_query>
    Example: /mongo query users {"name": "John"}
  
  /mongo insert <collection> <json_document>
    Example: /mongo insert users {"name": "John", "age": 30}
  
  /mongo update <collection> <json_query> <json_update>
    Example: /mongo update users {"name": "John"} {"age": 31}
  
  /mongo delete <collection> <json_query>
    Example: /mongo delete users {"name": "John"}
  
  /mongo collections
    List all collections in the database
  
  /mongo help
    Show this help message
""")

def main():
    if len(sys.argv) > 1:
        mode = sys.argv[1].lower()
        if mode == "gemini":
            chat_with_gemini()
        elif mode == "agent":
            chat_with_gemini_agent()
        elif mode == "ollama-agent":
            model = sys.argv[2] if len(sys.argv) > 2 else "minimax-m2.5:cloud"
            chat_with_ollama_agent(model=model)
        else:
            # Assume it's an Ollama model name
            chat_with_ollama(model=mode)
    else:
        # Default to the Ollama Agent with your preferred model
        chat_with_ollama_agent(model="minimax-m2.5:cloud")

if __name__ == "__main__":
    main()
