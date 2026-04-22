#!/usr/bin/env python3
"""
Test script for chatbot functionality
"""
import requests
import json

BASE_URL = "http://localhost:5000"

def test_chatbot_status():
    """Test chatbot status endpoint"""
    try:
        response = requests.get(f"{BASE_URL}/chatbot/status")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing status: {e}")
        return False

def test_chatbot_query():
    """Test chatbot query endpoint"""
    try:
        data = {
            "user_id": "test_user",
            "query": "formal wear"
        }
        response = requests.post(
            f"{BASE_URL}/chatbot/query",
            json=data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Query Status Code: {response.status_code}")
        print(f"Query Response: {response.json()}")
        return response.status_code == 200
    except Exception as e:
        print(f"Error testing query: {e}")
        return False

if __name__ == "__main__":
    print("Testing Chatbot Integration...")
    print("=" * 40)
    
    print("\n1. Testing chatbot status...")
    status_ok = test_chatbot_status()
    
    print("\n2. Testing chatbot query...")
    query_ok = test_chatbot_query()
    
    print("\n" + "=" * 40)
    if status_ok and query_ok:
        print("✅ All tests passed! Chatbot integration is working.")
    else:
        print("❌ Some tests failed. Check the backend logs.")
