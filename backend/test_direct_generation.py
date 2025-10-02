#!/usr/bin/env python3
"""
Test the ultra-intelligent comment generation by bypassing cooldown
"""

import mysql.connector
import sys
sys.path.append('.')
from human_like_task_monitor import HumanLikeTaskMonitor

def test_comment_generation_directly():
    print("🧠 TESTING ULTRA-INTELLIGENT COMMENT GENERATION (BYPASS COOLDOWN)")
    print("=" * 80)
    
    monitor = HumanLikeTaskMonitor()
    
    # Test with task 1867
    task_data = {
        'taskid': 1867,
        'firstname': 'Hamza',
        'lastname': 'Haseeb',
        'staffid': 188,
        'urgency_status': 'overdue',
        'days_late': 4,
        'title': 'Create APIs to Set and Get Timer from Database'
    }
    
    print(f"📋 Task: {task_data['title']}")
    print(f"👤 Staff: {task_data['firstname']} {task_data['lastname']}")
    print(f"🚨 Status: {task_data['urgency_status']} ({task_data['days_late']} days)")
    
    # Test conversation analysis
    print(f"\n🔍 CONVERSATION ANALYSIS...")
    context = monitor.analyze_full_conversation_history(task_data['taskid'])
    
    print(f"📊 Analysis Results:")
    print(f"   Current Status: {context.get('current_status', 'unknown')}")
    print(f"   Work in Progress: {context.get('work_in_progress', False)}")
    print(f"   Issues Mentioned: {len(context.get('issues_mentioned', []))}")
    print(f"   Progress Updates: {len(context.get('progress_updates', []))}")
    print(f"   Completion Mentions: {len(context.get('completion_mentions', []))}")
    
    # Generate comment directly (bypass cooldown check)
    print(f"\n💡 GENERATING ULTRA-INTELLIGENT COMMENT...")
    comment = monitor.generate_intelligent_comment(task_data['firstname'], task_data)
    
    print(f"\n🎯 GENERATED COMMENT:")
    print(f"   To: {task_data['firstname']} {task_data['lastname']}")
    print(f"   Message: {comment}")
    
    # Analyze the intelligence
    print(f"\n🧠 INTELLIGENCE ANALYSIS:")
    comment_lower = comment.lower()
    
    if 'hamza' in comment_lower:
        print(f"   ✅ USES REAL NAME: Contains 'Hamza' instead of 'User'")
    else:
        print(f"   ❌ NAME ISSUE: Doesn't use real name")
    
    if context['current_status'] == 'in_progress':
        if 'progress' in comment_lower or 'update' in comment_lower:
            print(f"   ✅ CONTEXT AWARE: References work-in-progress status")
        if 'eta' in comment_lower or 'timeline' in comment_lower or 'completion' in comment_lower:
            print(f"   ✅ TIMELINE FOCUSED: Asks for completion estimate")
    
    if any(word in comment_lower for word in ['help', 'support', 'assist']):
        print(f"   ✅ SUPPORTIVE: Offers assistance")
    
    if any(word in comment_lower for word in ['implement', 'test', 'api', 'timer']):
        print(f"   ✅ TASK SPECIFIC: References specific task elements")
    
    print(f"\n✅ Direct comment generation test complete!")
    
    # Now test with different task statuses
    print(f"\n🔄 TESTING DIFFERENT SCENARIOS...")
    
    scenarios = [
        {'current_status': 'testing', 'description': 'Task in testing phase'},
        {'current_status': 'completed', 'description': 'Task mentioned as completed'},
        {'current_status': 'blocked', 'description': 'Task has issues/problems'},
    ]
    
    for scenario in scenarios:
        print(f"\n📝 Scenario: {scenario['description']}")
        # Simulate the context
        original_method = monitor.analyze_full_conversation_history
        def mock_analysis(task_id):
            base_context = original_method(task_id)
            base_context['current_status'] = scenario['current_status']
            if scenario['current_status'] == 'testing':
                base_context['key_topics'] = ['testing']
            elif scenario['current_status'] == 'completed':
                base_context['completion_mentions'] = ['Task is completed']
            elif scenario['current_status'] == 'blocked':
                base_context['issues_mentioned'] = ['Having some issues']
            return base_context
        
        monitor.analyze_full_conversation_history = mock_analysis
        comment = monitor.generate_intelligent_comment(task_data['firstname'], task_data)
        print(f"   Comment: {comment}")
        monitor.analyze_full_conversation_history = original_method

if __name__ == "__main__":
    test_comment_generation_directly()