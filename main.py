"""
MCP Server for Gemini, Ollama, and MongoDB
"""

import os
import json
from typing import Optional, Any, List, Dict
import requests
from mcp.server.fastmcp import FastMCP
from mongodb_handler import MongoDBHandler

# Create an MCP server
mcp = FastMCP("LocalAI")

# Initialize MongoDB handler with error handling
try:
    db_handler = MongoDBHandler()
except Exception as e:
    print(f"Warning: MongoDB connection failed: {e}")
    db_handler = None

# --- Gemini Chat integration -------------------------------------------------

def call_gemini_chat(prompt: str, model: Optional[str] = None, timeout: int = 30) -> str:
    """Call Gemini/Generative Language API using an API key via REST."""
    api_key = os.getenv("GOOGLE_API_KEY")
    model = model or os.getenv("GEMINI_MODEL", "gemini-1.5-flash")

    if not api_key:
        raise RuntimeError(
            "No GOOGLE_API_KEY found in environment. Export GOOGLE_API_KEY to call Gemini."
        )

    # NOTE: endpoint and payload structure may change across API versions.
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    payload = {
        "contents": [{"parts": [{"text": prompt}]}]
    }

    resp = requests.post(url, json=payload, timeout=timeout)
    resp.raise_for_status()
    j = resp.json()

    try:
        return j["candidates"][0]["content"]["parts"][0]["text"]
    except Exception:
        return json.dumps(j, indent=2, ensure_ascii=False)


@mcp.tool()
def gemini_chat(prompt: str) -> str:
    """MCP tool that forwards a prompt to Gemini and returns the reply.
    
    It uses GOOGLE_API_KEY + GEMINI_MODEL environment variables.
    """
    try:
        return call_gemini_chat(prompt)
    except Exception as e:
        return f"[gemini error] {e}"


@mcp.tool()
def ollama_chat(prompt: str, model: str = "qwen3.5:4b") -> str:
    """MCP tool that forwards a prompt to a local Ollama instance and returns the reply.
    
    Ensure Ollama is running locally (http://localhost:11434).
    """
    url = "http://localhost:11434/api/generate"
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }

    try:
        resp = requests.post(url, json=payload, timeout=120)
        resp.raise_for_status()
        return resp.json().get("response", "No response from Ollama")
    except Exception as e:
        return f"[ollama error] {e}"


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


# Add a prompt
@mcp.prompt()
def greet_user(name: str, style: str = "friendly") -> str:
    """Generate a greeting prompt"""
    styles = {
        "friendly": "Please write a warm, friendly greeting",
        "formal": "Please write a formal, professional greeting",
        "casual": "Please write a casual, relaxed greeting",
    }

    return f"{styles.get(style, styles['friendly'])} for someone named {name}."


# --- MongoDB tools -----------------------------------------------------------

@mcp.tool()
def mongo_query(collection: str, query: str) -> str:
    """Query MongoDB collection.
    
    Args:
        collection: Collection name (e.g., 'users')
        query: JSON query string (e.g., '{"name": "John"}')
    """
    if db_handler is None:
        return "[mongo error] MongoDB not connected"
    try:
        query_dict = json.loads(query)
        results = db_handler.find_many(collection, query_dict, limit=10)
        return json.dumps(results, indent=2)
    except json.JSONDecodeError as e:
        return f"[mongo error] Invalid JSON query: {e}"
    except Exception as e:
        return f"[mongo error] {e}"


@mcp.tool()
def mongo_insert(collection: str, document: str) -> str:
    """Insert a document into MongoDB collection.
    
    Args:
        collection: Collection name
        document: JSON document string
    """
    if db_handler is None:
        return "[mongo error] MongoDB not connected"
    try:
        doc_dict = json.loads(document)
        doc_id = db_handler.insert_one(collection, doc_dict)
        return f"Inserted document with ID: {doc_id}"
    except json.JSONDecodeError as e:
        return f"[mongo error] Invalid JSON document: {e}"
    except Exception as e:
        return f"[mongo error] {e}"


@mcp.tool()
def mongo_update(collection: str, query: str, update: str) -> str:
    """Update a document in MongoDB collection.
    
    Args:
        collection: Collection name
        query: JSON query string to find document
        update: JSON update data
    """
    if db_handler is None:
        return "[mongo error] MongoDB not connected"
    try:
        query_dict = json.loads(query)
        update_dict = json.loads(update)
        modified = db_handler.update_one(collection, query_dict, update_dict)
        return f"Modified {modified} document(s)"
    except json.JSONDecodeError as e:
        return f"[mongo error] Invalid JSON: {e}"
    except Exception as e:
        return f"[mongo error] {e}"


@mcp.tool()
def mongo_delete(collection: str, query: str) -> str:
    """Delete a document from MongoDB collection.
    
    Args:
        collection: Collection name
        query: JSON query string to find document
    """
    if db_handler is None:
        return "[mongo error] MongoDB not connected"
    try:
        query_dict = json.loads(query)
        deleted = db_handler.delete_one(collection, query_dict)
        return f"Deleted {deleted} document(s)"
    except json.JSONDecodeError as e:
        return f"[mongo error] Invalid JSON query: {e}"
    except Exception as e:
        return f"[mongo error] {e}"


@mcp.tool()
def mongo_collections() -> str:
    """Get all collections in the MongoDB database."""
    if db_handler is None:
        return "[mongo error] MongoDB not connected"
    try:
        collections = db_handler.get_collections()
        return json.dumps({"collections": collections})
    except Exception as e:
        return f"[mongo error] {e}"



if __name__ == "__main__":
    # When running directly, start the MCP server
    mcp.run()
