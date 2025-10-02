#!/usr/bin/env python3
"""
Manual scan and update with the ultra-intelligent system
"""

import sys
sys.path.append('.')
from human_like_task_monitor import HumanLikeTaskMonitor

def manual_intelligent_scan():
    print("🚀 STARTING ULTRA-INTELLIGENT TASK SCAN & COMMENT UPDATE")
    print("=" * 80)
    
    monitor = HumanLikeTaskMonitor()
    
    print("🔍 Fetching all tasks from CRM database...")
    tasks = monitor.get_tasks_needing_attention()
    
    print(f"✅ Found {len(tasks)} tasks to analyze with ultra-intelligence!")
    
    # Categorize tasks
    completed_tasks = [t for t in tasks if t.get('urgency_status') == 'completed']
    overdue_tasks = [t for t in tasks if t.get('urgency_status') == 'overdue'] 
    due_soon_tasks = [t for t in tasks if t.get('urgency_status') == 'due_soon']
    normal_tasks = [t for t in tasks if t.get('urgency_status') == 'normal']
    
    print(f"📋 Task Categories:")
    print(f"   🚨 Overdue: {len(overdue_tasks)} tasks")
    print(f"   ⏰ Due Soon: {len(due_soon_tasks)} tasks") 
    print(f"   ✅ Completed: {len(completed_tasks)} tasks")
    print(f"   📝 Normal: {len(normal_tasks)} tasks")
    
    print(f"\n🧠 ULTRA-INTELLIGENT ANALYSIS & COMMENTING...")
    print("=" * 80)
    
    comments_added = 0
    tasks_analyzed = 0
    
    # Process tasks with ultra-intelligence (more than the usual 50 limit)
    for i, task in enumerate(tasks[:100], 1):  # Analyze 100 tasks for demo
        tasks_analyzed += 1
        
        # Show progress for first 20, then every 10th
        if i <= 20 or i % 10 == 0:
            print(f"   🔍 Analyzing task {i}/{min(len(tasks), 100)}: {task.get('title', 'Untitled')[:40]}...")
        
        # Check if we should comment with ultra-intelligence
        if monitor.should_comment_on_task(task):
            # Generate ultra-intelligent comment
            comment = monitor.get_appropriate_comment(task)
            
            # Get conversation context for display
            context = monitor.analyze_full_conversation_history(task['taskid'])
            current_status = context.get('current_status', 'unknown')
            
            # Add comment to database
            if monitor.add_comment_to_task(task['taskid'], comment):
                comments_added += 1
                
                # Determine comment intelligence type
                if context['needs_followup']:
                    comment_type = "🔄 INTELLIGENT FOLLOW-UP"
                elif current_status == 'testing':
                    comment_type = "🧪 TESTING INTELLIGENCE"
                elif current_status == 'completed':
                    comment_type = "🎯 STATUS INTELLIGENCE"
                elif current_status == 'blocked':
                    comment_type = "🆘 SUPPORT INTELLIGENCE"
                elif current_status == 'in_progress':
                    comment_type = "📈 PROGRESS INTELLIGENCE"
                else:
                    comment_type = "🧠 SMART URGENCY"
                
                # Display intelligent comment details
                urgency_emoji = {
                    'completed': '✅',
                    'overdue': '🚨',
                    'due_soon': '⏰',
                    'normal': '💬'
                }
                
                staff_name = task['firstname'] if task['firstname'] != 'User' else task.get('lastname', 'Unknown')
                task_title = task.get('title', 'Unknown Task')[:35]
                
                print(f"   {urgency_emoji.get(task['urgency_status'], '📝')} {comment_type}")
                print(f"      📋 Task {task['taskid']}: {task_title}")
                print(f"      👤 To: {staff_name}")
                print(f"      💭 Comment: {comment[:65]}...")
                
                if current_status != 'unknown':
                    print(f"      🧠 Context: Detected '{current_status}' from conversation analysis")
                
                print()  # Add spacing
        
        # Small delay to show progress
        if i <= 10:
            import time
            time.sleep(0.5)
    
    print(f"✨ ===== ULTRA-INTELLIGENT SCAN COMPLETE =====")
    print(f"🧠 Tasks Analyzed: {tasks_analyzed}")
    print(f"💬 Intelligent Comments Added: {comments_added}")
    print(f"📊 Total Tasks Available: {len(tasks)}")
    print(f"🎯 Intelligence Features Used:")
    print(f"   ✅ Real staff names (no more 'User')")
    print(f"   ✅ Complete conversation history analysis")
    print(f"   ✅ Context-aware intelligent responses")
    print(f"   ✅ Scenario-based comment generation")
    print("=" * 50)
    
    if comments_added > 0:
        print(f"🎉 SUCCESS! Added {comments_added} ultra-intelligent comments!")
    else:
        print(f"ℹ️  No new comments added (likely due to 24-hour cooldown)")
        print(f"   The system respects human-like commenting frequency")
    
    print(f"\n✅ Manual ultra-intelligent scan complete!")

if __name__ == "__main__":
    manual_intelligent_scan()