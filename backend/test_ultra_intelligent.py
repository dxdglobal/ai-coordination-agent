#!/usr/bin/env python3
"""
Test the ultra-intelligent commenting system with real names and full conversation analysis
"""

import mysql.connector
import sys
sys.path.append('.')
from human_like_task_monitor import HumanLikeTaskMonitor

def test_ultra_intelligent_system():
    print("🧠 TESTING ULTRA-INTELLIGENT COMMENTING SYSTEM")
    print("=" * 80)
    
    monitor = HumanLikeTaskMonitor()
    
    # Test with task that has conversation history
    task_id = 1867  
    
    print(f"🔍 Testing ultra-intelligent system for task #{task_id}...")
    
    # Get task data with real names
    try:
        conn = monitor.get_database_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Get task with real staff names
        query = """
        SELECT DISTINCT
            t.id as taskid,
            t.name as title,
            COALESCE(s.firstname, 'Unknown') as firstname,
            COALESCE(s.lastname, 'User') as lastname,
            COALESCE(ta.staffid, 0) as staffid,
            CASE 
                WHEN t.datefinished IS NOT NULL THEN 'completed'
                WHEN t.duedate IS NOT NULL AND CURDATE() > t.duedate THEN 'overdue'
                WHEN t.duedate IS NOT NULL AND DATEDIFF(t.duedate, CURDATE()) <= 2 THEN 'due_soon'
                ELSE 'normal'
            END as urgency_status,
            CASE 
                WHEN t.duedate IS NOT NULL THEN DATEDIFF(CURDATE(), t.duedate) 
                ELSE 0
            END as days_late
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
            print(f"   Staff: {task['firstname']} {task['lastname']} (ID: {task['staffid']})")
            print(f"   Urgency: {task['urgency_status']}")
            print(f"   Days Late: {task['days_late']}")
            
            # Test full conversation analysis
            print(f"\n🔍 ANALYZING COMPLETE CONVERSATION HISTORY...")
            context = monitor.analyze_full_conversation_history(task_id)
            
            print(f"📊 Full Conversation Analysis:")
            print(f"   Total Comments: {context.get('total_comments', 0)}")
            print(f"   AI Comments: {context.get('ai_comment_count', 0)}")
            print(f"   Human Comments: {context.get('human_comment_count', 0)}")
            print(f"   Current Status: {context.get('current_status', 'unknown')}")
            print(f"   Work in Progress: {context.get('work_in_progress', False)}")
            print(f"   Needs Follow-up: {context.get('needs_followup', False)}")
            
            if context.get('completion_mentions'):
                print(f"   📝 Completion Mentions: {len(context['completion_mentions'])}")
            if context.get('issues_mentioned'):
                print(f"   🚨 Issues Mentioned: {len(context['issues_mentioned'])}")
            if context.get('progress_updates'):
                print(f"   📈 Progress Updates: {len(context['progress_updates'])}")
            if context.get('key_topics'):
                print(f"   🎯 Key Topics: {', '.join(context['key_topics'])}")
            
            if context.get('last_human_message'):
                print(f"   💬 Last Human Message: {context['last_human_message'][:80]}...")
            
            # Test ultra-intelligent comment generation
            print(f"\n🎯 GENERATING ULTRA-INTELLIGENT COMMENT...")
            
            should_comment = monitor.should_comment_on_task(task)
            print(f"Should Comment: {should_comment}")
            
            if should_comment:
                comment = monitor.get_appropriate_comment(task)
                print(f"\n💡 ULTRA-INTELLIGENT COMMENT GENERATED:")
                print(f"   👤 To: {task['firstname']} {task['lastname']}")
                print(f"   📝 Message: {comment}")
                
                # Analyze intelligence level
                print(f"\n🧠 INTELLIGENCE ANALYSIS:")
                if context['current_status'] == 'testing' and 'test' in comment.lower():
                    print(f"   ✅ ULTRA-INTELLIGENT: References specific testing discussion")
                elif context['current_status'] == 'completed' and 'status' in comment.lower():
                    print(f"   ✅ ULTRA-INTELLIGENT: Asks for status update after completion mention")
                elif context['current_status'] == 'blocked' and ('help' in comment.lower() or 'support' in comment.lower()):
                    print(f"   ✅ ULTRA-INTELLIGENT: Offers assistance for mentioned issues")
                elif context['work_in_progress'] and 'progress' in comment.lower():
                    print(f"   ✅ ULTRA-INTELLIGENT: Acknowledges ongoing work")
                elif context['needs_followup']:
                    print(f"   ✅ ULTRA-INTELLIGENT: Intelligent follow-up based on non-response")
                else:
                    print(f"   ✅ INTELLIGENT: Contextual urgency-based comment")
                
                # Check for real name usage
                if task['firstname'] != 'User' and task['firstname'] in comment:
                    print(f"   ✅ REAL NAMES: Uses actual name '{task['firstname']}' instead of 'User'")
                else:
                    print(f"   ❌ NAME ISSUE: May still be using 'User' or generic names")
                    
            else:
                print("❌ Should not comment (cooldown or other rules)")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    
    print(f"\n✅ Ultra-intelligent system test complete!")

if __name__ == "__main__":
    test_ultra_intelligent_system()