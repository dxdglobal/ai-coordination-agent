#!/usr/bin/env python3
"""
Smart Comment Manager
====================
Intelligent comment management system that tracks employee patterns,
performance trends, and provides personalized human-like feedback.
"""

import mysql.connector
from datetime import datetime, timedelta
from typing import List, Dict, Set
import random
import logging

logger = logging.getLogger(__name__)

class SmartCommentManager:
    def __init__(self, db_config: dict, agent_staff_id: int):
        self.db_config = db_config
        self.agent_staff_id = agent_staff_id
        
        # Track employee performance patterns
        self.employee_patterns = {}
        
        # Time-sensitive comments
        self.morning_greetings = [
            "Good morning {name}! ☀️",
            "Morning {name}! 🌅", 
            "Hey {name}! Hope you're having a great morning! ☕"
        ]
        
        self.afternoon_checkins = [
            "Hey {name}! 🌤️",
            "Hi {name}! Hope your day is going well! 📈",
            "Afternoon {name}! 🌞"
        ]
        
        self.evening_comments = [
            "Hey {name}! 🌆",
            "Hi {name}! End of day check-in 📋",
            "Evening {name}! 🌙"
        ]
        
        # Context-aware motivational comments
        self.monday_motivation = [
            "Monday energy! Let's make this week amazing! 💪",
            "New week, new opportunities! 🚀",
            "Monday momentum! Let's get this! 🔥"
        ]
        
        self.friday_encouragement = [
            "Friday focus! Let's finish strong! 🎯",
            "Almost weekend! One final push! 💪",
            "Friday finale! You've got this! 🌟"
        ]
        
        # Performance-based comment variations
        self.consistent_performer_comments = [
            "Your consistency is absolutely incredible! The whole team looks up to your reliability 🌟",
            "You're the definition of dependable! Thanks for being such a solid team member 💪",
            "Your track record speaks for itself - pure excellence! 🏆"
        ]
        
        self.improving_performer_comments = [
            "I'm really seeing great improvement in your work! Keep up this positive momentum 📈",
            "Love seeing this upward trend in your performance! You're on fire! 🔥",
            "Your growth is genuinely inspiring! This is exactly what progress looks like 🚀"
        ]
        
        self.struggling_performer_comments = [
            "I know you have so much potential. Let's work together to unlock it! 🤝",
            "Every expert was once a beginner. You're learning and growing, and that's what matters 🌱",
            "I believe in your abilities. Sometimes we just need to find the right approach 💡"
        ]

    def get_time_appropriate_greeting(self) -> str:
        """Get greeting based on current time"""
        hour = datetime.now().hour
        
        if 5 <= hour < 12:
            return random.choice(self.morning_greetings)
        elif 12 <= hour < 17:
            return random.choice(self.afternoon_checkins)
        else:
            return random.choice(self.evening_comments)

    def get_day_context_comment(self) -> str:
        """Get day-specific motivational content"""
        day = datetime.now().weekday()  # 0 = Monday, 4 = Friday
        
        if day == 0:  # Monday
            return random.choice(self.monday_motivation)
        elif day == 4:  # Friday
            return random.choice(self.friday_encouragement)
        else:
            return ""

    def analyze_employee_performance(self, employee_id: int) -> Dict:
        """Analyze employee's recent performance pattern"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            
            # Get recent task completion data
            query = """
            SELECT 
                t.taskid,
                t.duedate,
                t.completiondate,
                DATEDIFF(COALESCE(t.completiondate, CURDATE()), t.duedate) as days_late
            FROM tbltasks t
            JOIN tbltask_assigned ta ON t.taskid = ta.taskid
            WHERE ta.staffid = %s 
                AND t.duedate >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            ORDER BY t.duedate DESC
            LIMIT 20
            """
            
            cursor.execute(query, (employee_id,))
            tasks = cursor.fetchall()
            
            if not tasks:
                return {"pattern": "new", "performance_score": 50}
            
            # Calculate performance metrics
            completed_tasks = [t for t in tasks if t['completiondate']]
            on_time_tasks = [t for t in completed_tasks if t['days_late'] <= 0]
            
            completion_rate = len(completed_tasks) / len(tasks) if tasks else 0
            on_time_rate = len(on_time_tasks) / len(completed_tasks) if completed_tasks else 0
            
            avg_delay = sum(max(0, t['days_late']) for t in completed_tasks) / len(completed_tasks) if completed_tasks else 0
            
            # Determine pattern
            performance_score = (completion_rate * 40) + (on_time_rate * 40) + (max(0, 20 - avg_delay * 2))
            
            if performance_score >= 80:
                pattern = "consistent_performer"
            elif performance_score >= 60:
                pattern = "improving_performer"
            else:
                pattern = "struggling_performer"
            
            cursor.close()
            conn.close()
            
            return {
                "pattern": pattern,
                "performance_score": performance_score,
                "completion_rate": completion_rate,
                "on_time_rate": on_time_rate,
                "avg_delay": avg_delay
            }
            
        except Exception as e:
            logger.error(f"Error analyzing employee {employee_id}: {e}")
            return {"pattern": "unknown", "performance_score": 50}

    def get_personalized_comment_style(self, employee_id: int, base_comment: str, task_context: str) -> str:
        """Enhance comment with personalized touch based on employee pattern"""
        
        # Get employee performance analysis
        performance = self.analyze_employee_performance(employee_id)
        pattern = performance["pattern"]
        
        # Get time and day context
        greeting = self.get_time_appropriate_greeting()
        day_context = self.get_day_context_comment()
        
        # Build personalized comment
        enhanced_comment = base_comment
        
        # Add performance-specific encouragement
        if pattern == "consistent_performer" and random.random() < 0.3:
            enhanced_comment += f" {random.choice(self.consistent_performer_comments)}"
        elif pattern == "improving_performer" and random.random() < 0.4:
            enhanced_comment += f" {random.choice(self.improving_performer_comments)}"
        elif pattern == "struggling_performer" and random.random() < 0.5:
            enhanced_comment += f" {random.choice(self.struggling_performer_comments)}"
        
        # Add day-specific motivation
        if day_context and random.random() < 0.2:
            enhanced_comment += f" {day_context}"
        
        return enhanced_comment

    def check_comment_frequency(self, employee_id: int, task_id: int) -> Dict:
        """Check recent comment patterns to avoid spam"""
        try:
            conn = mysql.connector.connect(**self.db_config)
            cursor = conn.cursor(dictionary=True)
            
            # Check recent comments to this employee
            query = """
            SELECT COUNT(*) as recent_comments
            FROM tbltask_comments tc
            JOIN tbltask_assigned ta ON tc.taskid = ta.taskid
            WHERE ta.staffid = %s 
                AND tc.staffid = %s 
                AND tc.dateadded >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """
            
            cursor.execute(query, (employee_id, self.agent_staff_id))
            result = cursor.fetchone()
            
            recent_comments = result['recent_comments'] if result else 0
            
            cursor.close()
            conn.close()
            
            return {
                "recent_comments": recent_comments,
                "should_limit": recent_comments > 3  # Max 3 comments per employee per day
            }
            
        except Exception as e:
            logger.error(f"Error checking comment frequency: {e}")
            return {"recent_comments": 0, "should_limit": False}

    def generate_contextual_comment(self, task_info: Dict) -> str:
        """Generate highly contextual, human-like comment"""
        
        name = task_info['employee_name'].split()[0]
        employee_id = task_info['employee_id']
        days_late = task_info['days_late']
        task_title = task_info['title']
        
        # Check if we should limit comments to this employee
        frequency_check = self.check_comment_frequency(employee_id, task_info['task_id'])
        
        if frequency_check["should_limit"]:
            return None  # Skip commenting for now
        
        # Generate base comment based on context
        base_comment = self._generate_base_comment(name, days_late, task_title)
        
        # Enhance with personalization
        final_comment = self.get_personalized_comment_style(
            employee_id, base_comment, task_info['status']
        )
        
        return final_comment

    def _generate_base_comment(self, name: str, days_late: int, task_title: str) -> str:
        """Generate base comment before personalization"""
        
        # Contextual responses based on task content
        task_lower = task_title.lower()
        
        if 'deploy' in task_lower or 'release' in task_lower:
            context = "deployment"
        elif 'fix' in task_lower or 'bug' in task_lower:
            context = "bugfix"
        elif 'create' in task_lower or 'develop' in task_lower:
            context = "development"
        elif 'test' in task_lower:
            context = "testing"
        else:
            context = "general"
        
        # Time-based greeting
        greeting = self.get_time_appropriate_greeting().format(name=name)
        
        if days_late <= 0:
            return f"{greeting} Perfect timing on this {context} task! Your reliability makes everyone's job easier 🎯"
        elif days_late <= 2:
            return f"{greeting} Just a gentle nudge on this {context} task. No rush, but wanted to keep it on your radar 📋"
        elif days_late <= 5:
            return f"{greeting} This {context} task needs some attention. Can we prioritize getting it wrapped up? 🔧"
        else:
            return f"{greeting} We really need to get this {context} task moving. Let's chat about what's blocking progress 🚨"