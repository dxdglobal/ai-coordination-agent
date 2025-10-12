"""
🗄️ Simplified Vector Database Service (Without ChromaDB dependency)
Fallback implementation for semantic search using basic text matching
"""

import openai
import os
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import json
from datetime import datetime
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

class TaskVectorDatabase:
    """🔍 Simplified vector database for semantic task search (ChromaDB-free version)"""
    
    def __init__(self, collection_name: str = "task_embeddings"):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.collection_name = collection_name
        
        # In-memory storage for now (simplified)
        self.task_store = {}
        
        # Database connection config
        self.db_config = {
            'host': '92.113.22.65',
            'user': 'u906714182_sqlrrefdvdv',
            'password': os.getenv('DB_PASSWORD', '3@6*t:lU'),
            'database': 'u906714182_sqlrrefdvdv'
        }
        
        print("🗄️ Simplified Vector Database Service initialized (ChromaDB-free)")

    def generate_embedding(self, text: str) -> List[float]:
        """🧮 Generate OpenAI embedding for text"""
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=text
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"❌ Error generating embedding: {e}")
            return []

    def create_task_document(self, task: Dict) -> str:
        """📝 Create a comprehensive document from task data for embedding"""
        doc_parts = []
        
        # Task name and basic info
        if task.get('name'):
            doc_parts.append(f"Task: {task['name']}")
        
        # Creator information
        if task.get('firstname') and task.get('lastname'):
            doc_parts.append(f"Created by: {task['firstname']} {task['lastname']}")
        elif task.get('firstname'):
            doc_parts.append(f"Created by: {task['firstname']}")
            
        # Status and priority
        if task.get('status'):
            doc_parts.append(f"Status: {task['status']}")
        if task.get('priority'):
            doc_parts.append(f"Priority: {task['priority']}")
            
        # Dates
        if task.get('dateadded'):
            doc_parts.append(f"Created on: {task['dateadded']}")
        if task.get('duedate'):
            doc_parts.append(f"Due date: {task['duedate']}")
            
        # Description if available
        if task.get('description'):
            doc_parts.append(f"Description: {task['description']}")
            
        # Project information
        if task.get('project_name'):
            doc_parts.append(f"Project: {task['project_name']}")
            
        return " | ".join(doc_parts)

    def get_tasks_for_employee(self, employee_name: str) -> List[Dict]:
        """👤 Get all tasks for a specific employee from MySQL"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor(dictionary=True)
            
            # Enhanced query to get comprehensive task data
            sql = """
            SELECT 
                t.id,
                t.name,
                t.description,
                t.status,
                t.priority,
                t.dateadded,
                t.duedate,
                t.addedfrom,
                s.firstname,
                s.lastname,
                p.name as project_name
            FROM tbltasks t
            LEFT JOIN tblstaff s ON t.addedfrom = s.staffid
            LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
            WHERE s.firstname LIKE %s OR s.lastname LIKE %s
            ORDER BY t.dateadded DESC
            """
            
            name_pattern = f"%{employee_name}%"
            cursor.execute(sql, (name_pattern, name_pattern))
            tasks = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            print(f"📊 Retrieved {len(tasks)} tasks for employee: {employee_name}")
            return tasks
            
        except Exception as e:
            print(f"❌ Error retrieving tasks from MySQL: {e}")
            return []

    def index_employee_tasks(self, employee_name: str) -> Dict[str, Any]:
        """📚 Index all tasks for an employee (simplified version)"""
        try:
            print(f"🔄 Indexing tasks for employee: {employee_name}")
            
            # Get tasks from MySQL
            tasks = self.get_tasks_for_employee(employee_name)
            if not tasks:
                return {'success': False, 'message': f'No tasks found for {employee_name}'}
            
            # Store in memory for simplified search
            self.task_store[employee_name] = tasks
            
            print(f"✅ Successfully indexed {len(tasks)} tasks for {employee_name}")
            return {
                'success': True,
                'tasks_indexed': len(tasks),
                'employee': employee_name,
                'collection_name': self.collection_name
            }
                
        except Exception as e:
            print(f"❌ Error indexing tasks: {e}")
            return {'success': False, 'message': str(e)}

    def semantic_search(self, query: str, employee_name: str = None, top_k: int = 10) -> List[Dict]:
        """🔍 Perform simplified semantic search for relevant tasks"""
        try:
            print(f"🔍 Simplified search: '{query}' for employee: {employee_name or 'All'}")
            
            # Get tasks from storage or fetch fresh
            if employee_name and employee_name in self.task_store:
                tasks = self.task_store[employee_name]
            elif employee_name:
                tasks = self.get_tasks_for_employee(employee_name)
            else:
                # For now, return empty if no specific employee
                return []
            
            # Simple text-based search (fallback)
            query_lower = query.lower()
            search_results = []
            
            for task in tasks:
                doc_text = self.create_task_document(task)
                
                # Basic relevance scoring based on keyword matches
                relevance_score = 0
                doc_lower = doc_text.lower()
                
                # Check for direct matches
                query_words = query_lower.split()
                for word in query_words:
                    if word in doc_lower:
                        relevance_score += 1
                
                # Add task name matches (higher weight)
                if task.get('name') and query_lower in task['name'].lower():
                    relevance_score += 3
                
                if relevance_score > 0:
                    search_results.append({
                        'document': doc_text,
                        'metadata': {
                            'task_id': str(task['id']),
                            'task_name': task['name'] or '',
                            'employee_name': employee_name,
                            'creator_firstname': task.get('firstname', ''),
                            'creator_lastname': task.get('lastname', ''),
                            'status': task.get('status', ''),
                            'priority': str(task.get('priority', '')),
                            'dateadded': str(task.get('dateadded', ''))
                        },
                        'similarity_score': relevance_score / 10.0,  # Normalize
                        'task_id': str(task['id']),
                        'task_name': task['name'] or '',
                        'employee_name': employee_name,
                        'status': task.get('status', ''),
                        'priority': str(task.get('priority', '')),
                        'dateadded': str(task.get('dateadded', ''))
                    })
            
            # Sort by relevance score
            search_results.sort(key=lambda x: x['similarity_score'], reverse=True)
            
            print(f"🎯 Found {len(search_results[:top_k])} relevant tasks")
            return search_results[:top_k]
            
        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            return []

    def get_contextual_tasks(self, query: str, employee_name: str, intent: str, top_k: int = 5) -> List[Dict]:
        """🎯 Get the most relevant tasks based on query intent and context"""
        
        # Adjust search based on intent
        if intent == 'performance':
            enhanced_query = f"{query} completion progress status performance"
            top_k = min(top_k, 15)
        elif intent == 'recent_tasks':
            enhanced_query = f"{query} recent latest new today this week"
            top_k = min(top_k, 8)
        elif intent == 'task_summary':
            enhanced_query = f"{query} overview summary activities work"
            top_k = min(top_k, 12)
        else:
            enhanced_query = query
            
        return self.semantic_search(enhanced_query, employee_name, top_k)

    def get_collection_stats(self) -> Dict:
        """📊 Get statistics about the task storage"""
        try:
            total_documents = sum(len(tasks) for tasks in self.task_store.values())
            employee_counts = {emp: len(tasks) for emp, tasks in self.task_store.items()}
            
            return {
                'total_documents': total_documents,
                'employee_counts': employee_counts,
                'collection_name': self.collection_name
            }
            
        except Exception as e:
            print(f"❌ Error getting collection stats: {e}")
            return {'total_documents': 0, 'employee_counts': {}, 'error': str(e)}

    def clear_employee_embeddings(self, employee_name: str) -> bool:
        """🗑️ Clear all embeddings for a specific employee"""
        try:
            if employee_name in self.task_store:
                del self.task_store[employee_name]
                print(f"🗑️ Cleared embeddings for {employee_name}")
                return True
            else:
                print(f"ℹ️ No embeddings found for {employee_name}")
                return True
                
        except Exception as e:
            print(f"❌ Error clearing embeddings: {e}")
            return False

    # Placeholder methods for compatibility
    def update_task_embeddings(self, task_id: str, employee_name: str) -> bool:
        """🔄 Update embeddings for a specific task (simplified)"""
        return True