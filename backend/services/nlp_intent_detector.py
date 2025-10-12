"""
🧠 NLP Intent Detection Service
Advanced natural language processing for detecting user intent and extracting entities
"""

import re
import openai
import os
from typing import Dict, List, Optional, Tuple
from enum import Enum
import json

class TaskIntent(Enum):
    """Supported task-related intents"""
    LIST_TASKS = "list_tasks"
    TASK_SUMMARY = "task_summary"
    PERFORMANCE_ANALYSIS = "performance"
    TASK_DETAILS = "task_details"
    PROGRESS_REPORT = "progress_report"
    TASK_COUNT = "task_count"
    RECENT_TASKS = "recent_tasks"
    SPECIFIC_TASK = "specific_task"
    TASK_ASSIGNMENT = "task_assignment"
    OVERDUE_TASKS = "overdue_tasks"
    COMPLETED_TASKS = "completed_tasks"
    INPROGRESS_TASKS = "inprogress_tasks"
    GENERAL_QUERY = "general_query"

class NLPIntentDetector:
    """🔍 Advanced NLP service for intent detection and entity extraction"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        
        # Predefined patterns for quick detection
        self.intent_patterns = {
            TaskIntent.LIST_TASKS: [
                r'(?:show|list|give).+(?:tasks?|assignments?)',
                r'(?:all|every).+tasks?',
                r'tasks?.+(?:of|for|by)',
                r'(?:what|which).+tasks?'
            ],
            TaskIntent.TASK_SUMMARY: [
                r'summar[yi]ze?.+tasks?',
                r'overview.+(?:tasks?|work)',
                r'brief.+(?:tasks?|activities)',
                r'what.+(?:working on|doing)'
            ],
            TaskIntent.PERFORMANCE_ANALYSIS: [
                r'performance.+(?:analysis|report)',
                r'how.+(?:performing|doing)',
                r'productivity.+(?:analysis|report)',
                r'efficiency.+(?:analysis|report)'
            ],
            TaskIntent.PROGRESS_REPORT: [
                r'progress.+(?:report|update)',
                r'status.+(?:update|report)',
                r'how.+(?:going|progressing)',
                r'completion.+(?:status|rate)'
            ],
            TaskIntent.TASK_COUNT: [
                r'how many.+tasks?',
                r'count.+tasks?',
                r'number.+tasks?',
                r'total.+tasks?'
            ],
            TaskIntent.RECENT_TASKS: [
                r'recent.+tasks?',
                r'latest.+tasks?',
                r'new.+tasks?',
                r'today.+tasks?'
            ],
            TaskIntent.OVERDUE_TASKS: [
                r'overdue.+tasks?',
                r'late.+tasks?',
                r'delayed.+tasks?',
                r'past.+due.+tasks?',
                r'missed.+deadline.+tasks?',
                r'behind.+schedule.+tasks?',
                r'expired.+tasks?'
            ],
            TaskIntent.COMPLETED_TASKS: [
                r'completed.+tasks?',
                r'finished.+tasks?',
                r'done.+tasks?',
                r'completed.+work',
                r'finished.+work',
                r'accomplished.+tasks?'
            ],
            TaskIntent.INPROGRESS_TASKS: [
                r'(?:in.?progress|ongoing|current|active).+tasks?',
                r'working.+on.+tasks?',
                r'current.+work',
                r'active.+tasks?',
                r'pending.+tasks?',
                r'running.+tasks?'
            ]
        }
        
        # Common employee name patterns
        self.name_patterns = [
            r'(?:of|for|by)\s+(\w+)',
            r'(\w+)\'s?\s+(?:tasks?|work|activities)',
            r'(?:employee|person|user)\s+(\w+)',
            r'(?:show|list|give)\s+(?:me\s+)?(\w+)',
            r'(\w+)\s+(?:tasks?|assignments?|work)'
        ]
        
        print("🧠 NLP Intent Detector initialized with pattern matching and OpenAI integration")

    def detect_intent_and_entities(self, query: str) -> Dict:
        """🎯 Main method to detect intent and extract entities from user query"""
        try:
            print(f"🔍 Analyzing query: '{query}'")
            
            # First try pattern-based detection for speed
            pattern_result = self._pattern_based_detection(query)
            
            # Use AI for complex cases or validation
            ai_result = self._ai_based_detection(query)
            
            # Combine results with AI having higher priority
            final_result = self._combine_results(pattern_result, ai_result, query)
            
            print(f"🎯 Final Intent: {final_result['intent']}, Employee: {final_result.get('employee_name', 'None')}")
            return final_result
            
        except Exception as e:
            print(f"❌ Error in intent detection: {e}")
            return {
                'intent': TaskIntent.GENERAL_QUERY.value,
                'employee_name': None,
                'confidence': 0.3,
                'method': 'fallback',
                'query': query
            }

    def _pattern_based_detection(self, query: str) -> Dict:
        """⚡ Fast pattern-based intent detection"""
        query_lower = query.lower()
        detected_intent = TaskIntent.GENERAL_QUERY
        confidence = 0.5
        
        # Check each intent pattern
        for intent, patterns in self.intent_patterns.items():
            for pattern in patterns:
                if re.search(pattern, query_lower):
                    detected_intent = intent
                    confidence = 0.8
                    break
            if detected_intent != TaskIntent.GENERAL_QUERY:
                break
        
        # Extract employee name
        employee_name = self._extract_employee_name(query)
        
        return {
            'intent': detected_intent.value,
            'employee_name': employee_name,
            'confidence': confidence,
            'method': 'pattern_matching'
        }

    def _ai_based_detection(self, query: str) -> Dict:
        """🤖 AI-powered intent detection for complex queries"""
        try:
            prompt = f"""
            Analyze this user query for task management intent and employee name extraction:
            
            Query: "{query}"
            
            Available intents:
            - list_tasks: User wants to see a list of tasks
            - task_summary: User wants a summary/overview of tasks
            - performance: User wants performance analysis
            - task_details: User wants details about specific tasks
            - progress_report: User wants progress/status updates
            - task_count: User wants to count tasks
            - recent_tasks: User wants recent/latest tasks
            - overdue_tasks: User wants to see overdue/late tasks
            - completed_tasks: User wants to see completed/finished tasks
            - inprogress_tasks: User wants to see in-progress/ongoing tasks
            - specific_task: User asking about one specific task
            - task_assignment: User wants to know who assigned/created tasks
            - general_query: General or unclear intent
            
            Instructions:
            1. Identify the most likely intent
            2. Extract any employee/person name mentioned
            3. Provide confidence score (0.0-1.0)
            
            Respond with ONLY valid JSON:
            {{
                "intent": "intent_name",
                "employee_name": "name or null",
                "confidence": 0.95,
                "reasoning": "brief explanation"
            }}
            
            Examples:
            - "Show me Hamza's AI monitoring tasks" → {{"intent": "list_tasks", "employee_name": "Hamza", "confidence": 0.95}}
            - "Hamza's overdue tasks" → {{"intent": "overdue_tasks", "employee_name": "Hamza", "confidence": 0.95}}
            - "Hamza's completed tasks" → {{"intent": "completed_tasks", "employee_name": "Hamza", "confidence": 0.95}}
            - "Hamza's in-progress tasks" → {{"intent": "inprogress_tasks", "employee_name": "Hamza", "confidence": 0.95}}
            - "How is John performing this week?" → {{"intent": "performance", "employee_name": "John", "confidence": 0.9}}
            - "Summarize recent tasks" → {{"intent": "task_summary", "employee_name": null, "confidence": 0.85}}
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=200,
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content.strip())
            result['method'] = 'ai_analysis'
            return result
            
        except Exception as e:
            print(f"⚠️ AI detection failed: {e}")
            return {
                'intent': TaskIntent.GENERAL_QUERY.value,
                'employee_name': None,
                'confidence': 0.3,
                'method': 'ai_fallback'
            }

    def _extract_employee_name(self, query: str) -> Optional[str]:
        """👤 Extract employee name using multiple patterns"""
        for pattern in self.name_patterns:
            match = re.search(pattern, query, re.IGNORECASE)
            if match:
                name = match.group(1).strip().title()
                # Filter out common words that aren't names
                if name.lower() not in ['me', 'my', 'all', 'every', 'some', 'any', 'the', 'tasks', 'task']:
                    return name
        return None

    def _combine_results(self, pattern_result: Dict, ai_result: Dict, query: str) -> Dict:
        """🔄 Combine pattern and AI results intelligently"""
        
        # AI result takes precedence if confidence is high
        if ai_result.get('confidence', 0) > 0.7:
            final_result = ai_result.copy()
        else:
            final_result = pattern_result.copy()
            
        # Cross-validate employee name
        pattern_name = pattern_result.get('employee_name')
        ai_name = ai_result.get('employee_name')
        
        if pattern_name and ai_name and pattern_name.lower() == ai_name.lower():
            final_result['confidence'] = min(1.0, final_result.get('confidence', 0.5) + 0.2)
        elif pattern_name and not ai_name:
            final_result['employee_name'] = pattern_name
        elif ai_name and not pattern_name:
            final_result['employee_name'] = ai_name
            
        # Add metadata
        final_result.update({
            'query': query,
            'pattern_detected': pattern_result.get('intent'),
            'ai_detected': ai_result.get('intent'),
            'processing_methods': [pattern_result.get('method'), ai_result.get('method')]
        })
        
        return final_result

    def is_task_related_query(self, query: str) -> bool:
        """✅ Quick check if query is task-related"""
        task_keywords = [
            'task', 'tasks', 'assignment', 'assignments', 'work', 'project', 'projects',
            'activity', 'activities', 'job', 'jobs', 'todo', 'to-do', 'performance',
            'progress', 'status', 'completion', 'monitoring', 'tracking'
        ]
        
        query_lower = query.lower()
        return any(keyword in query_lower for keyword in task_keywords)

    def extract_task_filters(self, query: str) -> Dict:
        """🔍 Extract task filtering criteria from query"""
        filters = {}
        query_lower = query.lower()
        
        # Time-based filters
        if 'today' in query_lower:
            filters['time_period'] = 'today'
        elif 'this week' in query_lower or 'weekly' in query_lower:
            filters['time_period'] = 'week'
        elif 'this month' in query_lower or 'monthly' in query_lower:
            filters['time_period'] = 'month'
        elif 'recent' in query_lower or 'latest' in query_lower:
            filters['time_period'] = 'recent'
            
        # Status filters
        if 'completed' in query_lower or 'finished' in query_lower:
            filters['status'] = 'completed'
        elif 'pending' in query_lower or 'waiting' in query_lower:
            filters['status'] = 'pending'
        elif 'in progress' in query_lower or 'ongoing' in query_lower:
            filters['status'] = 'in_progress'
            
        # Priority filters
        if 'urgent' in query_lower or 'high priority' in query_lower:
            filters['priority'] = 'urgent'
        elif 'important' in query_lower:
            filters['priority'] = 'high'
            
        # Type filters
        if 'monitoring' in query_lower:
            filters['task_type'] = 'monitoring'
        elif 'ai' in query_lower or 'artificial intelligence' in query_lower:
            filters['task_type'] = 'ai'
        elif 'development' in query_lower or 'dev' in query_lower:
            filters['task_type'] = 'development'
            
        return filters