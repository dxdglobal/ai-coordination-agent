"""
RAG Module Initialization - Task 1.4
====================================

RAG (Retrieval-Augmented Generation) pipeline module for the AI Coordination Agent.
Provides complete RAG functionality with multi-source retrieval and AI processing.

This module implements:
- Complete RAG pipeline (Query → Retrieve → AI Processing → Response)
- Multi-provider embedding services (OpenAI, SentenceTransformers)
- Vector similarity search with ChromaDB
- AI response generation with OpenAI GPT
- Handbook data processing and indexing
- Performance monitoring and testing

Components:
- pipeline.py: Core RAG pipeline orchestration
- embedding_service.py: Text embedding and vectorization
- retrieval_service.py: Document retrieval and search
- ai_service.py: AI response generation
- integration.py: Complete integration and testing

Usage:
    from rag import create_rag_integration_service
    
    # Create and initialize RAG service
    rag_service = await create_rag_integration_service()
    
    # Process handbook data
    result = await rag_service.process_handbook_data(handbook_data)
    
    # Query the system
    response = await rag_service.query("How do I coordinate project tasks?")

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

# Core pipeline components
from .pipeline import (
    RAGPipeline,
    RAGPipelineBuilder,
    RAGQuery,
    RetrievedDocument,
    RAGResponse,
    create_rag_pipeline
)

# Embedding services
from .embedding_service import (
    EmbeddingService,
    BaseEmbeddingService,
    OpenAIEmbeddingService,
    SentenceTransformerEmbeddingService,
    EmbeddingResult,
    TextChunk,
    create_openai_embedding_service,
    create_sentence_transformer_embedding_service,
    create_default_embedding_service
)

# Retrieval services
from .retrieval_service import (
    BaseRetrievalService,
    ChromaDBRetrievalService,
    MultiSourceRetrievalService,
    HandbookDataProcessor,
    DocumentIndex,
    SearchFilter,
    create_chromadb_retrieval_service,
    create_multi_source_retrieval_service
)

# AI processing services
from .ai_service import (
    AIProcessingService,
    BaseAIService,
    OpenAIService,
    AIResponse,
    PromptTemplate,
    create_openai_service,
    create_default_ai_service
)

# Integration and testing
from .integration import (
    RAGIntegrationService,
    SAMPLE_HANDBOOK_DATA,
    create_rag_integration_service
)

# Module metadata
__version__ = "1.0.0"
__author__ = "AI Coordination Agent"
__description__ = "RAG Pipeline for AI Coordination Agent"

# Quick start function
async def quick_start_rag(handbook_data=None):
    """
    Quick start function for RAG pipeline
    
    Args:
        handbook_data: Optional handbook data to process
        
    Returns:
        Initialized RAG integration service
    """
    try:
        # Create and initialize RAG service
        rag_service = await create_rag_integration_service(
            initialize_immediately=True,
            process_sample_data=True
        )
        
        # Process additional handbook data if provided
        if handbook_data:
            result = await rag_service.process_handbook_data(handbook_data)
            print(f"Processed handbook data: {result['indexed_documents']} documents indexed")
        
        # Run basic test
        test_query = "What are the project control templates?"
        response = await rag_service.query(test_query)
        print(f"Test query successful: {response.confidence:.2f} confidence")
        
        return rag_service
        
    except Exception as e:
        print(f"RAG quick start failed: {e}")
        raise

# Export all components
__all__ = [
    # Core pipeline
    "RAGPipeline",
    "RAGPipelineBuilder", 
    "RAGQuery",
    "RetrievedDocument",
    "RAGResponse",
    "create_rag_pipeline",
    
    # Embedding services
    "EmbeddingService",
    "BaseEmbeddingService",
    "OpenAIEmbeddingService", 
    "SentenceTransformerEmbeddingService",
    "EmbeddingResult",
    "TextChunk",
    "create_openai_embedding_service",
    "create_sentence_transformer_embedding_service",
    "create_default_embedding_service",
    
    # Retrieval services
    "BaseRetrievalService",
    "ChromaDBRetrievalService",
    "MultiSourceRetrievalService",
    "HandbookDataProcessor",
    "DocumentIndex", 
    "SearchFilter",
    "create_chromadb_retrieval_service",
    "create_multi_source_retrieval_service",
    
    # AI services
    "AIProcessingService",
    "BaseAIService",
    "OpenAIService",
    "AIResponse",
    "PromptTemplate",
    "create_openai_service", 
    "create_default_ai_service",
    
    # Integration
    "RAGIntegrationService",
    "SAMPLE_HANDBOOK_DATA",
    "create_rag_integration_service",
    
    # Utilities
    "quick_start_rag"
]