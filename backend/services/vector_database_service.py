"""
🗄️ Vector Database Service
Advanced semantic search using OpenAI embeddings and Chroma vector database
"""

import openai
import os
import numpy as np
import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional, Tuple
import hashlib
import json
from datetime import datetime
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

class TaskVectorDatabase:
    """🔍 Vector database for semantic task search using OpenAI embeddings"""
    
    def __init__(self, collection_name: str = "task_embeddings"):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.collection_name = collection_name
        
        # Initialize Chroma client
        self.chroma_client = chromadb.PersistentClient(
            path="/Users/dds/Desktop/Git-Projects/ai-coordination-agent/chroma_db"
        )
        
        # Get or create collection
        try:
            self.collection = self.chroma_client.get_collection(name=collection_name)
            print(f"📚 Using existing collection: {collection_name}")
        except:
            self.collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={"description": "Task embeddings for semantic search"}
            )
            print(f"🆕 Created new collection: {collection_name}")
        
        # Database connection config
        self.db_config = {
            'host': '92.113.22.65',
            'user': 'u906714182_sqlrrefdvdv',
            'password': os.getenv('DB_PASSWORD', '3@6*t:lU'),
            'database': 'u906714182_sqlrrefdvdv'
        }
        
        print("🗄️ Vector Database Service initialized with Chroma and OpenAI embeddings")

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
        """📚 Index all tasks for an employee in vector database"""
        try:
            print(f"🔄 Indexing tasks for employee: {employee_name}")
            
            # Get tasks from MySQL
            tasks = self.get_tasks_for_employee(employee_name)
            if not tasks:
                return {'success': False, 'message': f'No tasks found for {employee_name}'}
            
            # Prepare data for vector storage
            documents = []
            embeddings = []
            metadatas = []
            ids = []
            
            for task in tasks:
                # Create document text for embedding
                doc_text = self.create_task_document(task)
                documents.append(doc_text)
                
                # Generate embedding
                embedding = self.generate_embedding(doc_text)
                if embedding:
                    embeddings.append(embedding)
                    
                    # Create metadata
                    metadata = {
                        'task_id': str(task['id']),
                        'task_name': task['name'] or '',
                        'employee_name': employee_name,
                        'creator_firstname': task.get('firstname', ''),
                        'creator_lastname': task.get('lastname', ''),
                        'status': task.get('status', ''),
                        'priority': str(task.get('priority', '')),
                        'dateadded': str(task.get('dateadded', '')),
                        'project_name': task.get('project_name', ''),
                        'indexed_at': str(datetime.now())
                    }
                    metadatas.append(metadata)
                    
                    # Create unique ID
                    task_id = f"{employee_name}_{task['id']}_{hashlib.md5(doc_text.encode()).hexdigest()[:8]}"
                    ids.append(task_id)
            
            # Add to vector database
            if embeddings:
                self.collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids
                )
                
                print(f"✅ Successfully indexed {len(embeddings)} tasks for {employee_name}")
                return {
                    'success': True,
                    'tasks_indexed': len(embeddings),
                    'employee': employee_name,
                    'collection_name': self.collection_name
                }
            else:
                return {'success': False, 'message': 'Failed to generate embeddings'}
                
        except Exception as e:
            print(f"❌ Error indexing tasks: {e}")
            return {'success': False, 'message': str(e)}

    def semantic_search(self, query: str, employee_name: str = None, top_k: int = 10) -> List[Dict]:
        """🔍 Perform semantic search for relevant tasks"""
        try:
            print(f"🔍 Semantic search: '{query}' for employee: {employee_name or 'All'}")
            
            # Generate query embedding
            query_embedding = self.generate_embedding(query)
            if not query_embedding:
                return []
            
            # Prepare search filters
            where_filter = {}
            if employee_name:
                where_filter["employee_name"] = employee_name
            
            # Search in vector database
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where_filter if where_filter else None,
                include=['documents', 'metadatas', 'distances']
            )
            
            # Format results
            search_results = []
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                    distance = results['distances'][0][i] if results['distances'] else 1.0
                    
                    search_results.append({
                        'document': doc,
                        'metadata': metadata,
                        'similarity_score': 1 - distance,  # Convert distance to similarity
                        'task_id': metadata.get('task_id', ''),
                        'task_name': metadata.get('task_name', ''),
                        'employee_name': metadata.get('employee_name', ''),
                        'status': metadata.get('status', ''),
                        'priority': metadata.get('priority', ''),
                        'dateadded': metadata.get('dateadded', '')
                    })
            
            print(f"🎯 Found {len(search_results)} relevant tasks")
            return search_results
            
        except Exception as e:
            print(f"❌ Error in semantic search: {e}")
            return []

    def get_contextual_tasks(self, query: str, employee_name: str, intent: str, top_k: int = 5) -> List[Dict]:
        """🎯 Get the most relevant tasks based on query intent and context"""
        
        # Adjust search based on intent
        if intent == 'performance':
            # For performance queries, look for completed/in-progress tasks
            enhanced_query = f"{query} completion progress status performance"
            top_k = min(top_k, 15)  # More tasks for performance analysis
        elif intent == 'recent_tasks':
            # For recent tasks, focus on time-related context
            enhanced_query = f"{query} recent latest new today this week"
            top_k = min(top_k, 8)
        elif intent == 'task_summary':
            # For summaries, get broader context
            enhanced_query = f"{query} overview summary activities work"
            top_k = min(top_k, 12)
        else:
            enhanced_query = query
            
        return self.semantic_search(enhanced_query, employee_name, top_k)

    def update_task_embeddings(self, task_id: str, employee_name: str) -> bool:
        """🔄 Update embeddings for a specific task"""
        try:
            # Get updated task data
            tasks = self.get_tasks_for_employee(employee_name)
            target_task = next((t for t in tasks if str(t['id']) == str(task_id)), None)
            
            if not target_task:
                return False
            
            # Remove old embedding
            try:
                old_ids = [id for id in self.collection.get()['ids'] if id.startswith(f"{employee_name}_{task_id}_")]
                if old_ids:
                    self.collection.delete(ids=old_ids)
            except:
                pass
            
            # Add new embedding
            doc_text = self.create_task_document(target_task)
            embedding = self.generate_embedding(doc_text)
            
            if embedding:
                metadata = {
                    'task_id': str(target_task['id']),
                    'task_name': target_task['name'] or '',
                    'employee_name': employee_name,
                    'status': target_task.get('status', ''),
                    'updated_at': str(datetime.now())
                }
                
                new_id = f"{employee_name}_{task_id}_{hashlib.md5(doc_text.encode()).hexdigest()[:8]}"
                
                self.collection.add(
                    documents=[doc_text],
                    embeddings=[embedding],
                    metadatas=[metadata],
                    ids=[new_id]
                )
                
                print(f"✅ Updated embeddings for task {task_id}")
                return True
                
        except Exception as e:
            print(f"❌ Error updating task embeddings: {e}")
            
        return False

    def get_collection_stats(self) -> Dict:
        """📊 Get statistics about the vector database collection"""
        try:
            collection_data = self.collection.get()
            total_documents = len(collection_data['ids']) if collection_data['ids'] else 0
            
            # Count by employee
            employee_counts = {}
            if collection_data['metadatas']:
                for metadata in collection_data['metadatas']:
                    emp_name = metadata.get('employee_name', 'Unknown')
                    employee_counts[emp_name] = employee_counts.get(emp_name, 0) + 1
            
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
            # Get all IDs for this employee
            collection_data = self.collection.get()
            employee_ids = []
            
            if collection_data['ids'] and collection_data['metadatas']:
                for i, metadata in enumerate(collection_data['metadatas']):
                    if metadata.get('employee_name') == employee_name:
                        employee_ids.append(collection_data['ids'][i])
            
            if employee_ids:
                self.collection.delete(ids=employee_ids)
                print(f"🗑️ Cleared {len(employee_ids)} embeddings for {employee_name}")
                return True
            else:
                print(f"ℹ️ No embeddings found for {employee_name}")
                return True
                
        except Exception as e:
            print(f"❌ Error clearing embeddings: {e}")
            return False