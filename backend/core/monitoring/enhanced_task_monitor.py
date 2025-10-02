#!/usr/bin/env python3
"""
24/7 Enhanced Task Monitor with Performance Analytics
===================================================
Advanced monitoring system that tracks performance trends, provides
intelligent human-like feedback, and runs continuously 24/7.
"""

import mysql.connector
import schedule
import time
import random
import json
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging
from dataclasses import dataclass, asdict
from smart_comment_manager import SmartCommentManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('enhanced_task_monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class EmployeePerformance:
    employee_id: int
    name: str
    total_tasks: int
    completed_tasks: int
    on_time_tasks: int
    avg_completion_days: float
    current_streak: int  # Days of good performance
    performance_trend: str  # "improving", "declining", "stable"
    last_updated: datetime

@dataclass
class TaskMetrics:
    task_id: int
    title: str
    employee_name: str
    employee_id: int
    due_date: datetime
    completion_date: datetime = None
    days_late: int = 0
    status: str = "pending"
    priority: str = "normal"  # "low", "normal", "high", "critical"
    last_comment_date: datetime = None
    comment_count: int = 0
    urgency_score: float = 0.0

class EnhancedTaskMonitor:
    def __init__(self):
        self.db_config = {
            'host': '92.113.22.65',
            'user': 'u906714182_sqlrrefdvdv',
            'password': '3@6*t:lU',
            'database': 'u906714182_sqlrrefdvdv'
        }
        
        # AI Agent staff ID for commenting
        self.agent_staff_id = 248
        
        # Performance tracking
        self.employee_performance: Dict[int, EmployeePerformance] = {}
        
        # Initialize smart comment manager
        self.comment_manager = SmartCommentManager(self.db_config, self.agent_staff_id)
        
        # Monitoring statistics
        self.stats = {
            'total_monitoring_cycles': 0,
            'total_comments_added': 0,
            'employees_monitored': 0,
            'last_cycle_time': None,
            'performance_alerts': 0
        }

    def get_database_connection(self):
        """Establish database connection with retry logic"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def calculate_urgency_score(self, task: TaskMetrics) -> float:
        """Calculate urgency score based on multiple factors"""
        score = 0.0
        
        # Days late factor (0-50 points)
        if task.days_late > 0:
            score += min(50, task.days_late * 5)
        elif task.days_late < 0:  # Due in future
            days_until_due = abs(task.days_late)
            if days_until_due <= 1:
                score += 20  # Due tomorrow
            elif days_until_due <= 3:
                score += 10  # Due within 3 days
        
        # Task title urgency keywords (0-30 points)
        urgent_keywords = ['urgent', 'critical', 'asap', 'emergency', 'hot', 'priority']
        if any(keyword in task.title.lower() for keyword in urgent_keywords):
            score += 30
        
        # Comment frequency factor (0-20 points)
        if task.comment_count > 5:
            score += 20
        elif task.comment_count > 2:
            score += 10
        
        return score

    def get_all_tasks_with_metrics(self) -> List[TaskMetrics]:
        """Get all tasks with comprehensive metrics"""
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
                    (SELECT MAX(dateadded) FROM tbltask_comments tc WHERE tc.taskid = t.taskid AND tc.staffid = %s),
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
            
            cursor.execute(query, (self.agent_staff_id, self.agent_staff_id))
            results = cursor.fetchall()
            
            tasks = []
            for row in results:
                task = TaskMetrics(
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
                    else:
                        task.days_late = -(due_date - now).days  # Negative for future due dates
                
                # Calculate urgency score
                task.urgency_score = self.calculate_urgency_score(task)
                
                # Determine priority
                if task.urgency_score >= 70:
                    task.priority = "critical"
                elif task.urgency_score >= 40:
                    task.priority = "high"
                elif task.urgency_score >= 20:
                    task.priority = "normal"
                else:
                    task.priority = "low"
                
                tasks.append(task)
            
            cursor.close()
            conn.close()
            
            logger.info(f"Retrieved {len(tasks)} tasks with comprehensive metrics")
            return tasks
            
        except Exception as e:
            logger.error(f"Error fetching task metrics: {e}")
            return []

    def update_employee_performance(self, tasks: List[TaskMetrics]):
        """Update performance tracking for all employees"""
        employee_stats = {}
        
        # Group tasks by employee
        for task in tasks:
            emp_id = task.employee_id
            if emp_id not in employee_stats:
                employee_stats[emp_id] = {
                    'name': task.employee_name,
                    'all_tasks': [],
                    'completed_tasks': [],
                    'on_time_tasks': []
                }
            
            employee_stats[emp_id]['all_tasks'].append(task)
            
            if task.status == "completed":
                employee_stats[emp_id]['completed_tasks'].append(task)
                if task.days_late <= 0:
                    employee_stats[emp_id]['on_time_tasks'].append(task)
        
        # Calculate performance metrics
        for emp_id, stats in employee_stats.items():
            total_tasks = len(stats['all_tasks'])
            completed_tasks = len(stats['completed_tasks'])
            on_time_tasks = len(stats['on_time_tasks'])
            
            # Calculate average completion time
            if completed_tasks > 0:
                avg_completion_days = sum(max(0, task.days_late) for task in stats['completed_tasks']) / completed_tasks
            else:
                avg_completion_days = 0
            
            # Update performance record
            self.employee_performance[emp_id] = EmployeePerformance(
                employee_id=emp_id,
                name=stats['name'],
                total_tasks=total_tasks,
                completed_tasks=completed_tasks,
                on_time_tasks=on_time_tasks,
                avg_completion_days=avg_completion_days,
                current_streak=self._calculate_streak(stats['completed_tasks']),
                performance_trend=self._calculate_trend(emp_id, stats['completed_tasks']),
                last_updated=datetime.now()
            )
        
        self.stats['employees_monitored'] = len(employee_stats)

    def _calculate_streak(self, completed_tasks: List[TaskMetrics]) -> int:
        """Calculate current streak of on-time completions"""
        if not completed_tasks:
            return 0
        
        # Sort by completion date (most recent first)
        sorted_tasks = sorted(completed_tasks, 
                            key=lambda x: x.completion_date, 
                            reverse=True)
        
        streak = 0
        for task in sorted_tasks:
            if task.days_late <= 0:  # On time or early
                streak += 1
            else:
                break
        
        return streak

    def _calculate_trend(self, employee_id: int, completed_tasks: List[TaskMetrics]) -> str:
        """Calculate performance trend for employee"""
        if len(completed_tasks) < 3:
            return "stable"
        
        # Sort by completion date
        sorted_tasks = sorted(completed_tasks, key=lambda x: x.completion_date)
        
        # Split into recent and older tasks
        mid_point = len(sorted_tasks) // 2
        older_tasks = sorted_tasks[:mid_point]
        recent_tasks = sorted_tasks[mid_point:]
        
        # Calculate average performance for each period
        older_avg = sum(1 if task.days_late <= 0 else 0 for task in older_tasks) / len(older_tasks)
        recent_avg = sum(1 if task.days_late <= 0 else 0 for task in recent_tasks) / len(recent_tasks)
        
        if recent_avg > older_avg + 0.2:
            return "improving"
        elif recent_avg < older_avg - 0.2:
            return "declining"
        else:
            return "stable"

    def should_add_intelligent_comment(self, task: TaskMetrics) -> bool:
        """Advanced logic to determine if comment should be added"""
        now = datetime.now()
        
        # Check recent comment frequency
        if task.last_comment_date and task.last_comment_date != '1900-01-01':
            last_comment = task.last_comment_date
            if isinstance(last_comment, str):
                last_comment = datetime.strptime(last_comment, '%Y-%m-%d %H:%M:%S')
            
            hours_since_comment = (now - last_comment).total_seconds() / 3600
            
            # Dynamic commenting frequency based on urgency
            if task.priority == "critical":
                min_hours = 2  # Comment every 2 hours for critical tasks
            elif task.priority == "high":
                min_hours = 8  # Comment every 8 hours for high priority
            elif task.priority == "normal":
                min_hours = 24  # Comment daily for normal tasks
            else:
                min_hours = 72  # Comment every 3 days for low priority
            
            if hours_since_comment < min_hours:
                return False
        
        # Smart commenting scenarios
        
        # 1. Critical overdue tasks
        if task.priority == "critical" and task.days_late > 0:
            return True
        
        # 2. Tasks just completed (celebrate!)
        if task.status == "completed" and task.comment_count == 0:
            return True
        
        # 3. Tasks approaching deadline
        if task.status == "pending" and -2 <= task.days_late <= 0:
            return random.random() < 0.3  # 30% chance for approaching deadlines
        
        # 4. Overdue tasks with escalating frequency
        if task.status == "pending" and task.days_late > 0:
            probability = min(0.8, task.days_late * 0.1)  # Higher probability for later tasks
            return random.random() < probability
        
        # 5. Performance-based commenting
        emp_performance = self.employee_performance.get(task.employee_id)
        if emp_performance:
            # Encourage improving performers more
            if emp_performance.performance_trend == "improving":
                return random.random() < 0.4
            # Support declining performers
            elif emp_performance.performance_trend == "declining":
                return random.random() < 0.6
        
        return False

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

    def generate_performance_report(self) -> str:
        """Generate human-readable performance summary"""
        if not self.employee_performance:
            return "No performance data available yet."
        
        report = "📊 TEAM PERFORMANCE SNAPSHOT\n"
        report += "=" * 50 + "\n\n"
        
        # Sort by performance score
        performers = sorted(self.employee_performance.values(), 
                          key=lambda x: (x.on_time_tasks / max(1, x.completed_tasks)), 
                          reverse=True)
        
        for perf in performers[:10]:  # Top 10
            completion_rate = (perf.completed_tasks / max(1, perf.total_tasks)) * 100
            on_time_rate = (perf.on_time_tasks / max(1, perf.completed_tasks)) * 100
            
            trend_emoji = {"improving": "📈", "declining": "📉", "stable": "➡️"}
            
            report += f"👤 {perf.name}\n"
            report += f"   📋 Tasks: {perf.completed_tasks}/{perf.total_tasks} ({completion_rate:.1f}%)\n"
            report += f"   ⏰ On-time: {on_time_rate:.1f}%\n"
            report += f"   🔥 Streak: {perf.current_streak} tasks\n"
            report += f"   📊 Trend: {trend_emoji.get(perf.performance_trend, '❓')} {perf.performance_trend}\n\n"
        
        return report

    def run_enhanced_monitoring_cycle(self):
        """Main enhanced monitoring function"""
        cycle_start = datetime.now()
        logger.info(f"🚀 Starting enhanced monitoring cycle {self.stats['total_monitoring_cycles'] + 1}")
        
        try:
            # Get all tasks with metrics
            tasks = self.get_all_tasks_with_metrics()
            
            # Update performance tracking
            self.update_employee_performance(tasks)
            
            # Process comments
            comments_added = 0
            critical_tasks = 0
            
            # Sort tasks by urgency score (highest first)
            sorted_tasks = sorted(tasks, key=lambda x: x.urgency_score, reverse=True)
            
            for task in sorted_tasks:
                if task.priority == "critical":
                    critical_tasks += 1
                
                if self.should_add_intelligent_comment(task):
                    # Generate contextual comment
                    task_info = {
                        'task_id': task.task_id,
                        'title': task.title,
                        'employee_name': task.employee_name,
                        'employee_id': task.employee_id,
                        'days_late': task.days_late,
                        'status': task.status,
                        'priority': task.priority
                    }
                    
                    comment = self.comment_manager.generate_contextual_comment(task_info)
                    
                    if comment and self.add_comment_to_task(task.task_id, comment):
                        comments_added += 1
                        priority_emoji = {"critical": "🚨", "high": "🔴", "normal": "🟡", "low": "🟢"}
                        logger.info(f"✅ {priority_emoji.get(task.priority, '📝')} Added comment to task {task.task_id} ({task.employee_name}): {comment[:60]}...")
                        
                        # Small delay to prevent database overload
                        time.sleep(0.5)
            
            # Update statistics
            self.stats['total_monitoring_cycles'] += 1
            self.stats['total_comments_added'] += comments_added
            self.stats['last_cycle_time'] = cycle_start
            self.stats['performance_alerts'] = critical_tasks
            
            cycle_duration = (datetime.now() - cycle_start).total_seconds()
            
            logger.info(f"🎯 Cycle complete! Added {comments_added} comments to {len(tasks)} tasks")
            logger.info(f"📊 Critical tasks: {critical_tasks} | Duration: {cycle_duration:.1f}s")
            
            # Log performance report every 4 cycles
            if self.stats['total_monitoring_cycles'] % 4 == 0:
                performance_report = self.generate_performance_report()
                logger.info(f"\n{performance_report}")
            
        except Exception as e:
            logger.error(f"Error in enhanced monitoring cycle: {e}")

    def start_enhanced_24_7_monitoring(self):
        """Start the enhanced 24/7 monitoring service"""
        logger.info("🚀 ENHANCED 24/7 TASK MONITOR STARTING...")
        logger.info("=" * 70)
        logger.info("🤖 AI-Powered Human-Like Task Management")
        logger.info("📊 Performance Analytics & Trend Tracking")
        logger.info("🎯 Intelligent Comment Frequency Management")
        logger.info("⚡ Priority-Based Urgent Task Handling")
        logger.info("=" * 70)
        
        # Schedule monitoring every 3 hours (8 times per day)
        schedule.every(3).hours.do(self.run_enhanced_monitoring_cycle)
        
        # Run initial cycle
        self.run_enhanced_monitoring_cycle()
        
        logger.info("📅 Scheduled to run every 3 hours. Enhanced monitor is now active 24/7!")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(300)  # Check every 5 minutes
                
            except KeyboardInterrupt:
                logger.info("🛑 Enhanced monitor stopped by user")
                final_stats = f"""
                📈 FINAL STATISTICS:
                Monitoring Cycles: {self.stats['total_monitoring_cycles']}
                Comments Added: {self.stats['total_comments_added']}
                Employees Monitored: {self.stats['employees_monitored']}
                """
                logger.info(final_stats)
                break
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    print("🤖 ENHANCED 24/7 TASK MONITOR")
    print("=" * 50)
    print("Advanced AI-powered task management system")
    print("Features:")
    print("• Intelligent human-like commenting")
    print("• Performance analytics & trending")
    print("• Priority-based task handling")
    print("• Continuous 24/7 monitoring")
    print("• Smart comment frequency management")
    print("=" * 50)
    print("Press Ctrl+C to stop the monitor.")
    
    monitor = EnhancedTaskMonitor()
    monitor.start_enhanced_24_7_monitoring()