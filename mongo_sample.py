#!/usr/bin/env python3
"""
Sample script to demonstrate MongoDB queries
"""

from mongodb_handler import MongoDBHandler
import json

def main():
    # Connect to MongoDB
    db = MongoDBHandler()
    
    if db.db is None:
        print("Failed to connect to MongoDB. Make sure it's running!")
        return
    
    # Sample 1: Insert a single document
    print("\n📝 Inserting a user document...")
    user_doc = {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30,
        "city": "New York"
    }
    user_id = db.insert_one("users", user_doc)
    print(f"✅ Inserted user with ID: {user_id}")
    
    # Sample 2: Insert multiple documents
    print("\n📝 Inserting multiple users...")
    users = [
        {"name": "Jane Smith", "email": "jane@example.com", "age": 28, "city": "Los Angeles"},
        {"name": "Bob Johnson", "email": "bob@example.com", "age": 35, "city": "Chicago"},
        {"name": "Alice Brown", "email": "alice@example.com", "age": 32, "city": "Houston"},
    ]
    count = db.insert_many("users", users)
    print(f"✅ Inserted {count} users")
    
    # Sample 3: Find one document
    print("\n🔍 Finding one user by name...")
    user = db.find_one("users", {"name": "John Doe"})
    print(f"Found: {json.dumps(user, indent=2)}")
    
    # Sample 4: Find multiple documents
    print("\n🔍 Finding all users in New York...")
    ny_users = db.find_many("users", {"city": "New York"}, limit=5)
    print(f"Found {len(ny_users)} users:")
    for user in ny_users:
        print(f"  - {user['name']} ({user['email']})")
    
    # Sample 5: Update a document
    print("\n✏️ Updating user age...")
    modified = db.update_one("users", {"name": "John Doe"}, {"age": 31})
    print(f"✅ Modified {modified} document(s)")
    
    # Sample 6: Find updated document
    print("\n🔍 Verifying update...")
    updated_user = db.find_one("users", {"name": "John Doe"})
    print(f"Updated user: {updated_user['name']} is now {updated_user['age']} years old")
    
    # Sample 7: Get all collections
    print("\n📚 All collections in database:")
    collections = db.get_collections()
    for col in collections:
        print(f"  - {col}")
    
    # Sample 8: Interactive query
    print("\n" + "="*50)
    print("Interactive MongoDB Query")
    print("="*50)
    
    while True:
        collection = input("\nEnter collection name (or 'exit' to quit): ").strip()
        if collection.lower() == 'exit':
            break
        
        query_str = input("Enter query as JSON (e.g., {\"name\": \"John Doe\"}): ").strip()
        try:
            query = json.loads(query_str)
            results = db.find_many(collection, query, limit=5)
            print(f"\nFound {len(results)} document(s):")
            print(json.dumps(results, indent=2))
        except json.JSONDecodeError:
            print("❌ Invalid JSON format")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    # Close connection
    db.close()

if __name__ == "__main__":
    main()
