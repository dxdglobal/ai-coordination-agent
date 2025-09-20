import requests
import json

def test_smart_chat():
    """Test the smart chat API endpoint"""
    url = "http://localhost:5000/ai/smart_chat"
    
    # Test cases
    test_queries = [
        "how many tables in the database",
        "is Haseeb there?",
        "show me overdue tasks",
        "what's the total revenue?",
        "test message"
    ]
    
    for query in test_queries:
        print(f"\n🧪 Testing query: '{query}'")
        print("-" * 50)
        
        data = {"message": query}
        
        try:
            response = requests.post(url, json=data, timeout=10)
            response.raise_for_status()
            
            result = response.json()
            
            print(f"✅ Status: Success")
            print(f"📝 Response: {result.get('response', 'No response')[:200]}...")
            print(f"🔗 Session ID: {result.get('session_id', 'None')}")
            print(f"⚡ Response Time: {result.get('response_time_ms', 0)}ms")
            print(f"🎯 Intent: {result.get('intent_analysis', {}).get('category', 'Unknown')}")
            print(f"💾 Cached: {result.get('cached', False)}")
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Request Error: {e}")
        except json.JSONDecodeError as e:
            print(f"❌ JSON Error: {e}")
        except Exception as e:
            print(f"❌ Unexpected Error: {e}")

if __name__ == "__main__":
    print("🚀 Testing AI Coordination Agent Smart Chat API")
    print("=" * 60)
    test_smart_chat()