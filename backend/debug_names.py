#!/usr/bin/env python3
"""Debug employee names in database"""

import sys
sys.path.append('/Users/dds/Desktop/Git-Projects/ai-coordination-agent/backend')

from task_management.crm_connector import get_crm_connector
from task_management.nlp_utils import NLPProcessor

def debug_employee_names():
    """Debug employee names"""
    print("🔍 Debugging Employee Names")
    print("=" * 50)
    
    crm = get_crm_connector()
    nlp = NLPProcessor()
    
    # Get all employees
    employees = crm.get_all_employees()
    
    # Look for Hamza and İlahe
    hamza_employees = [emp for emp in employees if 'hamza' in emp['firstname'].lower()]
    ilahe_employees = [emp for emp in employees if 'ilahe' in emp['firstname'].lower() or 'İlahe' in emp['firstname']]
    
    print(f"🔍 Found {len(hamza_employees)} employees with 'Hamza' in firstname:")
    for emp in hamza_employees:
        print(f"  - {emp['firstname']} {emp['lastname']} (ID: {emp['id']})")
        
    print(f"\n🔍 Found {len(ilahe_employees)} employees with 'İlahe' in firstname:")
    for emp in ilahe_employees:
        print(f"  - {emp['firstname']} {emp['lastname']} (ID: {emp['id']})")
    
    # Test Turkish normalization
    print(f"\n🔍 Testing Turkish normalization:")
    test_query = "Show completed tasks for Hamza"
    normalized = nlp._normalize_turkish_text(test_query.lower())
    print(f"  Query: '{test_query}' -> '{normalized}'")
    
    for emp in hamza_employees:
        firstname_norm = nlp._normalize_turkish_text(emp['firstname'].strip().lower())
        print(f"  Employee firstname: '{emp['firstname']}' -> '{firstname_norm}' (stripped)")
        print(f"  Match test: '{firstname_norm}' in '{normalized}' = {firstname_norm in normalized}")

if __name__ == "__main__":
    debug_employee_names()