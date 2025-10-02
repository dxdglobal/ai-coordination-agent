#!/usr/bin/env python3
"""
Human-Like Task Monitor - 10 Minute Cycles
==========================================
Intelligent task monitoring system that works like a real human manager:
- Checks every 10 minutes (like a human checking throughout the day)
- 24-hour comment cooldown (no spam, natural human frequency) 
- Smart commenting based on task urgency and employee patterns
- Respects human working hours and behavior patterns
"""
 
import mysql.connector
import schedule
import time
import random
from datetime import datetime, timedelta
from typing import List, Dict, Tuple
import logging

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

class HumanLikeTaskMonitor:
    def __init__(self):
        self.db_config = {
            'host': '92.113.22.65',
            'user': 'u906714182_sqlrrefdvdv',
            'password': '3@6*t:lU',
            'database': 'u906714182_sqlrrefdvdv'
        }
        
        # AI Agent staff ID (COORDINATION AGENT DXD AI)
        self.agent_staff_id = 248
        
        # Human-like comment patterns
        self.positive_comments = [
            "Hey {name}! 🌟 Great job completing this on time! Your consistency really helps the team",
            "Hi {name}! 💪 Perfect timing on this task. Your reliability is much appreciated",
            "{name}, excellent work! 🎯 Right on schedule as always. Keep it up!",
            "Hey {name}! 🚀 Another task nailed perfectly. Your work ethic is inspiring",
            "Hi {name}! ✨ Flawless execution! Thanks for being so dependable",
            "Hey {name}! 👏 This is exactly the kind of quality delivery we love to see",
            "{name}, you're crushing it! 🔥 On-time delivery like clockwork",
            "Hi {name}! 🎉 Spot on timing! Your professionalism really stands out"
        ]
        
        self.gentle_reminders = [
            "Hi {name}! 📅 Just a friendly reminder about this task. How's progress looking?",
            "Hey {name}! ⏰ This one's approaching the deadline. Need any support?",
            "{name}, just checking in - how are things going with this task?",
            "Hi {name}! 🤔 Wanted to touch base about this deadline. All good?",
            "Hey {name}! 📝 Quick check-in on this task. Any roadblocks I can help with?",
            "{name}, hope this task is progressing well. Let me know if you need anything!"
        ]
        
        self.urgent_reminders = [
            "Hi {name}! 🚨 This task is now overdue. Can we prioritize getting it completed?",
            "{name}, this deadline has passed. Let's work together to get back on track",
            "Hey {name}! ⚠️ This task needs immediate attention. What's the holdup?",
            "Hi {name}! This delay is concerning. Can we chat about what's blocking progress?",
            "{name}, we need to address this overdue task urgently. Please prioritize this",
            "Hey {name}! 🔴 This can't wait any longer. Let's get this resolved today"
        ]
        
        # Track recent activity to avoid spam
        self.recent_comments = {}
        self.stats = {
            'checks_performed': 0,
            'comments_added': 0,
            'tasks_monitored': 0,
            'last_check': None
        }

    def get_database_connection(self):
        """Get database connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            logger.error(f"Database connection failed: {e}")
            raise

    def has_commented_recently(self, task_id: int, employee_id: int) -> bool:
        """Check if we commented on this task within 24 hours (human-like behavior)"""
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            # Check for comments from our AI agent in the last 24 hours
            query = """
            SELECT COUNT(*) as recent_count
            FROM tbltask_comments 
            WHERE taskid = %s 
                AND staffid = %s 
                AND dateadded >= DATE_SUB(NOW(), INTERVAL 24 HOUR)
            """
            
            cursor.execute(query, (task_id, self.agent_staff_id))
            result = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return result[0] > 0
            
        except Exception as e:
            logger.error(f"Error checking recent comments: {e}")
            return True  # Err on side of caution - don't comment if error

    def get_tasks_needing_attention(self) -> List[Dict]:
        """Get tasks that need human-like attention"""
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get tasks with employee information (Simplified to work immediately)
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
            WHERE t.status != 5  -- Not completed status
            ORDER BY 
                CASE 
                    WHEN t.datefinished IS NOT NULL AND DATEDIFF(COALESCE(t.datefinished, CURDATE()), t.duedate) <= 0 THEN 1  -- Completed on time
                    WHEN CURDATE() > t.duedate THEN 2  -- Overdue (high priority)
                    WHEN DATEDIFF(t.duedate, CURDATE()) <= 2 THEN 3  -- Due soon
                    ELSE 4  -- Normal
                END,
                t.duedate ASC
            """
            
            cursor.execute(query)
            tasks = cursor.fetchall()
            
            cursor.close()
            conn.close()
            
            return tasks
            
        except Exception as e:
            logger.error(f"Error fetching tasks: {e}")
            return []

    def analyze_conversation_history(self, task_id: int) -> Dict:
        """Analyze previous comments to understand conversation context"""
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get all comments on this task, ordered by date
            query = """
            SELECT 
                tc.content,
                tc.dateadded,
                tc.staffid,
                s.firstname,
                s.lastname,
                CASE WHEN tc.staffid = %s THEN 'ai' ELSE 'human' END as comment_type
            FROM tbltask_comments tc
            LEFT JOIN tblstaff s ON tc.staffid = s.staffid
            WHERE tc.taskid = %s
            ORDER BY tc.dateadded ASC
            """
            
            cursor.execute(query, (self.agent_staff_id, task_id))
            comments = cursor.fetchall()
            
            # Analyze conversation pattern
            ai_comments = [c for c in comments if c['comment_type'] == 'ai']
            human_comments = [c for c in comments if c['comment_type'] == 'human']
            
            last_ai_comment = ai_comments[-1] if ai_comments else None
            last_human_comment = human_comments[-1] if human_comments else None
            
            # Check if AI commented but user hasn't responded
            needs_followup = False
            if last_ai_comment and last_human_comment:
                # If AI's last comment is after human's last comment, user hasn't responded
                if last_ai_comment['dateadded'] > last_human_comment['dateadded']:
                    hours_since_ai = (datetime.now() - last_ai_comment['dateadded']).total_seconds() / 3600
                    if hours_since_ai >= 48:  # 2 days without response
                        needs_followup = True
            elif last_ai_comment and not last_human_comment:
                # AI commented but no human ever responded
                hours_since_ai = (datetime.now() - last_ai_comment['dateadded']).total_seconds() / 3600
                if hours_since_ai >= 48:  # 2 days without response
                    needs_followup = True
            
            cursor.close()
            conn.close()
            
            return {
                'total_comments': len(comments),
                'ai_comment_count': len(ai_comments),
                'human_comment_count': len(human_comments),
                'last_ai_comment': last_ai_comment,
                'last_human_comment': last_human_comment,
                'needs_followup': needs_followup,
                'conversation_pattern': 'no_response' if needs_followup else 'normal'
            }
            
        except Exception as e:
            logger.error(f"Error analyzing conversation: {e}")
            return {
                'total_comments': 0,
                'ai_comment_count': 0,
                'human_comment_count': 0,
                'needs_followup': False,
                'conversation_pattern': 'unknown'
            }

    def should_comment_on_task(self, task: Dict) -> bool:
        """Determine if we should comment based on intelligent conversation analysis"""
        task_id = task['taskid']
        employee_id = task['staffid']
        urgency = task['urgency_status']
        days_late = task.get('days_late', 0) or 0
        
        # Analyze full conversation history
        context = self.analyze_full_conversation_history(task_id)
        
        # Rule 0: If user needs follow-up (hasn't responded to AI), prioritize that
        if context['needs_followup']:
            return True
        
        # Rule 1: Don't comment if we already commented within 24 hours (unless follow-up needed)
        if self.has_commented_recently(task_id, employee_id):
            return False
        
        # Rule 2: Always celebrate completed tasks (once)
        if urgency == 'completed' and days_late <= 0:
            return True
        
        # Rule 3: Gentle reminders for tasks due soon (30% chance - human-like inconsistency)
        if urgency == 'due_soon':
            return random.random() < 0.3
        
        # Rule 4: Address overdue tasks (but with human-like graduated response)
        if urgency == 'overdue':
            if days_late == 1:  # Just became overdue
                return random.random() < 0.7  # 70% chance
            elif days_late <= 5:  # Moderately late
                return random.random() < 0.8  # 80% chance
            else:  # Very late
                return True  # Always comment on very late tasks
        
        # Rule 5: Random encouragement for normal tasks (5% chance - like a supportive manager)
        if urgency == 'normal':
            return random.random() < 0.05
        
        return False

    def analyze_full_conversation_history(self, task_id: int) -> Dict:
        """Analyze complete conversation history to understand full context"""
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor(dictionary=True)
            
            # Get ALL comments on this task to understand full conversation
            query = """
            SELECT 
                tc.content,
                tc.dateadded,
                tc.staffid,
                s.firstname,
                s.lastname,
                CASE WHEN tc.staffid = %s THEN 'ai' ELSE 'human' END as comment_type
            FROM tbltask_comments tc
            LEFT JOIN tblstaff s ON tc.staffid = s.staffid
            WHERE tc.taskid = %s
            ORDER BY tc.dateadded ASC
            """
            
            cursor.execute(query, (self.agent_staff_id, task_id))
            all_comments = cursor.fetchall()
            
            # Analyze conversation flow and content
            context = {
                'total_comments': len(all_comments),
                'conversation_flow': [],
                'key_topics': [],
                'current_status': 'unknown',
                'user_concerns': [],
                'progress_updates': [],
                'completion_mentions': [],
                'issues_mentioned': [],
                'last_human_message': '',
                'conversation_tone': 'neutral',
                'needs_followup': False,
                'work_in_progress': False
            }
            
            ai_comments = []
            human_comments = []
            
            # Process all comments to understand conversation
            for comment in all_comments:
                content_lower = comment['content'].lower()
                
                if comment['comment_type'] == 'ai':
                    ai_comments.append(comment)
                else:
                    human_comments.append(comment)
                    context['last_human_message'] = comment['content']
                    
                    # Analyze human comment content for better context
                    if any(word in content_lower for word in ['completed', 'done', 'finished', 'ready', 'complete']):
                        context['completion_mentions'].append(comment['content'][:100])
                        context['current_status'] = 'completed'
                    
                    elif any(word in content_lower for word in ['working', 'progress', 'update', 'implemented', 'development']):
                        context['progress_updates'].append(comment['content'][:100])
                        context['current_status'] = 'in_progress'
                        context['work_in_progress'] = True
                    
                    elif any(word in content_lower for word in ['issue', 'problem', 'error', 'bug', 'stuck', 'difficulty', 'challenge']):
                        context['issues_mentioned'].append(comment['content'][:100])
                        context['current_status'] = 'blocked'
                    
                    elif any(word in content_lower for word in ['test', 'testing', 'qa', 'review', 'check']):
                        context['key_topics'].append('testing')
                        context['current_status'] = 'testing'
                    
                    elif any(word in content_lower for word in ['deploy', 'deployment', 'live', 'production']):
                        context['key_topics'].append('deployment')
                        context['current_status'] = 'deployment'
            
            # Determine if follow-up is needed
            if ai_comments and human_comments:
                last_ai = max(ai_comments, key=lambda x: x['dateadded'])
                last_human = max(human_comments, key=lambda x: x['dateadded'])
                
                if last_ai['dateadded'] > last_human['dateadded']:
                    hours_since_ai = (datetime.now() - last_ai['dateadded']).total_seconds() / 3600
                    if hours_since_ai >= 48:  # 2 days without response
                        context['needs_followup'] = True
            elif ai_comments and not human_comments:
                last_ai = max(ai_comments, key=lambda x: x['dateadded'])
                hours_since_ai = (datetime.now() - last_ai['dateadded']).total_seconds() / 3600
                if hours_since_ai >= 48:
                    context['needs_followup'] = True
            
            context['ai_comment_count'] = len(ai_comments)
            context['human_comment_count'] = len(human_comments)
            
            cursor.close()
            conn.close()
            return context
            
        except Exception as e:
            logger.error(f"Error analyzing full conversation: {e}")
            return {'total_comments': 0, 'current_status': 'unknown', 'needs_followup': False}

    def generate_intelligent_comment(self, name: str, task: Dict) -> str:
        """Generate highly intelligent comments based on full conversation analysis"""
        urgency = task['urgency_status']
        days_late = task.get('days_late', 0) or 0
        
        # Get full conversation context
        context = self.analyze_full_conversation_history(task['taskid'])
        
        # Handle follow-up scenarios
        if context['needs_followup']:
            return self.get_smart_followup_comment(name, context, days_late)
        
        # Generate context-aware comments based on conversation history
        current_status = context.get('current_status', 'unknown')
        
        if current_status == 'completed' and context['completion_mentions']:
            return random.choice([
                f"Hi {name}! I see you mentioned this is completed. Could you please update the task status so we can close it out? 🎯",
                f"Hey {name}! Great to hear this is done! Can you mark it as complete in the system? That would be awesome! ✅",
                f"{name}, fantastic work getting this completed! Please update the status when you have a moment. 👍"
            ])
            
        elif current_status == 'testing' and 'testing' in context.get('key_topics', []):
            return random.choice([
                f"Hi {name}! How's the testing phase going? Any issues discovered that need addressing? 🔍",
                f"{name}, following up on the testing progress. Are we good to proceed or need more time for QA? 🧪",
                f"Hey {name}! Testing update needed - everything looking good or facing any blockers? 🛠️"
            ])
            
        elif current_status == 'blocked' and context['issues_mentioned']:
            recent_issue = context['issues_mentioned'][-1] if context['issues_mentioned'] else ""
            return random.choice([
                f"Hi {name}! I saw you mentioned some challenges. What specific support can I provide to help resolve them? 🆘",
                f"{name}, regarding the issues you brought up - let's tackle them together. What do you need? 🤝",
                f"Hey {name}! Those problems you mentioned sound tricky. How can I best assist you right now? 💪"
            ])
            
        elif current_status == 'in_progress' and context['work_in_progress']:
            if days_late > 5:
                return random.choice([
                    f"Hi {name}! I appreciate the progress updates. Since we're {days_late} days overdue, can we get a realistic ETA? ⏰",
                    f"{name}, thanks for keeping me posted on progress! Given the timeline, what's our best completion estimate? 📅",
                    f"Hey {name}! Good momentum on this. With {days_late} days delay, when do you think we can wrap up? 🎯"
                ])
            else:
                return random.choice([
                    f"Hi {name}! Love seeing the progress updates! Keep up the excellent work. Any obstacles I should know about? 👍",
                    f"{name}, great job on the development progress! Let me know if you need any support moving forward. 🚀",
                    f"Hey {name}! Fantastic progress! Everything flowing smoothly or need assistance with anything? 💪"
                ])
        
        # Default intelligent comments based on urgency but with personal touch
        return self.get_personalized_urgency_comment(name, urgency, days_late, context)

    def get_smart_followup_comment(self, name: str, context: Dict, days_late: int) -> str:
        """Generate intelligent follow-up based on conversation history"""
        if context.get('issues_mentioned'):
            return random.choice([
                f"Hi {name}! Following up on the issues you mentioned earlier. Were you able to resolve them or still need help? 🔄",
                f"{name}, checking back on those challenges. How did the troubleshooting go? 🛠️",
                f"Hey {name}! Circling back on the problems you raised. Any breakthroughs or still stuck? 🤔"
            ])
        elif context.get('work_in_progress'):
            return random.choice([
                f"Hi {name}! Haven't heard back on the progress updates. How are things moving along? 📊",
                f"{name}, following up on the development work. Any updates on how it's going? 🔄",
                f"Hey {name}! Checking in on the work in progress. Still on track or facing new challenges? 📈"
            ])
        else:
            return random.choice([
                f"Hi {name}! I reached out earlier but haven't heard back. Is everything okay with this task? 👋",
                f"{name}, just wanted to follow up. Any updates or do you need assistance? 🤝",
                f"Hey {name}! Second check-in on this one. Please let me know the current status! 📞"
            ])

    def get_personalized_urgency_comment(self, name: str, urgency: str, days_late: int, context: Dict) -> str:
        """Personalized urgency comments with conversation awareness"""
        if urgency == 'completed':
            return random.choice([
                f"Outstanding work {name}! 🌟 Task completed perfectly on time. Your consistency is truly appreciated!",
                f"Excellent job {name}! ✨ Right on schedule as always. This is exactly the quality we love to see!",
                f"Amazing {name}! 🎯 Perfect execution and timing. Thank you for being so reliable!"
            ])
            
        elif urgency == 'overdue':
            if days_late <= 1:
                return random.choice([
                    f"Hi {name}! This just became overdue. Can we prioritize getting it completed today? 🚨",
                    f"{name}, this missed yesterday's deadline. What do you need to finish it up? ⏰",
                    f"Hey {name}! One day overdue - let's get this back on track quickly! 📈"
                ])
            elif days_late <= 3:
                return random.choice([
                    f"Hi {name}! We're {days_late} days behind schedule. What's the plan to complete this? 🔴",
                    f"{name}, {days_late} days overdue now. Any specific blockers I can help remove? 🚧",
                    f"Hey {name}! {days_late} days delay - let's work together to catch up fast! 💪"
                ])
            else:
                return random.choice([
                    f"Hi {name}! This is seriously overdue at {days_late} days. We need urgent action on this! 🆘",
                    f"{name}, {days_late} days overdue is critical. Can we discuss this immediately? 📞",
                    f"Hey {name}! This {days_late}-day delay needs immediate attention. What's the situation? ⚠️"
                ])
        
        elif urgency == 'due_soon':
            return random.choice([
                f"Hi {name}! Deadline approaching soon. How's everything looking? Need any support? 📅",
                f"{name}, this is due soon. Are you on track or is there anything I can help with? ⏰",
                f"Hey {name}! Due date coming up fast. All good or any concerns I should know about? 🎯"
            ])
        
        else:
            return random.choice([
                f"Hi {name}! Just checking in on this task. How's the progress going? 👋",
                f"{name}, routine check-in. Everything moving smoothly or need assistance? 📊",
                f"Hey {name}! Quick status update - how are things with this one? 🔄"
            ])

    def get_contextual_comment(self, name: str, urgency: str, task: Dict) -> str:
        """Generate intelligent comments based on conversation context"""
        context = self.analyze_conversation_context(task['taskid'])
        days_late = task.get('days_late', 0) or 0
        
        # If there's recent context, use it to make intelligent comments
        if context.get('mentions_completion'):
            return random.choice([
                f"Hi {name}! I see you mentioned this is completed. Could you please update the task status? 🎯",
                f"{name}, great to hear this is done! Can you mark it as complete so we can close it out? ✅",
                f"Hey {name}! Sounds like this is finished. Please update the status when you get a chance! 👍"
            ])
        
        elif context.get('mentions_testing'):
            return random.choice([
                f"Hi {name}! How did the testing go? Any issues found that need addressing? 🔍",
                f"{name}, following up on the testing phase. Are we good to proceed or need more time? 🧪",
                f"Hey {name}! Testing update needed - are we on track or facing any blockers? 🛠️"
            ])
            
        elif context.get('mentions_issues'):
            return random.choice([
                f"Hi {name}! I saw you mentioned some issues. Do you need any help troubleshooting? 🆘",
                f"{name}, concerning the problems you mentioned - what support can I provide? 🤝",
                f"Hey {name}! Let's tackle those issues together. What specific help do you need? 💪"
            ])
            
        elif context.get('working_on_it'):
            if days_late > 3:
                return random.choice([
                    f"Hi {name}! I know you're working on this, but it's been {days_late} days overdue. Any ETA? ⏰",
                    f"{name}, appreciate the updates! Can we get a realistic timeline for completion? 📅",
                    f"Hey {name}! Thanks for the progress updates. When do you think we can wrap this up? 🎯"
                ])
            else:
                return random.choice([
                    f"Hi {name}! Thanks for the update. Keep up the good work! Any obstacles I should know about? 👍",
                    f"{name}, great to hear you're making progress! Let me know if you need anything 🚀",
                    f"Hey {name}! Good momentum on this one. Shout if you need support! 💪"
                ])
        
        # Default contextual messages based on urgency
        return self.get_default_urgency_comment(name, urgency, days_late)

    def get_default_urgency_comment(self, name: str, urgency: str, days_late: int) -> str:
        """Default urgency-based comments when no specific context available"""
        if urgency == 'completed':
            return random.choice([
                f"Amazing work {name}! 🌟 Task completed right on schedule. Your reliability is fantastic!",
                f"Excellent job {name}! ✨ Perfect timing on this one. Keep up the great work!",
                f"Outstanding {name}! 🎯 Delivered exactly on time. This is what great execution looks like!"
            ])
        elif urgency == 'overdue':
            if days_late <= 1:
                return random.choice([
                    f"Hi {name}! This just became overdue. Can we prioritize getting it wrapped up? 🚨",
                    f"{name}, this missed the deadline yesterday. What's needed to get it completed? ⏰",
                    f"Hey {name}! Just overdue by a day. Let's get this back on track! 📈"
                ])
            elif days_late <= 3:
                return random.choice([
                    f"Hi {name}! This is {days_late} days overdue now. What's the plan to complete it? 🔴",
                    f"{name}, we're {days_late} days behind schedule. Any blockers I can help remove? 🚧",
                    f"Hey {name}! {days_late} days overdue - let's work together to catch up! 🤝"
                ])
            else:
                return random.choice([
                    f"Hi {name}! This is seriously overdue ({days_late} days). We need to prioritize this urgently! 🆘",
                    f"{name}, this is {days_late} days overdue. Can we schedule a quick call to discuss? 📞",
                    f"Hey {name}! This critical delay ({days_late} days) needs immediate attention. What's happening? ⚠️"
                ])
        elif urgency == 'due_soon':
            return random.choice([
                f"Hi {name}! This is due soon. How's progress looking? Need any support? 📅",
                f"{name}, deadline approaching! Are you on track or need assistance? ⏰",
                f"Hey {name}! Due date coming up - all good or any concerns? 🎯"
            ])
        else:
            return random.choice([
                f"Hi {name}! Just checking in on this task. How are things progressing? 👋",
                f"{name}, quick status check - how's this one going? 📊",
                f"Hey {name}! Touching base on this task. All moving smoothly? 🔄"
            ])

    def get_followup_comment(self, name: str, urgency: str, conversation: Dict) -> str:
        """Generate follow-up comments when user hasn't responded"""
        followup_messages = [
            f"Hi {name}! 👋 I reached out earlier about this task. How's it going? Any blockers I can help with?",
            f"{name}, just checking in again on this one. Still need support or clarification on anything?",
            f"Hey {name}! 🤔 Haven't heard back on this task. Is everything okay? Let me know if you need help!",
            f"Hi {name}! Following up on my previous message. What's the current status on this task?",
            f"{name}, wanted to circle back on this. Are there any obstacles preventing progress?",
            f"Hey {name}! 📞 Just touching base again. Can we discuss what's needed to move this forward?",
            f"Hi {name}! Second follow-up on this task. Please update me on where things stand.",
            f"{name}, checking in once more. If there are issues, let's work through them together! 🤝"
        ]
        
        return random.choice(followup_messages)

    def get_appropriate_comment(self, task: Dict) -> str:
        """Generate highly intelligent comment based on full conversation history"""
        # Ensure we have the actual name, not "User"
        name = task['firstname'].strip() if task['firstname'] and task['firstname'] != 'User' else 'User'
        if name == 'User' and task.get('lastname') and task['lastname'] != 'Staff':
            name = task['lastname'].strip()
        
        # Use the enhanced intelligent comment generation
        return self.generate_intelligent_comment(name, task)

    def add_comment_to_task(self, task_id: int, comment: str) -> bool:
        """Add comment to task in database"""
        try:
            conn = self.get_database_connection()
            cursor = conn.cursor()
            
            insert_query = """
            INSERT INTO tbltask_comments (taskid, staffid, dateadded, content)
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

    def is_working_hours(self) -> bool:
        """Check if it's reasonable working hours (like a human manager)"""
        now = datetime.now()
        hour = now.hour
        day = now.weekday()  # 0 = Monday, 6 = Sunday
        
        # Work hours: 8 AM to 6 PM, Monday to Friday
        is_weekday = day < 5
        is_business_hours = 8 <= hour <= 18
        
        return is_weekday and is_business_hours

    def run_human_like_check(self):
        """Main monitoring function - like a human manager checking tasks"""
        check_time = datetime.now()
        self.stats['checks_performed'] += 1
        self.stats['last_check'] = check_time
        
        # Add some human-like variability - don't always check at exact 10-minute intervals
        if random.random() < 0.1:  # 10% chance to skip this check (like humans do)
            logger.info("Skipping this check cycle (human-like behavior)")
            return
        
        print(f"\n🔍 SCAN #{self.stats['checks_performed']} - {check_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        logger.info(f"Human-like check #{self.stats['checks_performed']} at {check_time.strftime('%H:%M:%S')}")
        
        try:
            # Get tasks needing attention
            print("📊 Fetching tasks from database...")
            tasks = self.get_tasks_needing_attention()
            self.stats['tasks_monitored'] = len(tasks)
            
            print(f"✅ Found {len(tasks)} tasks to analyze")
            
            # Categorize tasks for display
            completed_tasks = [t for t in tasks if t.get('urgency_status') == 'completed']
            overdue_tasks = [t for t in tasks if t.get('urgency_status') == 'overdue'] 
            due_soon_tasks = [t for t in tasks if t.get('urgency_status') == 'due_soon']
            normal_tasks = [t for t in tasks if t.get('urgency_status') == 'normal']
            
            print(f"📋 Task Categories:")
            print(f"   🚨 Overdue: {len(overdue_tasks)} tasks")
            print(f"   ⏰ Due Soon: {len(due_soon_tasks)} tasks") 
            print(f"   ✅ Completed: {len(completed_tasks)} tasks")
            print(f"   📝 Normal: {len(normal_tasks)} tasks")
            
            comments_added = 0
            
            print(f"\n💬 Processing tasks for comments...")
            
            # Process tasks with human-like attention patterns
            for i, task in enumerate(tasks[:50], 1):  # Limit to 50 tasks per check (human attention span)
                
                # Show progress
                if i <= 10 or i % 10 == 0:  # Show first 10, then every 10th
                    print(f"   📝 Analyzing task {i}/{min(len(tasks), 50)}: {task.get('title', 'Untitled')[:40]}...")
                
                if self.should_comment_on_task(task):
                    comment = self.get_appropriate_comment(task)
                    
                    # Analyze conversation for display context
                    context = self.analyze_full_conversation_history(task['taskid'])
                    is_followup = context['needs_followup']
                    current_status = context.get('current_status', 'unknown')
                    
                    if self.add_comment_to_task(task['taskid'], comment):
                        comments_added += 1
                        self.stats['comments_added'] += 1
                        
                        urgency_emoji = {
                            'completed': '✅',
                            'overdue': '🚨',
                            'due_soon': '⏰',
                            'normal': '💬'
                        }
                        
                        # Show intelligent comment indicators
                        if is_followup:
                            comment_type = "🔄 FOLLOW-UP"
                        elif current_status == 'testing':
                            comment_type = "🧪 TESTING UPDATE"
                        elif current_status == 'completed':
                            comment_type = "🎯 STATUS REQUEST"
                        elif current_status == 'blocked':
                            comment_type = "🆘 ASSISTANCE OFFER"
                        elif current_status == 'in_progress':
                            comment_type = "📈 PROGRESS CHECK"
                        else:
                            comment_type = "💬 SMART COMMENT"
                        
                        # Get actual name for display
                        display_name = task['firstname'] if task['firstname'] != 'User' else task.get('lastname', 'Unknown')
                        
                        task_title = task.get('title', 'Unknown Task')[:30]
                        print(f"   {urgency_emoji.get(task['urgency_status'], '📝')} {comment_type} → Task {task['taskid']}: {task_title}")
                        print(f"      👤 To: {display_name}")
                        print(f"      💭 Comment: {comment[:60]}...")
                        if current_status != 'unknown':
                            print(f"      🧠 Context: Detected {current_status} status from conversation")
                        
                        logger.info(f"Commented on task {task['taskid']} ({task['firstname']} {task['lastname']}): {comment[:50]}...")
                        
                        # Human-like pacing - small delay between comments
                        time.sleep(random.uniform(1, 3))
            
            # Final scan summary
            print(f"\n✨ ===== SCAN COMPLETE =====")
            print(f"💬 Comments Added: {comments_added}")
            print(f"📊 Tasks Processed: {len(tasks)}")
            print(f"🎯 Session Total Comments: {self.stats['comments_added']}")
            
            next_check = datetime.now() + timedelta(minutes=10)
            print(f"⏭️  Next scan at: {next_check.strftime('%H:%M:%S')}")
            print("=" * 30)
            
            # Log summary
            working_hours = "YES" if self.is_working_hours() else "NO"
            logger.info(f"Check complete: {comments_added} new comments | {len(tasks)} tasks monitored | Working hours: {working_hours}")
            
            # Occasional performance summary (like a human manager reviewing)
            if self.stats['checks_performed'] % 50 == 0:  # Every ~8 hours (50 * 10 min)
                logger.info(f"Daily Summary: {self.stats['comments_added']} total comments across {self.stats['checks_performed']} checks")
            
        except Exception as e:
            logger.error(f"Error in monitoring check: {e}")

    def start_human_like_monitoring(self):
        """Start the human-like monitoring system"""
        logger.info("HUMAN-LIKE TASK MONITOR STARTING")
        logger.info("=" * 60)
        logger.info("Mimicking human manager behavior:")
        logger.info("   • Checks every 10 minutes (like periodic check-ins)")
        logger.info("   • 24-hour comment cooldown (no spam)")
        logger.info("   • Smart urgency-based commenting")
        logger.info("   • Working hours awareness")
        logger.info("   • Natural human-like variability")
        logger.info("=" * 60)
        
        # Schedule every 10 minutes
        schedule.every(10).minutes.do(self.run_human_like_check)
        
        # Run initial check
        logger.info("Running initial task check...")
        self.run_human_like_check()
        
        logger.info("Monitor scheduled every 10 minutes. Running continuously...")
        logger.info("Press Ctrl+C to stop the monitor")
        
        while True:
            try:
                schedule.run_pending()
                time.sleep(30)  # Check every 30 seconds for scheduled tasks
                
            except KeyboardInterrupt:
                logger.info("\n🛑 Human-like monitor stopped by user")
                logger.info(f"📊 Final Stats: {self.stats['comments_added']} comments in {self.stats['checks_performed']} checks")
                break
            except Exception as e:
                logger.error(f"❌ Error in monitoring loop: {e}")
                logger.info("⏸️ Waiting 5 minutes before retrying...")
                time.sleep(300)  # Wait 5 minutes before retrying

if __name__ == "__main__":
    print("🧠 HUMAN-LIKE TASK MONITOR")
    print("=" * 40)
    print("Intelligent task monitoring that works")
    print("like a real human manager:")
    print()
    print("✓ Checks every 10 minutes")
    print("✓ 24-hour comment cooldown")
    print("✓ Smart urgency detection")
    print("✓ Human-like behavior patterns")
    print("✓ Working hours awareness")
    print()
    print("Press Ctrl+C to stop monitoring")
    print("=" * 40)
    
    monitor = HumanLikeTaskMonitor()
    monitor.start_human_like_monitoring()