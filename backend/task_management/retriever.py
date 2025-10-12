"""
Retriever Layer - MySQL queries and vector embeddings for RAG
Handles data retrieval and vector database operations
"""

import json
import time
import numpy as np
from typing import List, Dict, Optional, Any, Tuple
import openai
from .config import Config
from .crm_connector import get_crm_connector
from .logger import get_logger

# Initialize components
logger = get_logger()
crm = get_crm_connector()

# Try to import vector database libraries
try:
    import chromadb
    CHROMA_AVAILABLE = True
    logger.info("ChromaDB available")
except ImportError:
    CHROMA_AVAILABLE = False
    logger.warning("ChromaDB not available")

try:
    import faiss
    FAISS_AVAILABLE = True
    logger.info("FAISS available")
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available")

class TaskRetriever:
    """Retrieves tasks and manages vector embeddings for RAG"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=Config.OPENAI_API_KEY)
        self.vector_db = None
        self.embeddings_cache = {}
        self._initialize_vector_db()
    
    def _initialize_vector_db(self):
        """Initialize vector database based on configuration"""
        if Config.VECTOR_DB_TYPE == 'chroma' and CHROMA_AVAILABLE:
            self._init_chroma()
        elif Config.VECTOR_DB_TYPE == 'faiss' and FAISS_AVAILABLE:
            self._init_faiss()
        else:
            logger.warning("No vector database available, using basic text matching")
    
    def _init_chroma(self):
        """Initialize ChromaDB"""
        try:
            import os
            os.makedirs(Config.CHROMA_PERSIST_DIR, exist_ok=True)
            
            client = chromadb.PersistentClient(path=Config.CHROMA_PERSIST_DIR)
            self.vector_db = client.get_or_create_collection(
                name="task_embeddings",
                metadata={"hnsw:space": "cosine"}
            )
            logger.info("ChromaDB initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize ChromaDB", error=e)
            self.vector_db = None
    
    def _init_faiss(self):
        """Initialize FAISS"""
        try:
            import os
            os.makedirs(os.path.dirname(Config.FAISS_INDEX_PATH), exist_ok=True)
            
            # Create or load FAISS index
            if os.path.exists(Config.FAISS_INDEX_PATH):
                self.vector_db = faiss.read_index(Config.FAISS_INDEX_PATH)
            else:
                # Create new index
                self.vector_db = faiss.IndexFlatIP(Config.EMBEDDING_DIMENSION)
            
            logger.info("FAISS initialized successfully")
        except Exception as e:
            logger.error("Failed to initialize FAISS", error=e)
            self.vector_db = None
    
    def retrieve_tasks_for_employee(self, employee_id: int, intent: str, 
                                   query: str, limit: int = None, task_filters: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Retrieve tasks for employee based on intent and query
        Args:
            employee_id: Staff ID
            intent: User intent (list_tasks, task_summary, etc.)
            query: Original user query
            limit: Maximum number of tasks to return
            task_filters: Dictionary with task filters (overdue, completed, etc.)
        Returns: Dictionary with retrieved tasks and metadata
        """
        start_time = time.time()
        
        try:
            # Get basic task data from MySQL
            tasks = self._get_mysql_tasks(employee_id, intent, limit or Config.TASK_PAGINATION_SIZE, task_filters)
            
            
            if not tasks:
                return {
                    'tasks': [],
                    'total_count': 0,
                    'retrieval_method': 'mysql',
                    'processing_time': time.time() - start_time
                }
            
            # Enhance with vector similarity if available and relevant
            if self.vector_db and intent in ['task_summary', 'anomaly_check']:
                enhanced_tasks = self._enhance_with_vector_similarity(tasks, query)
                retrieval_method = 'mysql_plus_vector'
            else:
                enhanced_tasks = tasks
                retrieval_method = 'mysql'
            
            # Add metadata and format results
            result = {
                'tasks': enhanced_tasks[:limit] if limit else enhanced_tasks,
                'total_count': len(enhanced_tasks),
                'retrieval_method': retrieval_method,
                'processing_time': time.time() - start_time,
                'employee_id': employee_id,
                'intent': intent
            }
            
            logger.info(f"Retrieved {len(enhanced_tasks)} tasks for employee {employee_id}", 
                       extra_data={'intent': intent, 'method': retrieval_method})
            
            return result
            
        except Exception as e:
            logger.error("Failed to retrieve tasks", error=e, 
                        extra_data={'employee_id': employee_id, 'intent': intent})
            return {
                'tasks': [],
                'total_count': 0,
                'error': str(e),
                'processing_time': time.time() - start_time
            }
    
    def _get_mysql_tasks(self, employee_id: int, intent: str, limit: int, task_filters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Get tasks from MySQL based on intent and filters"""
        
        task_filters = task_filters or {}
        
        # Debug logging
        logger.info(f"_get_mysql_tasks: task_filters={task_filters}, intent={intent}")
        
        # Determine status filter based on intent and task filters
        status_filter = None
        if task_filters.get('completed'):
            status_filter = [5, 9]  # Completed and Approved tasks
            logger.info(f"Applied completed filter: {status_filter}")
        elif task_filters.get('active'):
            status_filter = [1, 2, 3, 4, 8]  # Active working statuses
            logger.info(f"Applied active filter: {status_filter}")
        elif task_filters.get('on_hold'):
            status_filter = [6]  # On Hold tasks
            logger.info(f"Applied on_hold filter: {status_filter}")
        elif task_filters.get('cancelled'):
            status_filter = [7, 10]  # Cancelled and Rejected
            logger.info(f"Applied cancelled filter: {status_filter}")
        elif task_filters.get('archived'):
            status_filter = [11]  # Archived tasks
            logger.info(f"Applied archived filter: {status_filter}")
        elif intent == 'list_tasks':
            status_filter = [1, 2, 3, 4, 8]  # All active tasks by default
            logger.info(f"Applied default list_tasks filter: {status_filter}")
        elif intent == 'task_summary':
            status_filter = [1, 2, 3, 4]  # Active tasks for summary
            logger.info(f"Applied task_summary filter: {status_filter}")
        elif intent == 'performance_report':
            status_filter = None  # All tasks including completed
            logger.info(f"Applied performance_report filter: {status_filter}")
        elif intent == 'anomaly_check':
            status_filter = [1, 2, 3, 4]  # Active tasks to check for issues
            logger.info(f"Applied anomaly_check filter: {status_filter}")
        else:
            logger.info(f"No filter applied, using None: {status_filter}")
        
        logger.info(f"Final status_filter: {status_filter}")
        
        # Get tasks from CRM
        tasks = crm.get_tasks_for_employee(
            employee_id=employee_id,
            status_filter=status_filter,
            limit=limit * 2  # Get more for filtering
        )
        
        # Add computed fields
        for task in tasks:
            task['status_name'] = Config.TASK_STATUS_MAP.get(task['status'], 'Unknown')
            task['priority_name'] = Config.TASK_PRIORITY_MAP.get(task['priority'], 'Unknown')
            
            # Check if overdue
            if task['duedate'] and task['status'] != 5:
                from datetime import datetime
                try:
                    due_date = datetime.strptime(task['duedate'], '%Y-%m-%d')
                    task['is_overdue'] = due_date < datetime.now()
                    task['days_overdue'] = (datetime.now() - due_date).days if task['is_overdue'] else 0
                except:
                    task['is_overdue'] = False
                    task['days_overdue'] = 0
            else:
                task['is_overdue'] = False
                task['days_overdue'] = 0
        
        # Apply additional filters
        filtered_tasks = []
        for task in tasks:
            # Filter by overdue status
            if task_filters.get('overdue') and not task.get('is_overdue'):
                continue
                
            # Filter by priority
            if task_filters.get('priority'):
                priority_filter = task_filters['priority'].lower()
                task_priority = task['priority_name'].lower()
                if priority_filter not in task_priority:
                    continue
            
            filtered_tasks.append(task)
        
        return filtered_tasks[:limit]
    
    def _enhance_with_vector_similarity(self, tasks: List[Dict[str, Any]], 
                                       query: str) -> List[Dict[str, Any]]:
        """Enhance tasks with vector similarity scores"""
        try:
            # Generate query embedding
            query_embedding = self._get_embedding(query)
            
            # Calculate similarity scores for each task
            for task in tasks:
                task_text = self._get_task_text(task)
                task_embedding = self._get_embedding(task_text)
                
                # Calculate cosine similarity
                similarity = self._cosine_similarity(query_embedding, task_embedding)
                task['similarity_score'] = similarity
            
            # Sort by similarity score (descending)
            tasks.sort(key=lambda x: x.get('similarity_score', 0), reverse=True)
            
            logger.debug(f"Enhanced {len(tasks)} tasks with vector similarity")
            
        except Exception as e:
            logger.error("Failed to enhance with vector similarity", error=e)
        
        return tasks
    
    def _get_embedding(self, text: str) -> List[float]:
        """Get embedding for text, with caching"""
        
        # Check cache first
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        try:
            start_time = time.time()
            
            response = self.openai_client.embeddings.create(
                model=Config.OPENAI_MODEL_EMBEDDING,
                input=text
            )
            
            embedding = response.data[0].embedding
            response_time = time.time() - start_time
            
            # Cache the embedding
            self.embeddings_cache[text] = embedding
            
            logger.log_openai_request(
                Config.OPENAI_MODEL_EMBEDDING, response.usage.total_tokens,
                response_time, True
            )
            
            return embedding
            
        except Exception as e:
            logger.log_openai_request(Config.OPENAI_MODEL_EMBEDDING, 0, 0, False, str(e))
            # Return zero vector as fallback
            return [0.0] * Config.EMBEDDING_DIMENSION
    
    def _get_task_text(self, task: Dict[str, Any]) -> str:
        """Convert task to text for embedding"""
        parts = []
        
        if task.get('name'):
            parts.append(f"Task: {task['name']}")
        
        if task.get('description'):
            parts.append(f"Description: {task['description']}")
        
        if task.get('project_name'):
            parts.append(f"Project: {task['project_name']}")
        
        if task.get('status_name'):
            parts.append(f"Status: {task['status_name']}")
        
        if task.get('priority_name'):
            parts.append(f"Priority: {task['priority_name']}")
        
        return " | ".join(parts)
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        try:
            vec1_np = np.array(vec1)
            vec2_np = np.array(vec2)
            
            dot_product = np.dot(vec1_np, vec2_np)
            norm1 = np.linalg.norm(vec1_np)
            norm2 = np.linalg.norm(vec2_np)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
            
        except Exception as e:
            logger.error("Failed to calculate cosine similarity", error=e)
            return 0.0
    
    def build_embeddings_index(self, employee_id: int = None) -> Dict[str, Any]:
        """
        Build or rebuild embeddings index for tasks
        Args:
            employee_id: If specified, build index only for this employee
        Returns: Status dictionary
        """
        start_time = time.time()
        
        try:
            if not self.vector_db:
                return {
                    'success': False,
                    'error': 'No vector database available'
                }
            
            # Get tasks to index
            if employee_id:
                all_tasks = crm.get_tasks_for_employee(employee_id)
                logger.info(f"Building index for employee {employee_id}: {len(all_tasks)} tasks")
            else:
                # Get all employees and their tasks
                employees = crm.get_all_employees()
                all_tasks = []
                for emp in employees:
                    emp_tasks = crm.get_tasks_for_employee(emp['id'])
                    all_tasks.extend(emp_tasks)
                logger.info(f"Building index for all employees: {len(all_tasks)} tasks")
            
            if not all_tasks:
                return {
                    'success': True,
                    'indexed_count': 0,
                    'message': 'No tasks to index'
                }
            
            # Process tasks in batches
            batch_size = Config.EMBEDDING_BATCH_SIZE
            indexed_count = 0
            
            for i in range(0, len(all_tasks), batch_size):
                batch = all_tasks[i:i + batch_size]
                
                # Prepare batch data
                texts = [self._get_task_text(task) for task in batch]
                ids = [str(task['id']) for task in batch]
                metadatas = [{
                    'task_id': task['id'],
                    'employee_id': task['assigned'],
                    'status': task['status'],
                    'priority': task['priority'],
                    'project_name': task.get('project_name', ''),
                    'updated_at': int(time.time())
                } for task in batch]
                
                # Generate embeddings
                embeddings = []
                for text in texts:
                    embedding = self._get_embedding(text)
                    embeddings.append(embedding)
                
                # Store in vector database
                if Config.VECTOR_DB_TYPE == 'chroma':
                    self.vector_db.upsert(
                        ids=ids,
                        embeddings=embeddings,
                        documents=texts,
                        metadatas=metadatas
                    )
                elif Config.VECTOR_DB_TYPE == 'faiss':
                    # FAISS implementation would go here
                    pass
                
                indexed_count += len(batch)
                logger.debug(f"Indexed batch {i//batch_size + 1}: {len(batch)} tasks")
            
            processing_time = time.time() - start_time
            
            logger.log_embedding_operation(
                'build_index', indexed_count, True, processing_time
            )
            
            return {
                'success': True,
                'indexed_count': indexed_count,
                'processing_time': processing_time,
                'vector_db_type': Config.VECTOR_DB_TYPE
            }
            
        except Exception as e:
            processing_time = time.time() - start_time
            logger.log_embedding_operation('build_index', 0, False, processing_time)
            logger.error("Failed to build embeddings index", error=e)
            return {
                'success': False,
                'error': str(e),
                'processing_time': processing_time
            }
    
    def search_similar_tasks(self, query: str, employee_id: int = None, 
                           top_k: int = 10) -> List[Dict[str, Any]]:
        """
        Search for similar tasks using vector similarity
        Args:
            query: Search query
            employee_id: Optional employee filter
            top_k: Number of results to return
        Returns: List of similar tasks with similarity scores
        """
        try:
            if not self.vector_db:
                return []
            
            # Generate query embedding
            query_embedding = self._get_embedding(query)
            
            # Search vector database
            if Config.VECTOR_DB_TYPE == 'chroma':
                # Build where filter for employee
                where_filter = {}
                if employee_id:
                    where_filter['employee_id'] = employee_id
                
                results = self.vector_db.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_filter if where_filter else None
                )
                
                # Format results
                similar_tasks = []
                if results['ids'] and results['ids'][0]:
                    for i, task_id in enumerate(results['ids'][0]):
                        similar_tasks.append({
                            'task_id': int(task_id),
                            'similarity_score': 1 - results['distances'][0][i],  # Convert distance to similarity
                            'document': results['documents'][0][i],
                            'metadata': results['metadatas'][0][i]
                        })
                
                return similar_tasks
            
        except Exception as e:
            logger.error("Failed to search similar tasks", error=e)
            return []
    
    def clear_embeddings_cache(self):
        """Clear the embeddings cache"""
        self.embeddings_cache.clear()
        logger.info("Embeddings cache cleared")

# Global retriever instance
task_retriever = TaskRetriever()

def get_task_retriever() -> TaskRetriever:
    """Get the global task retriever instance"""
    return task_retriever