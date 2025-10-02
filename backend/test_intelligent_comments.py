#!/usr/bin/env python3
"""
Test the enhanced intelligent commenting system with real names and conversation context
"""

import mysql.connector
import sys
sys.path.append('.')
from human_like_task_monitor import HumanLikeTaskMonitor

def test_intelligent_comments():
    print("🧠 TESTING ENHANCED INTELLIGENT COMMENTING SYSTEM")
    print("=" * 70)
    
    monitor = HumanLikeTaskMonitor()
    
    # Test with real task that has conversation history
    task_id = 1867  # Task from the images
    
    print(f"🔍 Testing intelligent comments for task #{task_id}...")
    
    # Get actual task data with real names
    try:
        conn = monitor.get_database_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Use the new query with real names
        query = """
        SELECT DISTINCT
            t.id as taskid,
            t.name as title,
            t.duedate,
            t.datefinished as completiondate,
            COALESCE(ta.staffid, 0) as staffid,
            COALESCE(s.firstname, 'User') as firstname,
            COALESCE(s.lastname, 'Staff') as lastname,
            CASE 
                WHEN t.datefinished IS NOT NULL AND t.duedate IS NOT NULL THEN DATEDIFF(CURDATE(), t.duedate)
                WHEN t.duedate IS NOT NULL THEN DATEDIFF(CURDATE(), t.duedate) 
                ELSE 0
            END as days_late,
            CASE 
                WHEN t.datefinished IS NOT NULL THEN 'completed'
                WHEN t.duedate IS NOT NULL AND CURDATE() > t.duedate THEN 'overdue'
                WHEN t.duedate IS NOT NULL AND DATEDIFF(t.duedate, CURDATE()) <= 2 THEN 'due_soon'
                ELSE 'normal'
            END as urgency_status
        FROM tbltasks t
        LEFT JOIN tbltask_assigned ta ON t.id = ta.taskid
        LEFT JOIN tblstaff s ON ta.staffid = s.staffid
        WHERE t.id = %s
        LIMIT 1
        """
        
        cursor.execute(query, (task_id,))
        task = cursor.fetchone()
        
        if task:
            print(f"✅ Task found:")
            print(f"   ID: {task['taskid']}")
            print(f"   Title: {task['title']}")
            print(f"   Assigned to: {task['firstname']} {task['lastname']} (Staff ID: {task['staffid']})")
            print(f"   Urgency: {task['urgency_status']}")
            print(f"   Days Late: {task['days_late']}")
            
            # Test conversation context analysis
            print(f"\n🔍 ANALYZING CONVERSATION CONTEXT...")
            context = monitor.analyze_conversation_context(task_id)
            
            print(f"📊 Context Analysis:")
            print(f"   Mentions Issues: {context.get('mentions_issues', False)}")
            print(f"   Mentions Progress: {context.get('mentions_progress', False)}")
            print(f"   Mentions Completion: {context.get('mentions_completion', False)}")
            print(f"   Mentions Testing: {context.get('mentions_testing', False)}")
            print(f"   Has Updates: {context.get('has_updates', False)}")
            print(f"   Working On It: {context.get('working_on_it', False)}")
            
            if context.get('last_human_content'):
                print(f"   Last Human Comment: {context['last_human_content'][:80]}...")
            
            # Test intelligent comment generation
            print(f"\n💬 GENERATING INTELLIGENT COMMENT...")
            
            should_comment = monitor.should_comment_on_task(task)
            print(f"Should Comment: {should_comment}")
            
            if should_comment:
                comment = monitor.get_appropriate_comment(task)
                print(f"\n🎯 GENERATED COMMENT:")
                print(f"   To: {task['firstname']} {task['lastname']}")
                print(f"   Message: {comment}")
                
                # Analyze comment intelligence
                if context.get('mentions_completion') and "completed" in comment.lower():
                    print(f"   🧠 INTELLIGENCE: Contextual - references completion mentioned in conversation")
                elif context.get('mentions_testing') and "test" in comment.lower():
                    print(f"   🧠 INTELLIGENCE: Contextual - references testing mentioned in conversation")
                elif context.get('mentions_issues') and ("help" in comment.lower() or "support" in comment.lower()):
                    print(f"   🧠 INTELLIGENCE: Contextual - offers help for issues mentioned")
                elif context.get('working_on_it'):
                    print(f"   🧠 INTELLIGENCE: Contextual - acknowledges work in progress")
                else:
                    print(f"   🧠 INTELLIGENCE: Standard urgency-based comment")
            else:
                print("❌ Should not comment (likely due to cooldown or other rules)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
    
    print(f"\n✅ Intelligent commenting system test complete!")

if __name__ == "__main__":
    test_intelligent_comments()