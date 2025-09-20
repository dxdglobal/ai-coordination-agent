"""
Test script for user-specific queries
"""
import requests
import json

def test_user_queries():
    backend_url = "http://localhost:5001"
    
    # Test queries
    test_queries = [
        "tell me about Haseeb",
        "show me Hamza Haseeb's tasks",
        "what is the total value of invoices this month?",
        "who is Haseeb's manager?",
        "list all employees in the Engineering department"
    ]
    
    print("Testing user-specific queries...")
    print("=" * 50)
    
    for i, query in enumerate(test_queries, 1):
        print(f"\n{i}. Query: '{query}'")
        print("-" * 40)
        
        try:
            response = requests.post(
                f"{backend_url}/api/chat",
                json={"message": query},
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Response: {result.get('response', 'No response')}")
                print(f"📊 Strategy: {result.get('strategy_used', 'Unknown')}")
                if result.get('data_sources'):
                    print(f"📋 Data sources: {', '.join(result['data_sources'])}")
            else:
                print(f"❌ Error {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Request failed: {e}")
        
        print()

if __name__ == '__main__':
    test_user_queries()