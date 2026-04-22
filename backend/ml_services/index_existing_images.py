#!/usr/bin/env python3
"""
Script to index existing images for chatbot functionality
"""
import requests
import json
import sys

BASE_URL = "http://localhost:5000"

def index_user_images(username):
    """Index all existing images for a user"""
    try:
        data = {"username": username}
        response = requests.post(
            f"{BASE_URL}/index-existing-images",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully indexed {result['indexed_count']} images for user '{username}'")
            print(f"📊 Total images found: {result['total_images']}")
            
            if result.get('errors'):
                print("\n⚠️  Some errors occurred:")
                for error in result['errors']:
                    print(f"   - {error}")
        else:
            print(f"❌ Error: {response.json()}")
            
    except Exception as e:
        print(f"❌ Error indexing images: {e}")

def main():
    if len(sys.argv) != 2:
        print("Usage: python index_existing_images.py <username>")
        print("Example: python index_existing_images.py loga")
        sys.exit(1)
    
    username = sys.argv[1]
    print(f"🔄 Indexing existing images for user: {username}")
    print("=" * 50)
    
    index_user_images(username)

if __name__ == "__main__":
    main()
