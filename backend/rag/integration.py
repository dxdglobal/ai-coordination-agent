"""
RAG Integration and Testing - Task 1.4
======================================

Complete RAG pipeline integration with handbook data processing and testing capabilities.
Provides end-to-end RAG functionality with the Account Management and Coordination Department data.

Features:
- Complete RAG pipeline integration
- Handbook data processing and indexing
- Sample query testing and validation
- Performance monitoring and analytics
- Integration with FastAPI backend

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import os
import logging
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import json

from core.logging_config import get_logger
from .pipeline import RAGPipeline, RAGQuery, RAGResponse, create_rag_pipeline
from .embedding_service import create_default_embedding_service, EmbeddingResult
from .retrieval_service import (
    create_multi_source_retrieval_service, 
    HandbookDataProcessor,
    DocumentIndex
)
from .ai_service import create_default_ai_service

# Configure logging
logger = get_logger(__name__)

class RAGIntegrationService:
    """
    Complete RAG integration service for the AI Coordination Agent
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        self.pipeline = None
        self.embedding_service = None
        self.retrieval_service = None
        self.ai_service = None
        self.is_initialized = False
        
        logger.info("RAG Integration Service created")
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration"""
        return {
            "embedding": {
                "provider": "auto",  # auto, openai, sentence_transformers
                "model": "text-embedding-ada-002",  # for OpenAI
                "cache_enabled": True,
                "chunk_size": 512,
                "chunk_overlap": 50
            },
            "retrieval": {
                "vector_db": "chromadb",
                "persist_directory": "chroma_db",
                "collection_name": "rag_documents",
                "max_results": 10,
                "min_score": 0.3
            },
            "ai": {
                "provider": "openai",
                "model": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 500
            },
            "pipeline": {
                "max_context_length": 4000,
                "enable_reranking": True,
                "enable_follow_ups": True
            }
        }
    
    async def initialize(self) -> bool:
        """
        Initialize all RAG services
        
        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info("Initializing RAG services...")
            
            # 1. Initialize embedding service
            self.embedding_service = create_default_embedding_service()
            logger.info(f"Embedding service initialized: {self.embedding_service.get_service_info()}")
            
            # 2. Initialize retrieval service
            self.retrieval_service = create_multi_source_retrieval_service()
            logger.info("Retrieval service initialized")
            
            # 3. Initialize AI service
            self.ai_service = create_default_ai_service()
            logger.info(f"AI service initialized: {self.ai_service.get_service_info()}")
            
            # 4. Create complete RAG pipeline
            self.pipeline = create_rag_pipeline(
                embedding_service=self.embedding_service,
                retrieval_service=self.retrieval_service,
                ai_service=self.ai_service,
                config=self.config.get("pipeline", {})
            )
            
            self.is_initialized = True
            logger.info("RAG Integration Service fully initialized")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG services: {e}", exc_info=True)
            return False
    
    async def process_handbook_data(self, handbook_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and index handbook data
        
        Args:
            handbook_data: Raw handbook data
            
        Returns:
            Processing results and statistics
        """
        if not self.is_initialized:
            raise RuntimeError("RAG services not initialized. Call initialize() first.")
        
        try:
            logger.info("Processing handbook data...")
            
            # 1. Process handbook data into embeddings
            embedding_results = await self.embedding_service.embed_handbook_data(handbook_data)
            logger.info(f"Generated {len(embedding_results)} embeddings")
            
            # 2. Convert to document indexes
            documents = []
            for result in embedding_results:
                document = DocumentIndex(
                    id=result.metadata.get("chunk_id", f"doc_{len(documents)}"),
                    content=result.text,
                    source="handbook",
                    embedding=result.embedding,
                    metadata=result.metadata,
                    timestamp=datetime.utcnow()
                )
                documents.append(document)
            
            # 3. Add to retrieval service
            indexed_count = await self.retrieval_service.add_handbook_documents(documents)
            
            # 4. Get processing statistics
            stats = await self.retrieval_service.get_service_stats()
            
            result = {
                "success": True,
                "processed_sections": len(handbook_data),
                "embedding_chunks": len(embedding_results),
                "indexed_documents": indexed_count,
                "total_documents": stats["vector_service"]["total_documents"],
                "handbook_documents": stats["vector_service"]["handbook_documents"],
                "processing_time": datetime.utcnow().isoformat()
            }
            
            logger.info(f"Handbook data processing completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Handbook data processing error: {e}", exc_info=True)
            return {
                "success": False,
                "error": str(e),
                "processed_sections": 0,
                "indexed_documents": 0
            }
    
    async def query(
        self,
        query_text: str,
        user_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        max_results: int = 5
    ) -> RAGResponse:
        """
        Process a query through the RAG pipeline
        
        Args:
            query_text: User query
            user_id: Optional user identifier
            context: Optional query context
            max_results: Maximum results to return
            
        Returns:
            RAG response
        """
        if not self.is_initialized:
            raise RuntimeError("RAG services not initialized. Call initialize() first.")
        
        try:
            # Create RAG query
            rag_query = RAGQuery(
                text=query_text,
                user_id=user_id,
                context=context,
                max_results=max_results,
                min_score=self.config["retrieval"]["min_score"]
            )
            
            # Process through pipeline
            response = await self.pipeline.process_query(rag_query)
            
            logger.info(
                f"Query processed successfully",
                extra={
                    "query_length": len(query_text),
                    "sources": len(response.sources),
                    "confidence": response.confidence
                }
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Query processing error: {e}", exc_info=True)
            raise
    
    async def test_with_sample_queries(self) -> Dict[str, Any]:
        """
        Test RAG pipeline with sample queries
        
        Returns:
            Test results and performance metrics
        """
        if not self.is_initialized:
            raise RuntimeError("RAG services not initialized. Call initialize() first.")
        
        # Sample queries for testing
        sample_queries = [
            "What are the project control templates for account management?",
            "How do I coordinate tasks between different departments?",
            "What is the process for client escalation management?",
            "What are the requirements for project status reporting?",
            "How should team coordination be handled for large projects?",
            "What are the guidelines for client communication protocols?",
            "How do I track project milestones and deliverables?",
            "What is the procedure for handling project budget changes?"
        ]
        
        test_results = {
            "total_queries": len(sample_queries),
            "successful_queries": 0,
            "failed_queries": 0,
            "average_processing_time": 0.0,
            "average_confidence": 0.0,
            "query_results": []
        }
        
        total_processing_time = 0.0
        total_confidence = 0.0
        
        logger.info(f"Testing RAG pipeline with {len(sample_queries)} sample queries...")
        
        for i, query in enumerate(sample_queries):
            try:
                # Process query
                response = await self.query(query, user_id="test_user")
                
                # Record results
                query_result = {
                    "query": query,
                    "success": True,
                    "processing_time": response.processing_time,
                    "confidence": response.confidence,
                    "sources_count": len(response.sources),
                    "response_length": len(response.answer),
                    "sources": [
                        {
                            "source": source.source,
                            "score": source.score
                        }
                        for source in response.sources
                    ]
                }
                
                test_results["query_results"].append(query_result)
                test_results["successful_queries"] += 1
                total_processing_time += response.processing_time
                total_confidence += response.confidence
                
                logger.debug(f"Query {i+1}/{len(sample_queries)} completed successfully")
                
            except Exception as e:
                # Record failure
                query_result = {
                    "query": query,
                    "success": False,
                    "error": str(e),
                    "processing_time": 0.0,
                    "confidence": 0.0,
                    "sources_count": 0
                }
                
                test_results["query_results"].append(query_result)
                test_results["failed_queries"] += 1
                
                logger.error(f"Query {i+1}/{len(sample_queries)} failed: {e}")
        
        # Calculate averages
        if test_results["successful_queries"] > 0:
            test_results["average_processing_time"] = total_processing_time / test_results["successful_queries"]
            test_results["average_confidence"] = total_confidence / test_results["successful_queries"]
        
        # Add service statistics
        service_stats = await self.retrieval_service.get_service_stats()
        test_results["service_stats"] = service_stats
        test_results["pipeline_stats"] = self.pipeline.get_pipeline_stats()
        
        logger.info(f"Testing completed: {test_results['successful_queries']}/{test_results['total_queries']} queries successful")
        return test_results
    
    async def get_system_status(self) -> Dict[str, Any]:
        """Get complete system status"""
        status = {
            "initialized": self.is_initialized,
            "services": {
                "embedding_service": bool(self.embedding_service),
                "retrieval_service": bool(self.retrieval_service),
                "ai_service": bool(self.ai_service),
                "pipeline": bool(self.pipeline)
            },
            "config": self.config
        }
        
        if self.is_initialized:
            # Add service details
            status["embedding_info"] = self.embedding_service.get_service_info()
            status["ai_info"] = self.ai_service.get_service_info()
            status["retrieval_stats"] = await self.retrieval_service.get_service_stats()
            status["pipeline_stats"] = self.pipeline.get_pipeline_stats()
        
        return status
    
    def update_config(self, new_config: Dict[str, Any]):
        """Update configuration"""
        self.config.update(new_config)
        logger.info("Configuration updated")

# Default handbook data for testing
SAMPLE_HANDBOOK_DATA = {
    "Account Management and Coordination Department": {
        "Project Control Templates": [
            "Project Charter Template: Define project scope, objectives, and stakeholders",
            "Work Breakdown Structure (WBS): Hierarchical decomposition of project tasks",
            "Project Schedule Template: Timeline with milestones and dependencies",
            "Risk Register: Identify, assess, and track project risks",
            "Status Report Template: Weekly/monthly progress reporting format",
            "Change Request Form: Process for handling scope changes",
            "Quality Checklist: Standards and criteria for deliverable review"
        ],
        "Coordination Protocols": [
            "Daily standup meetings for active projects",
            "Weekly cross-functional team meetings",
            "Monthly client review sessions",
            "Quarterly strategic planning meetings",
            "Escalation matrix for issue resolution",
            "Communication channels and response times",
            "Document sharing and version control procedures"
        ],
        "Task Management Guidelines": [
            "Task priority classification (High, Medium, Low)",
            "Assignment and ownership protocols",
            "Progress tracking and status updates",
            "Deadline management and buffer planning",
            "Resource allocation and capacity planning",
            "Quality assurance and review processes",
            "Completion criteria and sign-off procedures"
        ],
        "Client Communication Standards": [
            "Initial project kickoff meeting requirements",
            "Regular status update frequency and format",
            "Client feedback collection and documentation",
            "Issue escalation and resolution communication",
            "Project milestone celebration and recognition",
            "Contract change communication protocols",
            "Project closure and handover procedures"
        ]
    }
}

# Factory function
async def create_rag_integration_service(
    config: Optional[Dict[str, Any]] = None,
    initialize_immediately: bool = True,
    process_sample_data: bool = True
) -> RAGIntegrationService:
    """
    Create and optionally initialize RAG integration service
    
    Args:
        config: Optional configuration
        initialize_immediately: Whether to initialize services immediately
        process_sample_data: Whether to process sample handbook data
        
    Returns:
        RAG integration service
    """
    service = RAGIntegrationService(config=config)
    
    if initialize_immediately:
        success = await service.initialize()
        if not success:
            raise RuntimeError("Failed to initialize RAG services")
        
        if process_sample_data:
            result = await service.process_handbook_data(SAMPLE_HANDBOOK_DATA)
            logger.info(f"Sample data processing result: {result}")
    
    return service

# Export integration components
__all__ = [
    "RAGIntegrationService",
    "SAMPLE_HANDBOOK_DATA",
    "create_rag_integration_service"
]