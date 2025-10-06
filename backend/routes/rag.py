"""
RAG API Routes - Task 1.4
=========================

FastAPI routes for the RAG (Retrieval-Augmented Generation) pipeline.
Provides REST API endpoints for querying the RAG system.

Endpoints:
- POST /rag/query: Submit query to RAG pipeline
- POST /rag/handbook: Process handbook data
- GET /rag/status: Get RAG system status
- POST /rag/test: Run test queries
- GET /rag/stats: Get system statistics

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import asyncio
from datetime import datetime

from core.logging_config import get_logger
from core.dependencies import get_current_user
from rag import RAGIntegrationService, create_rag_integration_service, SAMPLE_HANDBOOK_DATA

# Configure logging
logger = get_logger(__name__)

# Global RAG service instance
rag_service: Optional[RAGIntegrationService] = None

# Pydantic models for request/response
class RAGQueryRequest(BaseModel):
    """RAG query request model"""
    query: str = Field(..., description="Query text", min_length=1, max_length=2000)
    user_id: Optional[str] = Field(None, description="User identifier")
    context: Optional[Dict[str, Any]] = Field(None, description="Additional context")
    max_results: int = Field(5, description="Maximum results to return", ge=1, le=20)

class RAGQueryResponse(BaseModel):
    """RAG query response model"""
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    confidence: float = Field(..., ge=0.0, le=1.0)
    processing_time: float
    metadata: Dict[str, Any]

class HandbookDataRequest(BaseModel):
    """Handbook data processing request"""
    data: Dict[str, Any] = Field(..., description="Handbook data to process")
    replace_existing: bool = Field(False, description="Whether to replace existing data")

class HandbookDataResponse(BaseModel):
    """Handbook data processing response"""
    success: bool
    processed_sections: int
    indexed_documents: int
    total_documents: int
    processing_time: str

class RAGStatusResponse(BaseModel):
    """RAG system status response"""
    initialized: bool
    services: Dict[str, bool]
    config: Dict[str, Any]
    embedding_info: Optional[Dict[str, Any]] = None
    ai_info: Optional[Dict[str, Any]] = None
    retrieval_stats: Optional[Dict[str, Any]] = None
    pipeline_stats: Optional[Dict[str, Any]] = None

class TestQueryResult(BaseModel):
    """Test query result model"""
    query: str
    success: bool
    processing_time: float
    confidence: float
    sources_count: int
    response_length: int
    error: Optional[str] = None

class TestResponse(BaseModel):
    """Test response model"""
    total_queries: int
    successful_queries: int
    failed_queries: int
    average_processing_time: float
    average_confidence: float
    query_results: List[TestQueryResult]
    service_stats: Dict[str, Any]

# Create router
router = APIRouter(prefix="/rag", tags=["RAG Pipeline"])

async def get_rag_service() -> RAGIntegrationService:
    """Get or create RAG service instance"""
    global rag_service
    
    if rag_service is None:
        try:
            logger.info("Initializing RAG service...")
            rag_service = await create_rag_integration_service(
                initialize_immediately=True,
                process_sample_data=True
            )
            logger.info("RAG service initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"RAG service initialization failed: {str(e)}"
            )
    
    return rag_service

@router.post("/query", response_model=RAGQueryResponse)
async def query_rag(
    request: RAGQueryRequest,
    current_user: Dict[str, Any] = Depends(get_current_user),
    rag_service: RAGIntegrationService = Depends(get_rag_service)
):
    """
    Submit a query to the RAG pipeline
    
    This endpoint processes user queries through the complete RAG pipeline:
    1. Query processing and embedding
    2. Document retrieval from multiple sources
    3. AI response generation with context
    4. Response formatting and source tracking
    """
    try:
        logger.info(
            f"Processing RAG query from user {current_user.get('id', 'unknown')}: {request.query[:100]}..."
        )
        
        # Process query through RAG pipeline
        response = await rag_service.query(
            query_text=request.query,
            user_id=request.user_id or current_user.get("id"),
            context=request.context,
            max_results=request.max_results
        )
        
        # Format sources for response
        formatted_sources = []
        for source in response.sources:
            formatted_sources.append({
                "id": source.id,
                "content": source.content[:200] + "..." if len(source.content) > 200 else source.content,
                "source": source.source,
                "score": source.score,
                "metadata": source.metadata
            })
        
        rag_response = RAGQueryResponse(
            query=response.query,
            answer=response.answer,
            sources=formatted_sources,
            confidence=response.confidence,
            processing_time=response.processing_time,
            metadata=response.metadata
        )
        
        logger.info(
            f"RAG query completed successfully",
            extra={
                "user_id": current_user.get('id'),
                "confidence": response.confidence,
                "sources": len(response.sources),
                "processing_time": response.processing_time
            }
        )
        
        return rag_response
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Query processing failed: {str(e)}"
        )

@router.post("/handbook", response_model=HandbookDataResponse)
async def process_handbook_data(
    request: HandbookDataRequest,
    background_tasks: BackgroundTasks,
    current_user: Dict[str, Any] = Depends(get_current_user),
    rag_service: RAGIntegrationService = Depends(get_rag_service)
):
    """
    Process and index handbook data
    
    This endpoint allows uploading and processing of handbook/policy data
    that will be indexed for retrieval in the RAG pipeline.
    """
    try:
        logger.info(
            f"Processing handbook data from user {current_user.get('id', 'unknown')}: {len(request.data)} sections"
        )
        
        # Process handbook data
        result = await rag_service.process_handbook_data(request.data)
        
        if not result["success"]:
            raise HTTPException(
                status_code=400,
                detail=f"Handbook processing failed: {result.get('error', 'Unknown error')}"
            )
        
        response = HandbookDataResponse(
            success=result["success"],
            processed_sections=result["processed_sections"],
            indexed_documents=result["indexed_documents"],
            total_documents=result["total_documents"],
            processing_time=result["processing_time"]
        )
        
        logger.info(
            f"Handbook data processed successfully",
            extra={
                "user_id": current_user.get('id'),
                "sections": result["processed_sections"],
                "documents": result["indexed_documents"]
            }
        )
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Handbook processing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Handbook processing failed: {str(e)}"
        )

@router.get("/status", response_model=RAGStatusResponse)
async def get_rag_status(
    current_user: Dict[str, Any] = Depends(get_current_user),
    rag_service: RAGIntegrationService = Depends(get_rag_service)
):
    """
    Get RAG system status and health information
    
    Returns comprehensive information about the RAG system including:
    - Service initialization status
    - Component health status  
    - Configuration details
    - Performance statistics
    """
    try:
        status = await rag_service.get_system_status()
        
        response = RAGStatusResponse(
            initialized=status["initialized"],
            services=status["services"],
            config=status["config"],
            embedding_info=status.get("embedding_info"),
            ai_info=status.get("ai_info"),
            retrieval_stats=status.get("retrieval_stats"),
            pipeline_stats=status.get("pipeline_stats")
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Status check failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Status check failed: {str(e)}"
        )

@router.post("/test", response_model=TestResponse)
async def run_rag_tests(
    current_user: Dict[str, Any] = Depends(get_current_user),
    rag_service: RAGIntegrationService = Depends(get_rag_service)
):
    """
    Run comprehensive tests on the RAG pipeline
    
    Executes a series of test queries to validate:
    - Pipeline functionality
    - Response quality and relevance
    - Performance characteristics
    - Error handling
    """
    try:
        logger.info(f"Running RAG tests for user {current_user.get('id', 'unknown')}")
        
        # Run test suite
        test_results = await rag_service.test_with_sample_queries()
        
        # Format test results
        query_results = []
        for result in test_results["query_results"]:
            query_result = TestQueryResult(
                query=result["query"],
                success=result["success"],
                processing_time=result.get("processing_time", 0.0),
                confidence=result.get("confidence", 0.0),
                sources_count=result.get("sources_count", 0),
                response_length=result.get("response_length", 0),
                error=result.get("error")
            )
            query_results.append(query_result)
        
        response = TestResponse(
            total_queries=test_results["total_queries"],
            successful_queries=test_results["successful_queries"],
            failed_queries=test_results["failed_queries"],
            average_processing_time=test_results["average_processing_time"],
            average_confidence=test_results["average_confidence"],
            query_results=query_results,
            service_stats=test_results["service_stats"]
        )
        
        logger.info(
            f"RAG tests completed",
            extra={
                "user_id": current_user.get('id'),
                "total_queries": test_results["total_queries"],
                "successful": test_results["successful_queries"],
                "avg_confidence": test_results["average_confidence"]
            }
        )
        
        return response
        
    except Exception as e:
        logger.error(f"RAG testing failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Testing failed: {str(e)}"
        )

@router.get("/stats")
async def get_rag_stats(
    current_user: Dict[str, Any] = Depends(get_current_user),
    rag_service: RAGIntegrationService = Depends(get_rag_service)
):
    """
    Get detailed RAG system statistics
    
    Returns comprehensive metrics and analytics about:
    - Document counts by source
    - Query performance metrics
    - System resource usage
    - Service health indicators
    """
    try:
        # Get system status
        status = await rag_service.get_system_status()
        
        # Compile comprehensive stats
        stats = {
            "system_status": {
                "initialized": status["initialized"],
                "services_healthy": all(status["services"].values())
            },
            "document_stats": status.get("retrieval_stats", {}),
            "pipeline_stats": status.get("pipeline_stats", {}),
            "embedding_info": status.get("embedding_info", {}),
            "ai_info": status.get("ai_info", {}),
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return stats
        
    except Exception as e:
        logger.error(f"Stats retrieval failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Stats retrieval failed: {str(e)}"
        )

# Health check endpoint (no auth required)
@router.get("/health")
async def rag_health_check():
    """
    Simple health check for RAG system
    
    Returns basic health status without requiring authentication.
    Useful for monitoring and load balancer health checks.
    """
    try:
        global rag_service
        
        if rag_service is None:
            return {
                "status": "unhealthy",
                "message": "RAG service not initialized",
                "timestamp": datetime.utcnow().isoformat()
            }
        
        # Basic status check
        status = await rag_service.get_system_status()
        
        if status["initialized"] and all(status["services"].values()):
            return {
                "status": "healthy",
                "message": "RAG pipeline operational",
                "services": status["services"],
                "timestamp": datetime.utcnow().isoformat()
            }
        else:
            return {
                "status": "degraded",
                "message": "Some RAG services not available", 
                "services": status["services"],
                "timestamp": datetime.utcnow().isoformat()
            }
            
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {
            "status": "unhealthy",
            "message": f"Health check failed: {str(e)}",
            "timestamp": datetime.utcnow().isoformat()
        }

# Initialize RAG service on startup
@router.on_event("startup")
async def startup_rag_service():
    """Initialize RAG service on startup"""
    try:
        logger.info("Starting RAG service initialization...")
        await get_rag_service()
        logger.info("RAG service startup completed")
    except Exception as e:
        logger.error(f"RAG service startup failed: {e}")
        # Don't fail startup, service will be initialized on first request

# Export router
__all__ = ["router"]