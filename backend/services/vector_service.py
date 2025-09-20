# Vector Database Service for AI Agent
import chromadb
from chromadb.utils import embedding_functions
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
                "business_knowledge": self.knowledge_collection.count()
            }
        except Exception as e:
            print(f"Error getting collection stats: {e}")
            return {"error": str(e)}

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