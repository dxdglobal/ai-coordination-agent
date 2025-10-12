#!/usr/bin/env python3
"""Test script for enhanced 11-status task system"""

import requests
import json
import time

BASE_URL = "http://127.0.0.1:5001"

def test_query(query, expected_employee=None):
    """Test a query against the AI system"""
    print(f"\n🔍 Testing: '{query}'")
    
    try:
        response = requests.post(f"{BASE_URL}/ai/query", 
                               json={"query": query},
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Response: {data.get('response', 'No response')[:200]}...")
            
            if expected_employee:
                if expected_employee.lower() in data.get('response', '').lower():
                    print(f"✅ Employee '{expected_employee}' found in response")
                else:
                    print(f"❌ Employee '{expected_employee}' NOT found in response")
                    
            return True
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

def main():
    """Test all enhanced features"""
    
    print("🚀 Testing Enhanced 11-Status Task System")
    print("=" * 50)
    
    # Test Turkish names
    print("\n📋 Testing Turkish Character Support:")
    test_query("Show İlahe tasks", "İlahe")
    test_query("List Çağla tasks", "Çağla")
    test_query("Show Şahar active tasks", "Şahar")
    
    # Test specific employees
    print("\n👥 Testing Specific Employees:")
    test_query("Show Laiba Batool tasks", "Laiba")
    test_query("List Hamza Haseeb tasks", "Hamza")
    test_query("Show Nawaz tasks", "Nawaz")
    
    # Test status filtering
    print("\n📊 Testing Status Filtering:")
    test_query("Show completed tasks for Hamza")
    test_query("List overdue tasks for Nawaz")
    test_query("Show active tasks for İlahe")
    test_query("List on hold tasks")
    test_query("Show cancelled tasks")
    test_query("List archived tasks")
    
    # Test specific status keywords
    print("\n🏷️ Testing Status Keywords:")
    test_query("Show approved tasks")
    test_query("List rejected tasks")
    test_query("Show pending review tasks")
    test_query("List finished tasks")
    test_query("Show paused tasks")
    
    # Test performance reports
    print("\n📈 Testing Performance Reports:")
    test_query("Generate performance report for Laiba Batool")
    test_query("Show task summary for İlahe")
    test_query("Analyze Hamza performance")
    
    print("\n✅ All tests completed!")

if __name__ == "__main__":
    main()