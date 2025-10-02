# Vector Database Service for AI Agent
try:
    import chromadb
    from chromadb.utils import embedding_functions
    CHROMADB_AVAILABLE = True
except ImportError:
    chromadb = None
    embedding_functions = None
    CHROMADB_AVAILABLE = False

import os
from typing import List, Dict, Any
import json
from datetime import datetime

class VectorDatabaseService:
    """
    Vector database service for storing and retrieving AI prompts and conversations
    using semantic similarity search
    """
    
    def __init__(self, persist_directory: str = "./chroma_db"):
        """Initialize ChromaDB client and collections"""
        if not CHROMADB_AVAILABLE:
            self.client = None
            self.prompt_collection = None
            self.conversation_collection = None
            self.knowledge_collection = None
            return
            
        self.client = chromadb.PersistentClient(path=persist_directory)
        
        # Use OpenAI embeddings (requires API key)
        openai_ef = embedding_functions.OpenAIEmbeddingFunction(
            api_key=os.getenv("OPENAI_API_KEY"),
            model_name="text-embedding-ada-002"
        )
        
        # Create collections for different data types
        self.prompt_collection = self.client.get_or_create_collection(
            name="ai_prompts",
            embedding_function=openai_ef,
            metadata={"description": "AI prompt templates and responses"}
        )
        
        self.conversation_collection = self.client.get_or_create_collection(
            name="conversations",
            embedding_function=openai_ef,
            metadata={"description": "Conversation history and context"}
        )
        
        self.knowledge_collection = self.client.get_or_create_collection(
            name="business_knowledge",
            embedding_function=openai_ef,
            metadata={"description": "Business process knowledge base"}
        )
        
        # Task collection for semantic task search
        self.task_collection = self.client.get_or_create_collection(
            name="task_embeddings",
            embedding_function=openai_ef,
            metadata={"description": "Task embeddings for semantic search"}
        )
    
    def store_prompt_template(self, prompt_id: str, prompt_text: str, 
                            category: str = None, metadata: Dict = None) -> bool:
        """Store a prompt template with embeddings"""
        try:
            doc_metadata = {
                "category": category or "general",
                "created_at": datetime.utcnow().isoformat(),
                "type": "prompt_template"
            }
            if metadata:
                doc_metadata.update(metadata)
            
            self.prompt_collection.add(
                documents=[prompt_text],
                metadatas=[doc_metadata],
                ids=[prompt_id]
            )
            return True
        except Exception as e:
            print(f"Error storing prompt template: {e}")
            return False
    
    def find_similar_prompts(self, query: str, n_results: int = 5) -> List[Dict]:
        """Find similar prompts based on semantic similarity"""
        try:
            results = self.prompt_collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            similar_prompts = []
            for i, doc in enumerate(results['documents'][0]):
                similar_prompts.append({
                    "prompt": doc,
                    "metadata": results['metadatas'][0][i],
                    "similarity_score": 1 - results['distances'][0][i],  # Convert distance to similarity
                    "id": results['ids'][0][i] if 'ids' in results else None
                })
            
            return similar_prompts
        except Exception as e:
            print(f"Error finding similar prompts: {e}")
            return []
    
    def store_conversation_context(self, conversation_id: str, context: str, 
                                 user_query: str = None, ai_response: str = None) -> bool:
        """Store conversation context for future reference"""
        try:
            # Combine context for better embeddings
            full_context = context
            if user_query:
                full_context += f"\nUser Query: {user_query}"
            if ai_response:
                full_context += f"\nAI Response: {ai_response}"
            
            doc_metadata = {
                "conversation_id": conversation_id,
                "timestamp": datetime.utcnow().isoformat(),
                "type": "conversation_context",
                "user_query": user_query,
                "ai_response": ai_response
            }
            
            self.conversation_collection.add(
                documents=[full_context],
                metadatas=[doc_metadata],
                ids=[f"{conversation_id}_{datetime.utcnow().timestamp()}"]
            )
            return True
        except Exception as e:
            print(f"Error storing conversation context: {e}")
            return False
    
    def find_relevant_context(self, query: str, n_results: int = 3) -> List[Dict]:
        """Find relevant conversation context for current query"""
        try:
            results = self.conversation_collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            relevant_context = []
            for i, doc in enumerate(results['documents'][0]):
                relevant_context.append({
                    "context": doc,
                    "metadata": results['metadatas'][0][i],
                    "relevance_score": 1 - results['distances'][0][i],
                    "conversation_id": results['metadatas'][0][i].get('conversation_id')
                })
            
            return relevant_context
        except Exception as e:
            print(f"Error finding relevant context: {e}")
            return []
    
    def store_business_knowledge(self, knowledge_id: str, content: str, 
                               topic: str = None, source: str = None) -> bool:
        """Store business process knowledge"""
        try:
            doc_metadata = {
                "topic": topic or "general",
                "source": source or "manual",
                "created_at": datetime.utcnow().isoformat(),
                "type": "business_knowledge"
            }
            
            self.knowledge_collection.add(
                documents=[content],
                metadatas=[doc_metadata],
                ids=[knowledge_id]
            )
            return True
        except Exception as e:
            print(f"Error storing business knowledge: {e}")
            return False
    
    def search_business_knowledge(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search business knowledge base"""
        try:
            results = self.knowledge_collection.query(
                query_texts=[query],
                n_results=n_results,
                include=["documents", "metadatas", "distances"]
            )
            
            knowledge_results = []
            for i, doc in enumerate(results['documents'][0]):
                knowledge_results.append({
                    "content": doc,
                    "metadata": results['metadatas'][0][i],
                    "relevance_score": 1 - results['distances'][0][i],
                    "topic": results['metadatas'][0][i].get('topic'),
                    "source": results['metadatas'][0][i].get('source')
                })
            
            return knowledge_results
        except Exception as e:
            print(f"Error searching business knowledge: {e}")
            return []
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get statistics about stored data"""
        try:
            return {
                "prompt_templates": self.prompt_collection.count(),
                "conversation_contexts": self.conversation_collection.count(),
                "business_knowledge": self.knowledge_collection.count(),
                "task_embeddings": self.task_collection.count()
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {"error": str(e)}

    def store_task_embedding(self, task_id: int, task_data: Dict) -> bool:
        """Store task with embeddings for semantic search"""
        try:
            # Create a comprehensive text representation of the task
            task_text = f"Title: {task_data.get('title', '')}\n"
            task_text += f"Description: {task_data.get('description', '')}\n"
            task_text += f"Status: {task_data.get('status', '')}\n"
            task_text += f"Priority: {task_data.get('priority', '')}\n"
            
            if task_data.get('assignee'):
                task_text += f"Assignee: {task_data.get('assignee')}\n"
            if task_data.get('project_name'):
                task_text += f"Project: {task_data.get('project_name')}\n"
            if task_data.get('labels'):
                labels = [label['name'] for label in task_data.get('labels', [])]
                task_text += f"Labels: {', '.join(labels)}\n"
            
            # Metadata for filtering and retrieval
            metadata = {
                "task_id": task_id,
                "title": task_data.get('title', ''),
                "status": task_data.get('status', ''),
                "priority": task_data.get('priority', ''),
                "assignee": task_data.get('assignee', ''),
                "project_id": task_data.get('project_id'),
                "project_name": task_data.get('project_name', ''),
                "created_at": task_data.get('created_at', datetime.utcnow().isoformat()),
                "updated_at": task_data.get('updated_at', datetime.utcnow().isoformat()),
                "type": "task"
            }
            
            # Add estimated and actual hours if available
            if task_data.get('estimated_hours'):
                metadata["estimated_hours"] = task_data.get('estimated_hours')
            if task_data.get('actual_hours'):
                metadata["actual_hours"] = task_data.get('actual_hours')
            
            # Add deadline info if available
            if task_data.get('start_time'):
                metadata["start_time"] = task_data.get('start_time')
            if task_data.get('end_time'):
                metadata["end_time"] = task_data.get('end_time')
            
            self.task_collection.add(
                documents=[task_text.strip()],
                metadatas=[metadata],
                ids=[f"task_{task_id}"]
            )
            return True
        except Exception as e:
            print(f"Error storing task embedding: {e}")
            return False
    
    def update_task_embedding(self, task_id: int, task_data: Dict) -> bool:
        """Update existing task embedding"""
        try:
            # First, try to delete the existing embedding
            try:
                self.task_collection.delete(ids=[f"task_{task_id}"])
            except:
                pass  # ID might not exist, which is fine
            
            # Then store the new embedding
            return self.store_task_embedding(task_id, task_data)
        except Exception as e:
            print(f"Error updating task embedding: {e}")
            return False
    
    def delete_task_embedding(self, task_id: int) -> bool:
        """Delete task embedding from vector database"""
        try:
            self.task_collection.delete(ids=[f"task_{task_id}"])
            return True
        except Exception as e:
            print(f"Error deleting task embedding: {e}")
            return False
    
    def semantic_task_search(self, query: str, n_results: int = 10, filters: Dict = None) -> List[Dict]:
        """
        Perform semantic search on tasks using natural language queries
        
        Args:
            query: Natural language query (e.g., "Find high priority tasks", "Show overdue items")
            n_results: Number of results to return
            filters: Optional filters like {"status": "todo", "priority": "high"}
        """
        try:
            # Build where clause for filtering if provided
            where_clause = {}
            if filters:
                for key, value in filters.items():
                    if value:  # Only add non-empty filters
                        where_clause[key] = value
            
            # Perform semantic search
            search_kwargs = {
                "query_texts": [query],
                "n_results": n_results,
                "include": ["documents", "metadatas", "distances"]
            }
            
            if where_clause:
                search_kwargs["where"] = where_clause
            
            results = self.task_collection.query(**search_kwargs)
            
            # Format results
            semantic_results = []
            for i in range(len(results['documents'][0])):
                task_data = {
                    "task_id": results['metadatas'][0][i].get('task_id'),
                    "title": results['metadatas'][0][i].get('title'),
                    "content": results['documents'][0][i],
                    "metadata": results['metadatas'][0][i],
                    "relevance_score": 1 - results['distances'][0][i],  # Convert distance to similarity
                    "status": results['metadatas'][0][i].get('status'),
                    "priority": results['metadatas'][0][i].get('priority'),
                    "assignee": results['metadatas'][0][i].get('assignee'),
                    "project_name": results['metadatas'][0][i].get('project_name')
                }
                semantic_results.append(task_data)
            
            return semantic_results
        except Exception as e:
            print(f"Error in semantic task search: {e}")
            return []
    
    def get_overdue_tasks_semantic(self, query: str = "overdue tasks past deadline urgent", n_results: int = 10) -> List[Dict]:
        """Get potentially overdue tasks using semantic search"""
        return self.semantic_task_search(query, n_results)
    
    def get_high_priority_tasks_semantic(self, query: str = "high priority urgent important critical tasks", n_results: int = 10) -> List[Dict]:
        """Get high priority tasks using semantic search"""
        return self.semantic_task_search(query, n_results)
    
    def search_tasks_by_assignee_semantic(self, assignee: str, additional_query: str = "", n_results: int = 10) -> List[Dict]:
        """Search tasks for a specific assignee using semantic search"""
        query = f"tasks assigned to {assignee} {additional_query}".strip()
        filters = {"assignee": assignee} if assignee else None
        return self.semantic_task_search(query, n_results, filters)
    
    def search_tasks_by_project_semantic(self, project_name: str, additional_query: str = "", n_results: int = 10) -> List[Dict]:
        """Search tasks within a specific project using semantic search"""
        query = f"tasks in project {project_name} {additional_query}".strip()
        filters = {"project_name": project_name} if project_name else None
        return self.semantic_task_search(query, n_results, filters)

# Example usage and testing
if __name__ == "__main__":
    # Initialize vector database
    vector_db = VectorDatabaseService()
    
    # Test storing and retrieving prompts
    vector_db.store_prompt_template(
        prompt_id="project_analysis_1",
        prompt_text="Analyze project status and provide recommendations for timeline optimization",
        category="project_management",
        metadata={"priority": "high", "domain": "project_analysis"}
    )
    
    # Test finding similar prompts
    similar = vector_db.find_similar_prompts("help with project planning", n_results=3)
    print("Similar prompts:", similar)
    
    # Test business knowledge storage
    vector_db.store_business_knowledge(
        knowledge_id="project_workflow_1",
        content="Standard project workflow: Requirements gathering, design, development, testing, deployment, maintenance",
        topic="project_management",
        source="company_handbook"
    )
    
    # Get stats
    stats = vector_db.get_collection_stats()
    print("Collection stats:", stats)