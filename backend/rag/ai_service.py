"""
AI Processing Service - Task 1.4
================================

AI processing service for the RAG pipeline.
Integrates with OpenAI and other AI providers for response generation.

Features:
- OpenAI GPT integration for response generation
- Context-aware prompt engineering
- Response quality assessment
- Multiple AI model support
- Error handling and fallback strategies

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from abc import ABC, abstractmethod
import asyncio
from dataclasses import dataclass
from datetime import datetime
import json

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from core.logging_config import get_logger
from .pipeline import RetrievedDocument

# Configure logging
logger = get_logger(__name__)

@dataclass
class AIResponse:
    """AI response structure"""
    response: str
    model: str
    tokens_used: int
    processing_time: float
    confidence: float
    metadata: Dict[str, Any]

@dataclass
class PromptTemplate:
    """Prompt template structure"""
    name: str
    system_prompt: str
    user_prompt_template: str
    max_tokens: int
    temperature: float
    metadata: Dict[str, Any]

class BaseAIService(ABC):
    """Abstract base class for AI services"""
    
    @abstractmethod
    async def generate_response(
        self,
        query: str,
        context: str,
        temperature: float = 0.7,
        max_tokens: int = 500
    ) -> str:
        """Generate response using AI model"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name"""
        pass
    
    @abstractmethod
    def calculate_tokens(self, text: str) -> int:
        """Calculate token count"""
        pass

class OpenAIService(BaseAIService):
    """OpenAI GPT service for response generation"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "gpt-3.5-turbo",
        default_temperature: float = 0.7,
        default_max_tokens: int = 500
    ):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available. Install with: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.model = model
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        self.client = openai.OpenAI(api_key=self.api_key)
        
        logger.info(f"OpenAI service initialized with model: {model}")
    
    async def generate_response(
        self,
        query: str,
        context: str,
        temperature: float = None,
        max_tokens: int = None
    ) -> str:
        """Generate response using OpenAI GPT"""
        try:
            # Use defaults if not specified
            temperature = temperature or self.default_temperature
            max_tokens = max_tokens or self.default_max_tokens
            
            # Create conversation messages
            messages = [
                {
                    "role": "system",
                    "content": self._get_system_prompt()
                },
                {
                    "role": "user", 
                    "content": self._format_user_prompt(query, context)
                }
            ]
            
            # Generate response
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            generated_text = response.choices[0].message.content
            
            logger.debug(f"Generated response using {self.model}: {len(generated_text)} characters")
            return generated_text
            
        except Exception as e:
            logger.error(f"OpenAI response generation error: {e}")
            raise
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for AI coordination agent"""
        return """You are an AI Coordination Agent specializing in project management, task coordination, and account management. Your role is to assist with:

1. **Project Coordination**: Help coordinate tasks, deadlines, and team activities
2. **Account Management**: Provide guidance on client relationships and account strategies  
3. **Process Optimization**: Suggest improvements to workflows and procedures
4. **Information Synthesis**: Combine information from multiple sources to provide comprehensive answers

**Response Guidelines**:
- Be professional, helpful, and accurate
- Use the provided context to inform your responses
- If information is unclear or missing, acknowledge limitations
- Provide actionable recommendations when appropriate
- Structure responses clearly with bullet points or sections when helpful
- Reference specific sources when citing information

**Context Usage**:
- The context provided contains relevant information from company handbooks, CRM data, and previous conversations
- Always prioritize handbook policies and official procedures
- Use CRM data to provide specific project or client insights
- Acknowledge when recommendations are based on context vs. general knowledge"""
    
    def _format_user_prompt(self, query: str, context: str) -> str:
        """Format user prompt with query and context"""
        if not context.strip():
            return f"User Query: {query}\n\nNote: No specific context was found for this query. Please provide a helpful response based on general project management and coordination best practices."
        
        return f"""User Query: {query}

Relevant Context:
{context}

Please provide a comprehensive response based on the query and context above. If the context doesn't fully address the query, supplement with relevant general guidance while clearly indicating which parts are from the provided context vs. general recommendations."""
    
    def get_model_name(self) -> str:
        """Get model name"""
        return self.model
    
    def calculate_tokens(self, text: str) -> int:
        """Estimate token count (rough approximation)"""
        # Rough approximation: 1 token ≈ 4 characters for English text
        return len(text) // 4

