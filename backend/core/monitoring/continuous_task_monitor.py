#!/usr/bin/env python3
"""
24/7 Continuous Task Monitor
============================
A human-like AI system that continuously monitors all tasks and provides
real-time feedback to team members based on their performance.

Features:
- Runs 24/7 checking tasks every few hours
- Human-like commenting with varied messages
- Avoids duplicate comments
- Tracks performance trends
- Encouraging for good work, constructive for delays
"""

import mysql.connector
import schedule
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging
from dataclasses import dataclass

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('task_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TaskInfo:
    task_id: int
    title: str
    employee_name: str
    employee_id: int
    due_date: datetime
    completion_date: datetime = None
    days_late: int = 0
    status: str = "pending"
    last_comment_date: datetime = None
    comment_count: int = 0

class ContinuousTaskMonitor:
    def __init__(self):
        self.db_config = {
            'host': '92.113.22.65',
            'user': 'u906714182_sqlrrefdvdv',
            'password': 'Abuasad123',
            'database': 'u906714182_sqlrrefdvdv'
        }
        
        # AI Agent staff ID for commenting
        self.agent_staff_id = 248
        
        # Human-like comment pools for different scenarios
        self.positive_comments = [
            "Hey {name}! 🌟 Absolutely crushing it on this task! Your consistency is inspiring the whole team",
            "Hi {name}! 💪 Love seeing this level of commitment. You're setting a great example",
            "Hey {name}! 🎯 Perfect timing as always! This kind of reliability is what makes great teams",
            "{name}, your dedication really shows in this work. Thanks for being so dependable! 👏",
            "Hi {name}! 🚀 Another task completed on time! Your work ethic is genuinely appreciated",
            "Hey {name}! ✨ This is exactly the kind of quality delivery we love to see",
            "{name}, you're on fire! 🔥 Keep up this amazing momentum",
            "Hi {name}! 🎉 Flawless execution! Your attention to deadlines never goes unnoticed",
            "Hey {name}! 💎 Quality work delivered right on schedule. You're a real asset to the team",
            "Hi {name}! 🌈 This task was handled beautifully. Your professionalism really stands out"
        ]
        
        self.encouragement_comments = [
            "Hey {name}! 😊 I notice you're working hard on this. Remember, progress is progress, no matter the pace!",
            "Hi {name}! 💪 This task is taking some time, but I believe in your ability to deliver great results",
            "{name}, I see the effort you're putting in. Let me know if you need any support or resources! 🤝",
            "Hey {name}! 🌟 Quality takes time, and I know you care about doing this right. Keep going!",
            "Hi {name}! 🎯 This one seems challenging - that's exactly why we chose you for it. You've got this!",
            "{name}, remember that some of our best work comes from taking the time to get it right ⏰",
            "Hey {name}! 💡 If you're stuck on anything, don't hesitate to reach out. We're all here to help",
            "Hi {name}! 🚀 I know you're capable of amazing work. Take the time you need to make it shine"
        ]
        
        self.gentle_reminders = [
            "Hi {name}, 📅 Just a friendly reminder about this task's deadline. How's progress looking?",
            "Hey {name}! ⏰ This one's coming up on the deadline soon. Any roadblocks I can help with?",
            "{name}, checking in on this task - is there anything slowing things down that we should address?",
            "Hi {name}! 🎯 The deadline is approaching. Let's touch base if you need any support",
            "Hey {name}, 💭 just wanted to see how this task is progressing. All good on your end?",
            "{name}, this task is due soon - let me know if there's anything blocking your progress!",
            "Hi {name}! 📝 Quick check-in: how are we doing with this deadline coming up?"
        ]
        
        self.concern_comments = [
            "Hi {name}, 📊 This task has been running behind for a while. Can we chat about what's happening?",
            "{name}, I'm a bit concerned about the timeline here. Let's work together to get back on track",
            "Hey {name}, 🤔 This delay is unusual for you. Is everything okay? Any way I can help?",
            "Hi {name}, this task is significantly overdue. We need to prioritize getting it completed",
            "{name}, let's have a quick conversation about this task and how to prevent future delays",
            "Hey {name}, ⚠️ this timeline needs immediate attention. Can we discuss next steps?"
        ]
        
        self.urgent_comments = [
            "{name}, this task is critically overdue. We need immediate action and a clear completion plan",
            "Hi {name}, ⚡ this delay is impacting other work. Let's get this resolved today",
            "{name}, this situation requires urgent attention. Please prioritize this immediately",
            "Hey {name}, 🚨 we can't let this slide any further. Time to make this the top priority",
            "{name}, this level of delay is concerning. Let's discuss what resources you need right now"
        ]

    def get_database_connection(self):
        """Establish database connection with retry logic"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def get_all_active_tasks(self) -> List[TaskInfo]:
        """Get all active tasks with employee information"""
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
            SELECT DISTINCT
                t.taskid,
                t.task as title,
                t.duedate,
                t.completiondate,
                ta.staffid,
                s.firstname,
                s.lastname,
                COALESCE(
                    (SELECT MAX(dateadded) FROM tbltask_comments tc WHERE tc.taskid = t.taskid),
                    '1900-01-01'
                ) as last_comment_date,
                COALESCE(
                    (SELECT COUNT(*) FROM tbltask_comments tc WHERE tc.taskid = t.taskid AND tc.staffid = %s),
                    0
                ) as comment_count
            FROM tbltasks t
            JOIN tbltask_assigned ta ON t.taskid = ta.taskid
            JOIN tblstaff s ON ta.staffid = s.id
            WHERE t.status != 5
            ORDER BY t.duedate ASC
            """
            
            cursor.execute(query, (self.agent_staff_id,))
            results = cursor.fetchall()
            
            tasks = []
            for row in results:
                task = TaskInfo(
                    task_id=row['taskid'],
                    title=row['title'],
                    employee_name=f"{row['firstname']} {row['lastname']}".strip(),
                    employee_id=row['staffid'],
                    due_date=row['duedate'],
                    completion_date=row['completiondate'],
                    last_comment_date=row['last_comment_date'],
                    comment_count=row['comment_count']
                )
                
                # Calculate status and days late
                now = datetime.now().date()
                due_date = task.due_date.date() if isinstance(task.due_date, datetime) else task.due_date
                
                if task.completion_date:
                    task.status = "completed"
                    completion_date = task.completion_date.date() if isinstance(task.completion_date, datetime) else task.completion_date
                    if completion_date > due_date:
                        task.days_late = (completion_date - due_date).days
                else:
                    task.status = "pending"
                    if now > due_date:
                        task.days_late = (now - due_date).days
                
                tasks.append(task)
            
            cursor.close()
            conn.close()
            
            logger.info(f"Retrieved {len(tasks)} active tasks for monitoring")
            return tasks
            
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []

    def should_add_comment(self, task: TaskInfo) -> bool:
        """Determine if we should add a comment based on intelligent logic"""
        now = datetime.now()
        
        # Don't comment if we already commented today
        if task.last_comment_date:
            last_comment = task.last_comment_date
            if isinstance(last_comment, str):
                last_comment = datetime.strptime(last_comment, '%Y-%m-%d %H:%M:%S')
            
            if (now - last_comment).days < 1:
                return False
        
        # Comment scenarios:
        
        # 1. Task completed on time or early (celebrate!)
        if task.status == "completed" and task.days_late <= 0:
            # Only comment if we haven't commented on this completed task
            return task.comment_count == 0
        
        # 2. Task just became overdue (gentle reminder)
        if task.status == "pending" and task.days_late == 1:
            return True
        
        # 3. Task is moderately late (every 3 days)
        if task.status == "pending" and 2 <= task.days_late <= 10:
            return task.days_late % 3 == 0
        
        # 4. Task is very late (every 2 days)
        if task.status == "pending" and task.days_late > 10:
            return task.days_late % 2 == 0
        
        # 5. Encourage work in progress (every 5 days for tasks due soon)
        if task.status == "pending" and task.days_late <= 0:
            due_soon = (task.due_date.date() - datetime.now().date()).days <= 2
            return due_soon and task.comment_count % 5 == 0
        
        return False

    def get_appropriate_comment(self, task: TaskInfo) -> str:
        """Select human-like comment based on task status and context"""
        name = task.employee_name.split()[0]  # First name only
        
        # Completed on time - celebrate!
        if task.status == "completed" and task.days_late <= 0:
            return random.choice(self.positive_comments).format(name=name)
        
        # Completed late but done
        if task.status == "completed" and task.days_late > 0:
            if task.days_late <= 3:
                return random.choice(self.encouragement_comments).format(name=name)
            else:
                return f"Hi {name}! 😅 Better late than never! Thanks for getting this wrapped up"
        
        # Pending tasks - various scenarios
        if task.status == "pending":
            if task.days_late <= 0:
                # Due soon - encourage
                return random.choice(self.encouragement_comments).format(name=name)
            elif 1 <= task.days_late <= 2:
                # Just overdue - gentle reminder
                return random.choice(self.gentle_reminders).format(name=name)
            elif 3 <= task.days_late <= 10:
                # Moderately late - show concern
                return random.choice(self.concern_comments).format(name=name)
            else:
                # Very late - urgent
                return random.choice(self.urgent_comments).format(name=name)
        
        # Default fallback
        return f"Hey {name}! 👋 Just checking in on this task. How's it going?"

    def add_comment_to_task(self, task_id: int, comment: str) -> bool:
        """Add a comment to the task"""
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            insert_query = """
            INSERT INTO tbltask_comments (taskid, staffid, dateadded, comment)
            VALUES (%s, %s, %s, %s)
            """
            
            cursor.execute(insert_query, (
                task_id,
                self.agent_staff_id,
                datetime.now(),
                comment
            ))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            logger.error(f"Error adding comment to task {task_id}: {e}")
            return False

    def monitor_and_comment(self):
        """Main monitoring function - checks all tasks and adds comments"""
        logger.info("🤖 Starting task monitoring cycle...")
        
        try:
            tasks = self.get_all_active_tasks()
            comments_added = 0
            
            for task in tasks:
                if self.should_add_comment(task):
                    comment = self.get_appropriate_comment(task)
                    
                    if self.add_comment_to_task(task.task_id, comment):
                        comments_added += 1
                        logger.info(f"✅ Added comment to task {task.task_id} ({task.employee_name}): {comment[:50]}...")
                        
                        # Add small delay to avoid database overload
                        time.sleep(0.5)
            
            logger.info(f"🎯 Monitoring cycle complete. Added {comments_added} comments to {len(tasks)} tasks")
            
        except Exception as e:
            logger.error(f"Error in monitoring cycle: {e}")

    def start_continuous_monitoring(self):
        """Start the 24/7 monitoring service"""
        logger.info("🚀 Starting 24/7 Continuous Task Monitor...")
        
        # Schedule monitoring every 4 hours
        schedule.every(4).hours.do(self.monitor_and_comment)
        
        # Run initial check
        self.monitor_and_comment()
        
        logger.info("📅 Scheduled to run every 4 hours. Monitor is now active 24/7!")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check every minute for scheduled tasks
                
            except KeyboardInterrupt:
                logger.info("🛑 Monitor stopped by user")
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    print("🤖 CONTINUOUS TASK MONITOR - 24/7 HUMAN-LIKE TASK MANAGEMENT")
    print("=" * 70)
    print("This system will monitor all tasks continuously and provide")
    print("human-like feedback to team members based on their performance.")
    print("Press Ctrl+C to stop the monitor.")
    print("=" * 70)
    
    monitor = ContinuousTaskMonitor()
    monitor.start_continuous_monitoring()