# Enhanced AI Service with Vector Database Integration
from .ai_service import AICoordinationService
from .vector_service import VectorDatabaseService
from typing import Dict, List, Any
import json
from datetime import datetime

class EnhancedAIService(AICoordinationService):
    """
    Enhanced AI Service that integrates vector database for semantic search
    and intelligent prompt management
    """
    
    def __init__(self):
        super().__init__()
        self.vector_db = VectorDatabaseService()
        
    def smart_chat_with_context(self, user_message: str, session_id: str = None, 
                               use_vector_context: bool = True) -> Dict[str, Any]:
        """
        Enhanced chat function that uses vector database for context retrieval
        """
        try:
            response_data = {
                "response": "",
                "vector_context_used": False,
                "similar_prompts_found": 0,
                "relevant_context_found": 0,
                "business_knowledge_found": 0
            }
            
            # Build enhanced prompt with vector context
            enhanced_prompt = user_message
            context_sources = []
            
            if use_vector_context:
                # 1. Find similar successful prompts
                similar_prompts = self.vector_db.find_similar_prompts(user_message, n_results=3)
                if similar_prompts:
                    response_data["similar_prompts_found"] = len(similar_prompts)
                    context_sources.append("similar_prompts")
                    
                    prompt_context = "\n\nSimilar successful prompts for context:\n"
                    for prompt in similar_prompts[:2]:  # Use top 2
                        if prompt["similarity_score"] > 0.7:  # High similarity threshold
                            prompt_context += f"- {prompt['prompt'][:100]}...\n"
                    
                    if len(prompt_context) > 50:  # If we found relevant prompts
                        enhanced_prompt += prompt_context
                
                # 2. Find relevant conversation context
                relevant_context = self.vector_db.find_relevant_context(user_message, n_results=2)
                if relevant_context:
                    response_data["relevant_context_found"] = len(relevant_context)
                    context_sources.append("conversation_history")
                    
                    context_info = "\n\nRelevant conversation context:\n"
                    for context in relevant_context:
                        if context["relevance_score"] > 0.6:  # Relevance threshold
                            user_query = context["metadata"].get("user_query", "")
                            if user_query:
                                context_info += f"- Previous Q: {user_query[:80]}...\n"
                    
                    if len(context_info) > 50:
                        enhanced_prompt += context_info
                
                # 3. Search business knowledge base
                business_knowledge = self.vector_db.search_business_knowledge(user_message, n_results=2)
                if business_knowledge:
                    response_data["business_knowledge_found"] = len(business_knowledge)
                    context_sources.append("business_knowledge")
                    
                    knowledge_context = "\n\nRelevant business knowledge:\n"
                    for knowledge in business_knowledge:
                        if knowledge["relevance_score"] > 0.6:
                            knowledge_context += f"- {knowledge['content'][:100]}...\n"
                    
                    if len(knowledge_context) > 50:
                        enhanced_prompt += knowledge_context
                
                response_data["vector_context_used"] = len(context_sources) > 0
            
            # Add instruction for AI to use context appropriately
            if response_data["vector_context_used"]:
                enhanced_prompt += "\n\nPlease use the above context information to provide a more informed and relevant response."
            
            # Get AI response using enhanced prompt
            ai_response = self.chat(enhanced_prompt)
            response_data["response"] = ai_response
            
            # Store this interaction in vector database for future context
            if session_id:
                self.vector_db.store_conversation_context(
                    conversation_id=session_id,
                    context=f"Enhanced prompt with vector context from: {', '.join(context_sources)}",
                    user_query=user_message,
                    ai_response=ai_response
                )
            
            # Note: No traditional database storage since base AI service doesn't have smart_chat
            response_data.update({
                "conversation_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "response_time": 0  # Could add timing here
            })
            
            return response_data
            
        except Exception as e:
            print(f"Error in enhanced smart chat: {e}")
            # Fallback to traditional chat
            return {
                "response": self.chat(user_message),
                "conversation_id": session_id,
                "timestamp": datetime.utcnow().isoformat(),
                "vector_context_used": False,
                "error_fallback": True
            }
    
    def store_effective_prompt(self, prompt: str, category: str = "user_generated", 
                             effectiveness_score: float = None) -> bool:
        """Store prompts that have been effective for future reference"""
        try:
            prompt_id = f"user_prompt_{hash(prompt)}_{int(datetime.utcnow().timestamp())}"
            metadata = {
                "category": category,
                "effectiveness_score": effectiveness_score or 0.8,
                "source": "user_interaction"
            }
            
            return self.vector_db.store_prompt_template(
                prompt_id=prompt_id,
                prompt_text=prompt,
                category=category,
                metadata=metadata
            )
        except Exception as e:
            print(f"Error storing effective prompt: {e}")
            return False
    
    def get_prompt_suggestions(self, partial_query: str, n_suggestions: int = 5) -> List[str]:
        """Get prompt suggestions based on similar successful prompts"""
        try:
            similar_prompts = self.vector_db.find_similar_prompts(partial_query, n_results=n_suggestions)
            suggestions = []
            
            for prompt in similar_prompts:
                if prompt["similarity_score"] > 0.5:  # Reasonable similarity
                    # Extract key phrases from successful prompts
                    prompt_text = prompt["prompt"]
                    if len(prompt_text) > 100:
                        prompt_text = prompt_text[:100] + "..."
                    suggestions.append(prompt_text)
            
            return suggestions
        except Exception as e:
            print(f"Error getting prompt suggestions: {e}")
            return []
    
    def analyze_query_patterns(self) -> Dict[str, Any]:
        """Analyze patterns in user queries using vector database"""
        try:
            stats = self.vector_db.get_collection_stats()
            
            # Get recent conversations for pattern analysis
            # This is a simplified analysis - could be enhanced with clustering
            return {
                "total_prompts_stored": stats.get("prompt_templates", 0),
                "total_conversations": stats.get("conversation_contexts", 0),
                "business_knowledge_items": stats.get("business_knowledge", 0),
                "pattern_analysis": "Vector-based pattern analysis would require clustering algorithms",
                "recommendations": [
                    "Store more effective prompts to improve suggestions",
                    "Build business knowledge base for domain-specific queries",
                    "Use conversation context for better continuity"
                ]
            }
        except Exception as e:
            print(f"Error analyzing query patterns: {e}")
            return {"error": str(e)}
    
    def initialize_business_knowledge(self) -> bool:
        """Initialize vector database with business knowledge from MySQL"""
        try:
            from ..models.models import db
            
            # This would extract business knowledge from existing MySQL tables
            # and store as embeddings for semantic search
            
            # Example: Extract project types and common workflows
            sample_knowledge = [
                {
                    "id": "project_types",
                    "content": "Common project types: Web development, Mobile apps, Desktop software, API development, Database design, System integration",
                    "topic": "project_management"
                },
                {
                    "id": "client_communication", 
                    "content": "Client communication best practices: Regular updates, clear timelines, documented requirements, change request process",
                    "topic": "client_management"
                },
                {
                    "id": "task_prioritization",
                    "content": "Task prioritization framework: Urgent and important tasks first, client deadlines, resource availability, dependency mapping",
                    "topic": "task_management"
                }
            ]
            
            success_count = 0
            for knowledge in sample_knowledge:
                if self.vector_db.store_business_knowledge(
                    knowledge_id=knowledge["id"],
                    content=knowledge["content"],
                    topic=knowledge["topic"],
                    source="mysql_extraction"
                ):
                    success_count += 1
            
            return success_count == len(sample_knowledge)
            
        except Exception as e:
            print(f"Error initializing business knowledge: {e}")
            return False

# Example usage
if __name__ == "__main__":
    enhanced_ai = EnhancedAIService()
    
    # Initialize with some business knowledge
    enhanced_ai.initialize_business_knowledge()
    
    # Test enhanced chat
    response = enhanced_ai.smart_chat_with_context(
        "How should I prioritize my project tasks?",
        session_id="test_session_1"
    )
    
    print("Enhanced AI Response:", response)