"""
MongoDB connection and utilities
"""

import os
from pymongo import MongoClient
from pymongo.errors import ServerSelectionTimeoutError
from typing import List, Dict, Any, Optional

class MongoDBHandler:
    """Handler for MongoDB operations"""
    
    def __init__(self, uri: Optional[str] = None, db_name: str = "hris"):
        """
        Initialize MongoDB connection
        
        Args:
            uri: MongoDB connection string (defaults to MONGODB_URI env var)
            db_name: Database name (defaults to hris)
        """
        self.uri = uri or os.getenv("MONGODB_URI", "mongodb+srv://joeysabusido:genesis11@cluster0.r76lv.mongodb.net/hris?retryWrites=true&w=majority")
        self.db_name = db_name
        self.client = None
        self.db = None
        self.connect()
    
    def connect(self) -> bool:
        """Connect to MongoDB"""
        try:
            self.client = MongoClient(self.uri, serverSelectionTimeoutMS=5000)
            # Verify connection
            self.client.admin.command('ping')
            self.db = self.client[self.db_name]
            print(f"✅ Connected to MongoDB: {self.db_name}")
            return True
        except ServerSelectionTimeoutError as e:
            print(f"❌ MongoDB connection failed: {e}")
            print(f"Make sure MongoDB is running at {self.uri}")
            return False
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def insert_one(self, collection: str, document: Dict[str, Any]) -> Optional[str]:
        """Insert a single document"""
        try:
            result = self.db[collection].insert_one(document)
            return str(result.inserted_id)
        except Exception as e:
            return f"Error inserting document: {e}"
    
    def insert_many(self, collection: str, documents: List[Dict[str, Any]]) -> int:
        """Insert multiple documents"""
        try:
            result = self.db[collection].insert_many(documents)
            return len(result.inserted_ids)
        except Exception as e:
            return f"Error inserting documents: {e}"
    
    def find_one(self, collection: str, query: Dict[str, Any]) -> Optional[Dict]:
        """Find a single document"""
        try:
            result = self.db[collection].find_one(query)
            if result:
                result['_id'] = str(result['_id'])  # Convert ObjectId to string
            return result
        except Exception as e:
            return {"error": str(e)}
    
    def find_many(self, collection: str, query: Dict[str, Any], limit: int = 10) -> List[Dict]:
        """Find multiple documents"""
        try:
            results = list(self.db[collection].find(query).limit(limit))
            for doc in results:
                doc['_id'] = str(doc['_id'])  # Convert ObjectId to string
            return results
        except Exception as e:
            return [{"error": str(e)}]
    
    def update_one(self, collection: str, query: Dict[str, Any], update: Dict[str, Any]) -> int:
        """Update a single document"""
        try:
            result = self.db[collection].update_one(query, {"$set": update})
            return result.modified_count
        except Exception as e:
            return f"Error updating document: {e}"
    
    def delete_one(self, collection: str, query: Dict[str, Any]) -> int:
        """Delete a single document"""
        try:
            result = self.db[collection].delete_one(query)
            return result.deleted_count
        except Exception as e:
            return f"Error deleting document: {e}"
    
    def get_collections(self) -> List[str]:
        """Get all collections in the database"""
        try:
            return self.db.list_collection_names()
        except Exception as e:
            return [f"Error: {e}"]
    
    def search(self, collection: str, query_text: str, limit: int = 10) -> List[Dict]:
        """Search for documents where name or email matches query_text (case-insensitive)"""
        try:
            # Simple regex search for name or email
            search_query = {
                "$or": [
                    {"name": {"$regex": query_text, "$options": "i"}},
                    {"email": {"$regex": query_text, "$options": "i"}},
                    {"first_name": {"$regex": query_text, "$options": "i"}},
                    {"last_name": {"$regex": query_text, "$options": "i"}}
                ]
            }
            results = list(self.db[collection].find(search_query).limit(limit))
            for doc in results:
                doc['_id'] = str(doc['_id'])
            return results
        except Exception as e:
            return [{"error": str(e)}]

    def search_users(self, query_text: str, limit: int = 10) -> List[Dict]:
        """Specific helper to search the users collection"""
        return self.search("users", query_text, limit)

    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            print("MongoDB connection closed")