class AIProcessingService:
    """
    Main AI processing service with enhanced capabilities
    """
    
    def __init__(
        self,
        ai_service: BaseAIService,
        prompt_templates: Optional[Dict[str, PromptTemplate]] = None
    ):
        self.ai_service = ai_service
        self.prompt_templates = prompt_templates or self._get_default_templates()
        
        logger.info(f"AI processing service initialized with {ai_service.get_model_name()}")
    
    def _get_default_templates(self) -> Dict[str, PromptTemplate]:
        """Get default prompt templates"""
        return {
            "general": PromptTemplate(
                name="general",
                system_prompt=self._get_general_system_prompt(),
                user_prompt_template="{query}\n\nContext:\n{context}",
                max_tokens=500,
                temperature=0.7,
                metadata={"type": "general_query"}
            ),
            "project_coordination": PromptTemplate(
                name="project_coordination",
                system_prompt=self._get_project_coordination_prompt(),
                user_prompt_template="Project Query: {query}\n\nRelevant Information:\n{context}",
                max_tokens=600,
                temperature=0.6,
                metadata={"type": "project_management"}
            ),
            "account_management": PromptTemplate(
                name="account_management", 
                system_prompt=self._get_account_management_prompt(),
                user_prompt_template="Account Management Query: {query}\n\nClient/Account Context:\n{context}",
                max_tokens=500,
                temperature=0.7,
                metadata={"type": "account_management"}
            )
        }
    
    def _get_general_system_prompt(self) -> str:
        """General system prompt"""
        return """You are an AI Coordination Agent that helps with project management, task coordination, and organizational efficiency. Provide clear, actionable responses based on the context provided."""
    
    def _get_project_coordination_prompt(self) -> str:
        """Project coordination system prompt"""
        return """You are a Project Coordination Specialist. Focus on:
- Task prioritization and scheduling
- Resource allocation and team coordination
- Deadline management and milestone tracking
- Risk identification and mitigation
- Process improvement recommendations

Provide structured, actionable guidance for project success."""
    
    def _get_account_management_prompt(self) -> str:
        """Account management system prompt"""
        return """You are an Account Management Specialist. Focus on:
- Client relationship management and communication strategies
- Account growth opportunities and upselling
- Issue resolution and client satisfaction
- Strategic account planning and goals
- Performance tracking and reporting

Provide strategic, client-focused recommendations."""
    
    async def generate_response(
        self,
        query: str,
        context: str,
        sources: List[RetrievedDocument],
        template_name: str = "general",
        custom_config: Optional[Dict[str, Any]] = None
    ) -> AIResponse:
        """
        Generate enhanced AI response with context and source tracking
        
        Args:
            query: User query
            context: Retrieved context
            sources: Source documents
            template_name: Prompt template to use
            custom_config: Custom configuration overrides
            
        Returns:
            AI response with metadata
        """
        start_time = datetime.utcnow()
        
        try:
            # Get prompt template
            template = self.prompt_templates.get(template_name, self.prompt_templates["general"])
            
            # Apply custom config
            temperature = custom_config.get("temperature", template.temperature) if custom_config else template.temperature
            max_tokens = custom_config.get("max_tokens", template.max_tokens) if custom_config else template.max_tokens
            
            # Enhance context with source information
            enhanced_context = self._enhance_context_with_sources(context, sources)
            
            # Generate response
            response_text = await self.ai_service.generate_response(
                query=query,
                context=enhanced_context,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            # Calculate processing time
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Estimate tokens used
            total_input_tokens = self.ai_service.calculate_tokens(query + enhanced_context)
            output_tokens = self.ai_service.calculate_tokens(response_text)
            
            # Calculate response confidence
            confidence = self._assess_response_confidence(response_text, sources, query)
            
            # Create AI response
            ai_response = AIResponse(
                response=response_text,
                model=self.ai_service.get_model_name(),
                tokens_used=total_input_tokens + output_tokens,
                processing_time=processing_time,
                confidence=confidence,
                metadata={
                    "template_used": template_name,
                    "sources_count": len(sources),
                    "context_length": len(enhanced_context),
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(
                f"Generated AI response",
                extra={
                    "model": ai_response.model,
                    "tokens": ai_response.tokens_used,
                    "confidence": ai_response.confidence,
                    "processing_time": processing_time
                }
            )
            
            return ai_response
            
        except Exception as e:
            logger.error(f"AI processing error: {e}", exc_info=True)
            raise
    
    def _enhance_context_with_sources(self, context: str, sources: List[RetrievedDocument]) -> str:
        """Enhance context with source metadata"""
        if not sources:
            return context
        
        # Add source summary at the beginning
        source_summary = self._create_source_summary(sources)
        enhanced_context = f"{source_summary}\n\n{context}"
        
        return enhanced_context
    
    def _create_source_summary(self, sources: List[RetrievedDocument]) -> str:
        """Create summary of sources used"""
        if not sources:
            return ""
        
        source_counts = {}
        for source in sources:
            source_type = source.source
            source_counts[source_type] = source_counts.get(source_type, 0) + 1
        
        summary_parts = []
        for source_type, count in source_counts.items():
            summary_parts.append(f"{count} {source_type.upper()} document(s)")
        
        return f"[Information Sources: {', '.join(summary_parts)}]"
    
    def _assess_response_confidence(
        self,
        response: str,
        sources: List[RetrievedDocument],
        query: str
    ) -> float:
        """
        Assess confidence in the generated response
        
        Factors:
        - Number and quality of sources
        - Average source scores
        - Response length and completeness
        - Query complexity vs. available information
        """
        if not sources:
            return 0.3  # Low confidence without sources
        
        # Base confidence from source scores
        avg_source_score = sum(source.score for source in sources) / len(sources)
        
        # Source diversity bonus
        unique_sources = len(set(source.source for source in sources))
        diversity_bonus = min(unique_sources * 0.1, 0.3)
        
        # Response completeness (longer responses might be more comprehensive)
        response_completeness = min(len(response) / 1000, 0.2)
        
        # Source count factor
        source_count_factor = min(len(sources) / 10, 0.2)
        
        confidence = min(
            avg_source_score + diversity_bonus + response_completeness + source_count_factor,
            1.0
        )
        
        return confidence
    
    async def generate_follow_up_suggestions(
        self,
        original_query: str,
        response: str,
        sources: List[RetrievedDocument]
    ) -> List[str]:
        """Generate follow-up question suggestions"""
        try:
            follow_up_prompt = f"""Based on this query and response, suggest 3-5 relevant follow-up questions:

Original Query: {original_query}

Response: {response[:500]}...

Generate specific, actionable follow-up questions that would help the user dive deeper into the topic or related areas. Format as a simple list."""
            
            suggestions_text = await self.ai_service.generate_response(
                query="Generate follow-up questions",
                context=follow_up_prompt,
                temperature=0.8,
                max_tokens=200
            )
            
            # Parse suggestions (simple line-based parsing)
            suggestions = [
                line.strip().lstrip("- ").lstrip("• ").lstrip("1234567890. ")
                for line in suggestions_text.split("\n")
                if line.strip() and not line.strip().startswith("Follow")
            ]
            
            return suggestions[:5]  # Limit to 5 suggestions
            
        except Exception as e:
            logger.error(f"Follow-up generation error: {e}")
            return []
    
    def add_custom_template(self, template: PromptTemplate):
        """Add custom prompt template"""
        self.prompt_templates[template.name] = template
        logger.info(f"Added custom template: {template.name}")
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get AI processing service information"""
        return {
            "ai_service": self.ai_service.get_model_name(),
            "available_templates": list(self.prompt_templates.keys()),
            "default_temperature": getattr(self.ai_service, 'default_temperature', 0.7),
            "default_max_tokens": getattr(self.ai_service, 'default_max_tokens', 500)
        }

# Factory functions
def create_openai_service(
    api_key: Optional[str] = None,
    model: str = "gpt-3.5-turbo"
) -> AIProcessingService:
    """Create OpenAI-based AI processing service"""
    ai_service = OpenAIService(api_key=api_key, model=model)
    return AIProcessingService(ai_service=ai_service)

def create_default_ai_service() -> AIProcessingService:
    """Create default AI processing service"""
    if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        logger.info("Using OpenAI service for AI processing")
        return create_openai_service()
    else:
        raise RuntimeError(
            "No AI service available. Install OpenAI package and set OPENAI_API_KEY:\n"
            "pip install openai\n"
            "export OPENAI_API_KEY=your_api_key"
        )

# Export AI processing components
__all__ = [
    "AIProcessingService",
    "BaseAIService", 
    "OpenAIService",
    "AIResponse",
    "PromptTemplate",
    "create_openai_service",
    "create_default_ai_service"
]