"""
RAG Pipeline Core - Task 1.4
=============================

Comprehensive Retrieval-Augmented Generation (RAG) pipeline for the AI Coordination Agent.
Implements the full pipeline: Query Input → Retrieve → AI Processing → Response Output.

Features:
- Vector embedding and similarity search
- Multi-source data retrieval (CRM, Handbook, Memory)
- OpenAI integration for response generation
- Query processing and context management
- Response ranking and filtering

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import os
import logging
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime
import asyncio
import json

from core.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)

@dataclass
class RAGQuery:
    """RAG query structure"""
    text: str
    user_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    filters: Optional[Dict[str, Any]] = None
    max_results: int = 5
    min_score: float = 0.5

@dataclass
class RetrievedDocument:
    """Retrieved document structure"""
    id: str
    content: str
    source: str  # 'handbook', 'crm', 'memory'
    score: float
    metadata: Dict[str, Any]
    timestamp: datetime

@dataclass
class RAGResponse:
    """RAG response structure"""
    query: str
    answer: str
    sources: List[RetrievedDocument]
    confidence: float
    processing_time: float
    metadata: Dict[str, Any]

class RAGPipeline:
    """
    Main RAG Pipeline orchestrator
    
    Pipeline Flow:
    1. Query Input → Process and validate query
    2. Retrieve → Search vector database for relevant documents
    3. AI Processing → Generate response using OpenAI with context
    4. Response Output → Format and return structured response
    """
    
    def __init__(
        self,
        embedding_service=None,
        retrieval_service=None,
        ai_service=None,
        config: Optional[Dict[str, Any]] = None
    ):
        self.embedding_service = embedding_service
        self.retrieval_service = retrieval_service
        self.ai_service = ai_service
        self.config = config or self._get_default_config()
        
        logger.info("RAG Pipeline initialized")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default RAG configuration"""
        return {
            "max_context_length": 4000,
            "max_retrieved_docs": 10,
            "min_relevance_score": 0.3,
            "enable_reranking": True,
            "temperature": 0.7,
            "max_tokens": 500,
            "model": "gpt-3.5-turbo"
        }
    
    async def process_query(self, query: RAGQuery) -> RAGResponse:
        """
        Process a RAG query through the complete pipeline
        
        Args:
            query: RAG query object
            
        Returns:
            RAG response with answer and sources
        """
        start_time = datetime.utcnow()
        
        try:
            logger.info(
                f"Processing RAG query: {query.text[:100]}...",
                extra={"user_id": query.user_id, "query_length": len(query.text)}
            )
            
            # Step 1: Query Input Processing
            processed_query = await self._process_query_input(query)
            
            # Step 2: Retrieve relevant documents
            retrieved_docs = await self._retrieve_documents(processed_query)
            
            # Step 3: AI Processing with retrieved context
            answer = await self._generate_response(processed_query, retrieved_docs)
            
            # Step 4: Format response output
            processing_time = (datetime.utcnow() - start_time).total_seconds()
            
            response = RAGResponse(
                query=query.text,
                answer=answer,
                sources=retrieved_docs[:query.max_results],
                confidence=self._calculate_confidence(retrieved_docs, answer),
                processing_time=processing_time,
                metadata={
                    "retrieved_docs_count": len(retrieved_docs),
                    "model_used": self.config["model"],
                    "timestamp": datetime.utcnow().isoformat()
                }
            )
            
            logger.info(
                f"RAG query processed successfully",
                extra={
                    "processing_time": processing_time,
                    "sources_count": len(retrieved_docs),
                    "confidence": response.confidence
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"RAG pipeline error: {e}", exc_info=True)
            raise
    
    async def _process_query_input(self, query: RAGQuery) -> RAGQuery:
        """
        Process and validate query input
        
        Args:
            query: Raw query input
            
        Returns:
            Processed query
        """
        # Clean and normalize query text
        processed_text = query.text.strip()
        
        # Add context enrichment
        if query.context:
            # Enrich query with user context
            if query.user_id:
                processed_text = f"User context: {query.context}. Query: {processed_text}"
        
        # Update query with processed text
        query.text = processed_text
        
        logger.debug(f"Query processed: {processed_text[:100]}...")
        return query
    
    async def _retrieve_documents(self, query: RAGQuery) -> List[RetrievedDocument]:
        """
        Retrieve relevant documents from all sources
        
        Args:
            query: Processed query
            
        Returns:
            List of retrieved documents
        """
        if not self.retrieval_service:
            logger.warning("No retrieval service configured")
            return []
        
        try:
            # Get query embedding
            query_embedding = await self.embedding_service.embed_query(query.text)
            
            # Search across all sources
            results = await self.retrieval_service.search(
                query_embedding=query_embedding,
                filters=query.filters,
                max_results=self.config["max_retrieved_docs"],
                min_score=query.min_score
            )
            
            # Filter by minimum relevance score
            filtered_results = [
                doc for doc in results 
                if doc.score >= self.config["min_relevance_score"]
            ]
            
            # Re-rank if enabled
            if self.config["enable_reranking"]:
                filtered_results = await self._rerank_documents(query, filtered_results)
            
            logger.debug(f"Retrieved {len(filtered_results)} relevant documents")
            return filtered_results
            
        except Exception as e:
            logger.error(f"Document retrieval error: {e}", exc_info=True)
            return []
    
    async def _rerank_documents(self, query: RAGQuery, documents: List[RetrievedDocument]) -> List[RetrievedDocument]:
        """
        Re-rank documents for better relevance
        
        Args:
            query: Original query
            documents: Retrieved documents
            
        Returns:
            Re-ranked documents
        """
        # Simple re-ranking based on content length and source priority
        source_priority = {"handbook": 3, "crm": 2, "memory": 1}
        
        def rerank_score(doc: RetrievedDocument) -> float:
            # Combine similarity score with source priority and content quality
            source_bonus = source_priority.get(doc.source, 0) * 0.1
            content_quality = min(len(doc.content) / 1000, 1.0) * 0.1
            return doc.score + source_bonus + content_quality
        
        return sorted(documents, key=rerank_score, reverse=True)
    
    async def _generate_response(self, query: RAGQuery, documents: List[RetrievedDocument]) -> str:
        """
        Generate AI response using retrieved context
        
        Args:
            query: Processed query
            documents: Retrieved documents
            
        Returns:
            Generated response
        """
        if not self.ai_service:
            logger.warning("No AI service configured")
            return "I'm sorry, I cannot process your request at this time."
        
        try:
            # Build context from retrieved documents
            context = self._build_context(documents)
            
            # Generate response using AI service
            response = await self.ai_service.generate_response(
                query=query.text,
                context=context,
                temperature=self.config["temperature"],
                max_tokens=self.config["max_tokens"]
            )
            
            return response
            
        except Exception as e:
            logger.error(f"AI response generation error: {e}", exc_info=True)
            return "I encountered an error while processing your request. Please try again."
    
    def _build_context(self, documents: List[RetrievedDocument]) -> str:
        """
        Build context string from retrieved documents
        
        Args:
            documents: Retrieved documents
            
        Returns:
            Formatted context string
        """
        if not documents:
            return ""
        
        context_parts = []
        total_length = 0
        max_length = self.config["max_context_length"]
        
        for doc in documents:
            # Format document with source information
            doc_text = f"[Source: {doc.source.upper()}]\n{doc.content}\n"
            
            # Check if adding this document would exceed context limit
            if total_length + len(doc_text) > max_length:
                # Truncate if necessary
                remaining_space = max_length - total_length
                if remaining_space > 100:  # Only add if meaningful space remains
                    doc_text = doc_text[:remaining_space] + "..."
                    context_parts.append(doc_text)
                break
            
            context_parts.append(doc_text)
            total_length += len(doc_text)
        
        return "\n".join(context_parts)
    
    def _calculate_confidence(self, documents: List[RetrievedDocument], answer: str) -> float:
        """
        Calculate confidence score for the response
        
        Args:
            documents: Retrieved documents
            answer: Generated answer
            
        Returns:
            Confidence score between 0 and 1
        """
        if not documents:
            return 0.1
        
        # Base confidence on average document scores
        avg_score = sum(doc.score for doc in documents) / len(documents)
        
        # Adjust based on number of sources
        source_diversity = len(set(doc.source for doc in documents))
        diversity_bonus = min(source_diversity * 0.1, 0.3)
        
        # Adjust based on answer length (longer answers might be more comprehensive)
        length_factor = min(len(answer) / 500, 1.0) * 0.1
        
        confidence = min(avg_score + diversity_bonus + length_factor, 1.0)
        return confidence
    
    async def batch_process_queries(self, queries: List[RAGQuery]) -> List[RAGResponse]:
        """
        Process multiple queries in batch
        
        Args:
            queries: List of RAG queries
            
        Returns:
            List of RAG responses
        """
        logger.info(f"Processing batch of {len(queries)} queries")
        
        # Process queries concurrently
        tasks = [self.process_query(query) for query in queries]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle any exceptions
        processed_responses = []
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                logger.error(f"Batch query {i} failed: {response}")
                # Create error response
                error_response = RAGResponse(
                    query=queries[i].text,
                    answer="Error processing query",
                    sources=[],
                    confidence=0.0,
                    processing_time=0.0,
                    metadata={"error": str(response)}
                )
                processed_responses.append(error_response)
            else:
                processed_responses.append(response)
        
        return processed_responses
    
    def get_pipeline_stats(self) -> Dict[str, Any]:
        """Get pipeline statistics and health information"""
        return {
            "config": self.config,
            "services": {
                "embedding_service": bool(self.embedding_service),
                "retrieval_service": bool(self.retrieval_service),
                "ai_service": bool(self.ai_service)
            },
            "status": "healthy" if all([
                self.embedding_service,
                self.retrieval_service,
                self.ai_service
            ]) else "degraded"
        }

class RAGPipelineBuilder:
    """Builder pattern for RAG pipeline configuration"""
    
    def __init__(self):
        self.embedding_service = None
        self.retrieval_service = None
        self.ai_service = None
        self.config = {}
    
    def with_embedding_service(self, service):
        """Add embedding service"""
        self.embedding_service = service
        return self
    
    def with_retrieval_service(self, service):
        """Add retrieval service"""
        self.retrieval_service = service
        return self
    
    def with_ai_service(self, service):
        """Add AI service"""
        self.ai_service = service
        return self
    
    def with_config(self, config: Dict[str, Any]):
        """Add configuration"""
        self.config.update(config)
        return self
    
    def build(self) -> RAGPipeline:
        """Build the RAG pipeline"""
        return RAGPipeline(
            embedding_service=self.embedding_service,
            retrieval_service=self.retrieval_service,
            ai_service=self.ai_service,
            config=self.config
        )

# Factory function for easy pipeline creation
def create_rag_pipeline(
    embedding_service=None,
    retrieval_service=None,
    ai_service=None,
    config: Optional[Dict[str, Any]] = None
) -> RAGPipeline:
    """
    Factory function to create RAG pipeline
    
    Args:
        embedding_service: Embedding service instance
        retrieval_service: Retrieval service instance
        ai_service: AI service instance
        config: Optional configuration
        
    Returns:
        Configured RAG pipeline
    """
    return RAGPipeline(
        embedding_service=embedding_service,
        retrieval_service=retrieval_service,
        ai_service=ai_service,
        config=config
    )

# Export RAG pipeline components
__all__ = [
    "RAGPipeline",
    "RAGPipelineBuilder",
    "RAGQuery",
    "RetrievedDocument",
    "RAGResponse",
    "create_rag_pipeline"
]