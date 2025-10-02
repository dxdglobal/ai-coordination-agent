#!/usr/bin/env python3
"""
Test the enhanced conversation analysis system
"""

import mysql.connector
from datetime import datetime, timedelta
import sys
sys.path.append('.')
from human_like_task_monitor import HumanLikeTaskMonitor

def test_conversation_analysis():
    print("🧠 TESTING ENHANCED CONVERSATION ANALYSIS")
    print("=" * 60)
    
    monitor = HumanLikeTaskMonitor()
    
    # Test with task #1867
    task_id = 1867
    print(f"🔍 Analyzing conversation history for task #{task_id}...")
    
    conversation = monitor.analyze_conversation_history(task_id)
    
    print(f"\n📊 CONVERSATION ANALYSIS RESULTS:")
    print(f"   Total Comments: {conversation['total_comments']}")
    print(f"   AI Comments: {conversation['ai_comment_count']}")
    print(f"   Human Comments: {conversation['human_comment_count']}")
    print(f"   Needs Follow-up: {conversation['needs_followup']}")
    print(f"   Conversation Pattern: {conversation['conversation_pattern']}")
    
    if conversation['last_ai_comment']:
        print(f"\n🤖 Last AI Comment:")
        print(f"   Date: {conversation['last_ai_comment']['dateadded']}")
        print(f"   Content: {conversation['last_ai_comment']['content'][:80]}...")
    
    if conversation['last_human_comment']:
        print(f"\n👤 Last Human Comment:")
        print(f"   Date: {conversation['last_human_comment']['dateadded']}")
        print(f"   Author: {conversation['last_human_comment']['firstname']} {conversation['last_human_comment']['lastname']}")
        print(f"   Content: {conversation['last_human_comment']['content'][:80]}...")
    
    # Test comment generation
    print(f"\n💬 TESTING SMART COMMENT GENERATION...")
    
    # Simulate task data
    task_data = {
        'taskid': task_id,
        'firstname': 'Hamza',
        'lastname': 'Haseeb',
        'staffid': 188,  # Added missing staffid
        'urgency_status': 'overdue',
        'days_late': 4
    }
    
    # Test if should comment
    should_comment = monitor.should_comment_on_task(task_data)
    print(f"Should Comment: {should_comment}")
    
    if should_comment:
        comment = monitor.get_appropriate_comment(task_data)
        print(f"Generated Comment: {comment}")
        
        if conversation['needs_followup']:
            print("📞 This is a FOLLOW-UP comment because user hasn't responded!")
        else:
            print("📝 This is a regular comment based on task urgency")
    
    print(f"\n✅ Enhanced conversation analysis test complete!")

if __name__ == "__main__":
    test_conversation_analysis()