#!/usr/bin/env python3
"""
Human-Like Task Monitor - 10 Minute Cycles with 24-Hour Comment Rules
====================================================================
A truly human-like monitoring system that:
- Checks every 10 minutes like a real manager would
- Respects 24-hour comment cooldown (no spam!)
- Behaves intelligently like a human manager
- Only comments when it makes sense
"""

import mysql.connector
import schedule
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('human_task_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HumanLikeTaskMonitor:
    def __init__(self):
        self.db_config = {
            'host': '92.113.22.65',
            'user': 'u906714182_sqlrrefdvdv',
            'password': '3@6*t:lU',
            'database': 'u906714182_sqlrrefdvdv'
        }
        
        # AI Agent staff ID for commenting
        self.agent_staff_id = 248
        
        # Human-like timing patterns
        self.working_hours = {
            'start': 9,  # 9 AM
            'end': 18,   # 6 PM
            'timezone': 'local'
        }
        
        # Statistics
        self.stats = {
            'total_checks': 0,
            'comments_added_today': 0,
            'last_comment_time': None,
            'tasks_monitored': 0
        }
        
        # Human-like comment pools organized by context
        self.greeting_patterns = [
            "Hey {name}! 👋",
            "Hi {name}! 😊", 
            "Morning {name}! ☀️",
            "Afternoon {name}! 🌤️",
            "{name}, hope you're doing well! 💪"
        ]
        
        self.positive_reactions = [
            "Awesome work getting this done on time! 🎉",
            "Perfect timing! Your reliability is gold ⭐",
            "Nailed it! Thanks for staying on track 🎯",
            "Excellent execution! This is how it's done 💪",
            "Love seeing tasks completed right on schedule! 🚀",
            "Great job! Your consistency really shows 👏",
            "Fantastic work! You're setting a great example ✨",
            "Outstanding! This kind of reliability makes my day 🌟"
        ]
        
        self.gentle_reminders = [
            "Just a friendly check-in on this one 📝",
            "How's this task coming along? 🤔",
            "Wanted to touch base about the deadline 📅",
            "Any blockers I can help remove? 🛠️",
            "Let me know if you need any support here! 🤝",
            "Quick status check - all good? ✅",
            "Checking in - how are we doing with this? 📊"
        ]
        
        self.concern_expressions = [
            "Getting a bit concerned about the timeline here ⏰",
            "This one's falling behind - can we chat? 💭",
            "The delay is starting to worry me a bit 😟",
            "We need to get this back on track soon 🚨",
            "This timeline needs some immediate attention ⚡",
            "Let's prioritize getting this caught up 🔄"
        ]

    def is_working_hours(self) -> bool:
        """Check if it's currently working hours (like a real manager)"""
        now = datetime.now()
        current_hour = now.hour
        
        # Don't comment outside working hours (be human!)
        return self.working_hours['start'] <= current_hour < self.working_hours['end']
    
    def should_be_less_active(self) -> bool:
        """Determine if we should be less active (lunch time, etc.)"""
        now = datetime.now()
        current_hour = now.hour
        
        # Be less active during lunch time (12-2 PM)
        if 12 <= current_hour < 14:
            return True
        
        # Be less active early morning and late afternoon
        if current_hour < 10 or current_hour > 16:
            return True
            
        return False

    def get_database_connection(self):
        """Establish database connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def has_commented_recently(self, task_id: int) -> tuple[bool, Optional[datetime]]:
        """Check if we've commented on this task within 24 hours"""
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor(dictionary=True)
            
            query = """
            SELECT MAX(dateadded) as last_comment
            FROM tbltask_comments 
            WHERE taskid = %s AND staffid = %s
                AND dateadded >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """
            
            cursor.execute(query, (task_id, self.agent_staff_id))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            if result and result['last_comment']:
                return True, result['last_comment']
            return False, None
            
        except Exception as e:
            logger.error(f"Error checking recent comments for task {task_id}: {e}")
            return False, None

    def get_tasks_needing_attention(self) -> List[Dict]:
        """Get tasks that might need attention (human-like prioritization)"""
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
                DATEDIFF(CURDATE(), t.duedate) as days_late,
                CASE 
                    WHEN t.completiondate IS NOT NULL THEN 'completed'
                    WHEN t.duedate < CURDATE() THEN 'overdue'
                    WHEN DATEDIFF(t.duedate, CURDATE()) <= 2 THEN 'due_soon'
                    ELSE 'pending'
                END as urgency_status
            FROM tbltasks t
            JOIN tbltask_assigned ta ON t.taskid = ta.taskid
            JOIN tblstaff s ON ta.staffid = s.id
            WHERE t.status != 5
            ORDER BY 
                CASE 
                    WHEN t.completiondate IS NOT NULL AND DATEDIFF(COALESCE(t.completiondate, CURDATE()), t.duedate) <= 0 THEN 1
                    WHEN t.duedate < CURDATE() THEN 2
                    WHEN DATEDIFF(t.duedate, CURDATE()) <= 2 THEN 3
                    ELSE 4
                END,
                t.duedate ASC
            LIMIT 50
            """
            
            cursor.execute(query)
            results = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []

    def generate_human_comment(self, task: Dict) -> Optional[str]:
        """Generate a natural, human-like comment"""
        name = task['firstname']
        status = task['urgency_status']
        days_late = task['days_late'] or 0
        
        # Get appropriate greeting based on time
        now = datetime.now()
        if now.hour < 12:
            greeting_pool = [g for g in self.greeting_patterns if "Morning" in g or "Hey" in g]
        elif now.hour < 17:
            greeting_pool = [g for g in self.greeting_patterns if "Afternoon" in g or "Hi" in g]
        else:
            greeting_pool = [g for g in self.greeting_patterns if "hope" in g]
        
        if not greeting_pool:
            greeting_pool = self.greeting_patterns
        
        greeting = random.choice(greeting_pool).format(name=name)
        
        # Generate response based on status
        if status == 'completed' and days_late <= 0:
            # Celebrate on-time completion
            reaction = random.choice(self.positive_reactions)
            return f"{greeting} {reaction}"
            
        elif status == 'completed' and days_late > 0:
            # Acknowledge late completion 
            return f"{greeting} Thanks for getting this finished! Better late than never 😊"
            
        elif status == 'due_soon':
            # Gentle reminder for upcoming deadlines
            reminder = random.choice(self.gentle_reminders)
            return f"{greeting} {reminder} The deadline is coming up soon!"
            
        elif status == 'overdue':
            if days_late <= 2:
                # Gentle nudge for recently overdue
                return f"{greeting} This task slipped past its deadline. Can we get it back on track? 📅"
            elif days_late <= 7:
                # More concern for moderately late
                concern = random.choice(self.concern_expressions)
                return f"{greeting} {concern} This has been overdue for {days_late} days now."
            else:
                # Direct but supportive for very late
                return f"{greeting} This task is significantly overdue ({days_late} days). Let's chat about what's blocking progress and how I can help 🤝"
        
        return None

    def add_comment_to_task(self, task_id: int, comment: str) -> bool:
        """Add comment to task"""
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

    def run_human_check_cycle(self):
        """Run a human-like check cycle every 10 minutes"""
        self.stats['total_checks'] += 1
        
        # Don't work outside office hours
        if not self.is_working_hours():
            logger.info("🌙 Outside working hours - sleeping like a human manager")
            return
        
        logger.info(f"👀 Human-like check #{self.stats['total_checks']} starting...")
        
        try:
            # Get tasks that need attention
            tasks = self.get_tasks_needing_attention()
            self.stats['tasks_monitored'] = len(tasks)
            
            if not tasks:
                logger.info("📋 No tasks need attention right now")
                return
            
            comments_added_this_cycle = 0
            
            # Process tasks with human-like logic
            for task in tasks:
                # Check if we've already commented recently (24-hour rule)
                has_recent_comment, last_comment_time = self.has_commented_recently(task['taskid'])
                
                if has_recent_comment:
                    continue  # Respect the 24-hour rule!
                
                # Decide if we should comment (be selective like a human)
                should_comment = self.decide_to_comment(task)
                
                if should_comment:
                    comment = self.generate_human_comment(task)
                    
                    if comment and self.add_comment_to_task(task['taskid'], comment):
                        comments_added_this_cycle += 1
                        self.stats['comments_added_today'] += 1
                        self.stats['last_comment_time'] = datetime.now()
                        
                        priority_emoji = {
                            'completed': '🎉',
                            'overdue': '⚠️', 
                            'due_soon': '⏰',
                            'pending': '📝'
                        }
                        
                        emoji = priority_emoji.get(task['urgency_status'], '📝')
                        logger.info(f"✅ {emoji} Commented on task {task['taskid']} ({task['firstname']} {task['lastname']})")
                        
                        # Human-like pause between comments
                        time.sleep(random.uniform(2, 5))
                        
                        # Don't comment on too many tasks at once (be human!)
                        if comments_added_this_cycle >= 3:
                            logger.info("📝 Commented on enough tasks for this cycle (being human-like)")
                            break
            
            if comments_added_this_cycle == 0:
                logger.info("✅ All tasks either recently commented or don't need attention")
            else:
                logger.info(f"💬 Added {comments_added_this_cycle} thoughtful comments this cycle")
                
        except Exception as e:
            logger.error(f"Error in human check cycle: {e}")

    def decide_to_comment(self, task: Dict) -> bool:
        """Decide whether to comment like a human manager would"""
        status = task['urgency_status']
        days_late = task['days_late'] or 0
        
        # Always celebrate completed tasks (if not already commented)
        if status == 'completed':
            return True
        
        # Be less active during low-energy times
        if self.should_be_less_active():
            # Only comment on urgent things during low-energy times
            return status in ['overdue'] and days_late > 3
        
        # Comment probabilities (like human attention patterns)
        probabilities = {
            'overdue': min(0.8, 0.2 + (days_late * 0.1)),  # More likely for later tasks
            'due_soon': 0.4,  # Moderate chance for upcoming deadlines
            'pending': 0.1    # Low chance for regular pending tasks
        }
        
        probability = probabilities.get(status, 0)
        return random.random() < probability

    def display_daily_stats(self):
        """Display human-readable stats"""
        stats_msg = f"""
📊 TODAY'S HUMAN-LIKE MONITORING STATS:
• Total checks performed: {self.stats['total_checks']}
• Comments added today: {self.stats['comments_added_today']}
• Tasks currently monitored: {self.stats['tasks_monitored']}
• Last comment time: {self.stats['last_comment_time'] or 'Never'}
• Working like a human manager! 🤖➡️👨‍💼
        """
        logger.info(stats_msg)

    def start_human_monitoring(self):
        """Start the 10-minute human-like monitoring"""
        logger.info("🚀 STARTING HUMAN-LIKE TASK MONITORING")
        logger.info("=" * 60)
        logger.info("⏰ Checking every 10 minutes")
        logger.info("🕘 Only works during business hours (9 AM - 6 PM)")
        logger.info("🚫 24-hour comment cooldown (no spam!)")
        logger.info("👤 Behaves like a real human manager")
        logger.info("=" * 60)
        
        # Schedule every 10 minutes
        schedule.every(10).minutes.do(self.run_human_check_cycle)
        
        # Daily stats at 5 PM
        schedule.every().day.at("17:00").do(self.display_daily_stats)
        
        # Run initial check
        self.run_human_check_cycle()
        
        logger.info("✅ Human-like monitor active! Checking every 10 minutes...")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Check schedule every minute
                
            except KeyboardInterrupt:
                logger.info("🛑 Human-like monitor stopped by user")
                self.display_daily_stats()
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    print("🤖➡️👨‍💼 HUMAN-LIKE TASK MONITOR")
    print("=" * 50)
    print("Features:")
    print("✅ Checks every 10 minutes")
    print("✅ 24-hour comment cooldown (no spam)")
    print("✅ Only works during business hours")
    print("✅ Behaves like a real manager")
    print("✅ Smart, contextual comments")
    print("✅ Celebrates successes, addresses delays")
    print("=" * 50)
    print("Press Ctrl+C to stop")
    
    monitor = HumanLikeTaskMonitor()
    monitor.start_human_monitoring()