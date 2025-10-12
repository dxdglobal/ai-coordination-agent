#!/usr/bin/env python3
"""Simple test for enhanced employee name detection"""

import sys
import os

# Add the current directory to Python path
sys.path.append('/Users/dds/Desktop/Git-Projects/ai-coordination-agent/backend')

from task_management.nlp_utils import NLPProcessor
from task_management.crm_connector import get_crm_connector

def test_name_extraction():
    """Test enhanced name extraction"""
    print("🧪 Testing Enhanced Employee Name Detection")
    print("=" * 50)
    
    # Initialize components
    nlp = NLPProcessor()
    crm = get_crm_connector()
    
    # Test queries
    test_queries = [
        "Show completed tasks for Hamza",
        "List active tasks for İlahe", 
        "Show overdue tasks for Nawaz",
        "Get tasks for Laiba",
        "Show Çağla tasks",
        "Performance report for Şahar"
    ]
    
    for query in test_queries:
        print(f"\n🔍 Query: '{query}'")
        try:
            result = nlp.process_query(query)
            print(f"✅ Employee: {result.get('employee', 'None')}")
            print(f"✅ Confidence: {result.get('confidence', 0.0):.2f}")
            print(f"✅ Employee ID: {result.get('employee_id', 'None')}")
            print(f"✅ Intent: {result.get('intent', 'None')}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print(f"\n✅ Test completed!")

if __name__ == "__main__":
    test_name_extraction()