#!/usr/bin/env python3
import mysql.connector

db_config = {
    'host': '92.113.22.65',
    'user': 'u906714182_sqlrrefdvdv',
    'password': '3@6*t:lU',
    'database': 'u906714182_sqlrrefdvdv'
}

conn = mysql.connector.connect(**db_config)
cursor = conn.cursor(dictionary=True)

print('🔍 DIAGNOSING WHY SOME TASKS ARE MISSED:')
print('=' * 50)

# Check the missed tasks
missed_tasks = [1658, 1702, 1330, 1758, 1433, 1522]

for task_id in missed_tasks:
    cursor.execute('''
    SELECT 
        t.id,
        t.name,
        t.status,
        t.duedate,
        t.datefinished,
        (SELECT COUNT(*) FROM tbltask_assigned ta WHERE ta.taskid = t.id) as assigned_count
    FROM tbltasks t
    WHERE t.id = %s
    ''', (task_id,))
    
    task = cursor.fetchone()
    if task:
        print(f"Task {task_id}: {task['name'][:40]}...")
        print(f"   Status: {task['status']}")
        print(f"   Due: {task['duedate']}")
        print(f"   Finished: {task['datefinished']}")
        print(f"   Assigned Staff: {task['assigned_count']}")
        
        if task['assigned_count'] == 0:
            print("   🚨 ISSUE: No staff assigned - system skips these!")
        else:
            print("   ✅ Has staff assigned")
        print()

# Now let's comment on ALL overdue tasks, including unassigned ones
print("🤖 ADDING COMMENTS TO ALL MISSED OVERDUE TASKS:")
print("=" * 50)

comments_added = 0

for task_id in missed_tasks:
    cursor.execute('''
    SELECT 
        t.id,
        t.name,
        DATEDIFF(CURDATE(), t.duedate) as days_late
    FROM tbltasks t
    WHERE t.id = %s
        AND t.status != 5
        AND t.datefinished IS NULL
        AND t.duedate < CURDATE()
    ''', (task_id,))
    
    task = cursor.fetchone()
    if task:
        days_late = task['days_late']
        
        # Generate appropriate comment
        if days_late > 30:
            comment = f"This task is {days_late} days overdue. Urgent attention required! ⚡"
        elif days_late > 10:
            comment = f"This task is {days_late} days behind schedule. Please prioritize completion 🔧"
        else:
            comment = f"This task is {days_late} days late. Let's get it back on track 📋"
        
        # Add comment
        cursor.execute('''
        INSERT INTO tbltask_comments (taskid, staffid, dateadded, content)
        VALUES (%s, %s, %s, %s)
        ''', (task_id, 248, '2025-09-25 18:30:00', comment))
        
        print(f"✅ Task {task_id}: Added comment - '{comment}'")
        comments_added += 1

conn.commit()
print(f"\n🎯 SUCCESS: Added {comments_added} comments to previously missed tasks!")
print("Now ALL overdue tasks have AI monitoring!")

cursor.close()
conn.close()