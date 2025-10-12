#!/usr/bin/env python3
"""
Test script to verify our Turkish character and overdue task fixes
"""

from task_management import process_task_query

def test_queries():
    """Test all the fixed queries"""
    
    test_cases = [
        {
            'name': 'Turkish Character Test - İlahe',
            'query': 'please show İlahe tasks list',
            'expected_employee': 'İlahe  Avcı'
        },
        {
            'name': 'Overdue Tasks Test - Hamza',
            'query': 'show hamza overdue tasks',
            'check_overdue': True
        },
        {
            'name': 'Completed Tasks Test - Hamza', 
            'query': 'show hamza completed tasks',
            'check_completed': True
        },
        {
            'name': 'Laiba Tasks Test',
            'query': 'please give me laiba tasks list',
            'expected_employee': 'Laiba Batool'
        }
    ]
    
    for test in test_cases:
        print(f"\n🧪 {test['name']}")
        print(f"Query: {test['query']}")
        print("-" * 50)
        
        try:
            result = process_task_query(test['query'])
            
            if result.get('success'):
                ai_resp = result.get('ai_response', {})
                employee = ai_resp.get('employee')
                total_tasks = ai_resp.get('total_count', 0)
                
                print(f"✅ SUCCESS")
                print(f"Employee: {employee}")
                print(f"Total tasks: {total_tasks}")
                
                # Check expected employee
                if test.get('expected_employee'):
                    if employee == test['expected_employee']:
                        print(f"✅ Employee match correct!")
                    else:
                        print(f"❌ Expected: {test['expected_employee']}, Got: {employee}")
                
                # Check task details if available
                tasks = ai_resp.get('tasks', [])
                if tasks:
                    print(f"Sample tasks:")
                    for i, task in enumerate(tasks[:3]):
                        status = task.get('status', 'Unknown')
                        is_overdue = task.get('is_overdue', False)
                        print(f"  {i+1}. {task.get('name', 'No name')[:50]}...")
                        print(f"     Status: {status}, Overdue: {is_overdue}")
                        
                # Check specific filters
                if test.get('check_overdue'):
                    overdue_count = sum(1 for task in tasks if task.get('is_overdue'))
                    print(f"🕒 Overdue tasks found: {overdue_count}")
                    
                if test.get('check_completed'):
                    completed_count = sum(1 for task in tasks if task.get('status') == 'Completed')
                    print(f"✅ Completed tasks found: {completed_count}")
                    
            else:
                print(f"❌ FAILED")
                print(f"Error: {result.get('error')}")
                
        except Exception as e:
            print(f"💥 EXCEPTION: {str(e)}")

if __name__ == "__main__":
    print("🚀 Testing RAG System Fixes")
    print("=" * 60)
    test_queries()
    print("\n" + "=" * 60)
    print("🏁 Test completed!")