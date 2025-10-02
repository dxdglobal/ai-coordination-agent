#!/usr/bin/env python3
"""
Fixed Task Monitor - Compatible with Both SQLite and MySQL
"""

import os
import sys
import sqlite3
import mysql.connector
import schedule
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('human_like_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DatabaseManager:
    def __init__(self):
        self.database_type = os.environ.get('DATABASE_TYPE', 'sqlite')
        
        if self.database_type == 'mysql':
            self.mysql_config = {
                'host': os.environ.get('DB_HOST', '92.113.22.65'),
                'user': os.environ.get('DB_USER', 'u906714182_sqlrrefdvdv'),
                'password': os.environ.get('DB_PASSWORD', '3@6*t:lU'),
                'database': os.environ.get('DB_NAME', 'u906714182_sqlrrefdvdv')
            }
        else:
            self.sqlite_path = 'project_management.db'
    
    def get_connection(self):
        """Get database connection based on type"""
        if self.database_type == 'mysql':
            try:
                return mysql.connector.connect(**self.mysql_config)
            except Exception as e:
                logger.error(f"MySQL connection failed: {e}")
                return None
        else:
            try:
                return sqlite3.connect(self.sqlite_path)
            except Exception as e:
                logger.error(f"SQLite connection failed: {e}")
                return None

class FixedTaskMonitor:
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.agent_staff_id = 248
        
        # Human-like comment patterns
        self.positive_comments = [
            "Hey {name}! 🌟 Great job completing this on time! Your consistency really helps the team",
            "Hi {name}! 💪 Perfect timing on this task. Your reliability is much appreciated",
            "{name}, excellent work! 🎯 Right on schedule as always. Keep it up!",
        ]
        
        self.gentle_reminders = [
            "Hi {name}! 📅 Just a friendly reminder about this task. How's progress looking?",
            "Hey {name}! ⏰ This one's approaching the deadline. Need any support?",
        ]
        
        self.urgent_reminders = [
            "Hi {name}! 🚨 This task is now overdue. Can we prioritize getting it completed?",
            "{name}, this deadline has passed. Let's work together to get back on track",
        ]
        
        self.stats = {
            'checks_performed': 0,
            'comments_added': 0,
            'tasks_monitored': 0,
            'last_check': None
        }

    def get_tasks_to_monitor(self) -> List[Dict]:
        """Get tasks that need monitoring - works with both databases"""
        connection = self.db_manager.get_connection()
        if not connection:
            return []
        
        try:
            cursor = connection.cursor()
            
            if self.db_manager.database_type == 'mysql':
                # MySQL query for external CRM system
                query = """
                SELECT DISTINCT
                    t.id as task_id,
                    t.name as title,
                    t.duedate,
                    t.datefinished as completion_date,
                    ta.staffid,
                    s.firstname,
                    s.lastname,
                    DATEDIFF(CURDATE(), t.duedate) as days_late,
                    CASE 
                        WHEN t.datefinished IS NOT NULL THEN 'completed'
                        WHEN CURDATE() > t.duedate THEN 'overdue'
                        WHEN DATEDIFF(t.duedate, CURDATE()) <= 2 THEN 'due_soon'
                        ELSE 'normal'
                    END as urgency_status
                FROM tbltasks t
                LEFT JOIN tbltask_assigned ta ON t.id = ta.taskid
                LEFT JOIN tblstaff s ON ta.staffid = s.id
                WHERE t.status != 5
                ORDER BY t.duedate ASC
                LIMIT 50
                """
                cursor.execute(query)
                columns = [col[0] for col in cursor.description]
                tasks = [dict(zip(columns, row)) for row in cursor.fetchall()]
                
            else:
                # SQLite query for local database
                query = """
                SELECT 
                    t.id as task_id,
                    t.title,
                    t.end_time as duedate,
                    CASE 
                        WHEN t.status = 'completed' THEN datetime('now')
                        ELSE NULL 
                    END as completion_date,
                    t.assignee as staffid,
                    'User' as firstname,
                    t.assignee as lastname,
                    CASE 
                        WHEN t.status = 'completed' THEN 0
                        WHEN date('now') > date(t.end_time) THEN 
                            julianday('now') - julianday(t.end_time)
                        ELSE 0
                    END as days_late,
                    CASE 
                        WHEN t.status = 'completed' THEN 'completed'
                        WHEN date('now') > date(t.end_time) THEN 'overdue'
                        WHEN julianday(t.end_time) - julianday('now') <= 2 THEN 'due_soon'
                        ELSE 'normal'
                    END as urgency_status
                FROM task t
                WHERE t.status != 'cancelled'
                ORDER BY t.end_time ASC
                LIMIT 50
                """
                cursor.execute(query)
                columns = [description[0] for description in cursor.description]
                tasks = [dict(zip(columns, row)) for row in cursor.fetchall()]
            
            cursor.close()
            connection.close()
            
            logger.info(f"Found {len(tasks)} tasks to monitor")
            return tasks
            
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            if connection:
                connection.close()
            return []

    def monitor_tasks(self):
        """Main monitoring function"""
        logger.info("🔍 Starting task monitoring cycle...")
        
        tasks = self.get_tasks_to_monitor()
        
        if not tasks:
            logger.warning("No tasks found to monitor")
            return
        
        self.stats['tasks_monitored'] = len(tasks)
        self.stats['checks_performed'] += 1
        self.stats['last_check'] = datetime.now()
        
        # Process tasks
        for task in tasks:
            urgency = task.get('urgency_status', 'normal')
            logger.info(f"Task: {task.get('title', 'Unknown')} - Status: {urgency}")
        
        logger.info(f"✅ Monitoring cycle complete. Checked {len(tasks)} tasks")

def run_monitor():
    """Run the monitoring system"""
    print("🤖 FIXED AI COORDINATION AGENT MONITOR")
    print("=" * 50)
    print("   ✅ Multi-database support (SQLite/MySQL)")
    print("   🔍 Checks every 10 minutes")
    print("   📊 Smart task prioritization")
    print("=" * 50)
    
    monitor = FixedTaskMonitor()
    
    # Schedule monitoring every 10 minutes
    schedule.every(10).minutes.do(monitor.monitor_tasks)
    
    # Run initial check
    monitor.monitor_tasks()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(30)  # Check every 30 seconds

if __name__ == "__main__":
    try:
        run_monitor()
    except KeyboardInterrupt:
        logger.info("Monitor stopped by user")
    except Exception as e:
        logger.error(f"Monitor crashed: {e}")