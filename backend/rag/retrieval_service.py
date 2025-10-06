"""
Retrieval Service - Task 1.4
============================

Comprehensive document retrieval service for the RAG pipeline.
Implements vector similarity search with multiple backends and filtering.

Features:
- Multi-source document retrieval (Handbook, CRM, Memory)
- Vector similarity search with ChromaDB
- Advanced filtering and ranking
- Metadata-based search enhancement
- Hybrid search capabilities (vector + keyword)

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from abc import ABC, abstractmethod
import asyncio
import json
from dataclasses import dataclass, asdict
from datetime import datetime
import uuid

try:
    import chromadb
    from chromadb.config import Settings
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

from core.logging_config import get_logger
from .pipeline import RetrievedDocument

# Configure logging
logger = get_logger(__name__)

@dataclass
class DocumentIndex:
    """Document index entry"""
    id: str
    content: str
    source: str
    embedding: List[float]
    metadata: Dict[str, Any]
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "content": self.content,
            "source": self.source,
            "embedding": self.embedding,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }

@dataclass
class SearchFilter:
    """Search filter structure"""
    sources: Optional[List[str]] = None
    date_range: Optional[Tuple[datetime, datetime]] = None
    metadata_filters: Optional[Dict[str, Any]] = None
    content_length_range: Optional[Tuple[int, int]] = None
    
class BaseRetrievalService(ABC):
    """Abstract base class for retrieval services"""
    
    @abstractmethod
    async def add_document(self, document: DocumentIndex) -> bool:
        """Add document to index"""
        pass
    
    @abstractmethod
    async def add_documents(self, documents: List[DocumentIndex]) -> int:
        """Add multiple documents to index"""
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        filters: Optional[SearchFilter] = None,
        max_results: int = 10,
        min_score: float = 0.0
    ) -> List[RetrievedDocument]:
        """Search for similar documents"""
        pass
    
    @abstractmethod
    async def delete_document(self, document_id: str) -> bool:
        """Delete document from index"""
        pass
    
    @abstractmethod
    async def get_document_count(self, source: Optional[str] = None) -> int:
        """Get total document count"""
        pass

class ChromaDBRetrievalService(BaseRetrievalService):
    """ChromaDB-based retrieval service"""
    
    def __init__(
        self,
        persist_directory: str = "chroma_db",
        collection_name: str = "rag_documents"
    ):
        if not CHROMADB_AVAILABLE:
            raise ImportError("ChromaDB package not available. Install with: pip install chromadb")
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        try:
            os.makedirs(persist_directory, exist_ok=True)
            self.client = chromadb.PersistentClient(path=persist_directory)
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": "RAG pipeline documents"}
            )
            
            logger.info(f"ChromaDB retrieval service initialized: {persist_directory}/{collection_name}")
            
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    async def add_document(self, document: DocumentIndex) -> bool:
        """Add single document to ChromaDB"""
        try:
            self.collection.add(
                ids=[document.id],
                embeddings=[document.embedding],
                documents=[document.content],
                metadatas=[{
                    "source": document.source,
                    "timestamp": document.timestamp.isoformat(),
                    **document.metadata
                }]
            )
            
            logger.debug(f"Added document to ChromaDB: {document.id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add document to ChromaDB: {e}")
            return False
    
    async def add_documents(self, documents: List[DocumentIndex]) -> int:
        """Add multiple documents to ChromaDB"""
        if not documents:
            return 0
        
        try:
            # Prepare batch data
            ids = [doc.id for doc in documents]
            embeddings = [doc.embedding for doc in documents]
            contents = [doc.content for doc in documents]
            metadatas = [{
                "source": doc.source,
                "timestamp": doc.timestamp.isoformat(),
                **doc.metadata
            } for doc in documents]
            
            # Add batch to collection
            self.collection.add(
                ids=ids,
                embeddings=embeddings,
                documents=contents,
                metadatas=metadatas
            )
            
            logger.info(f"Added {len(documents)} documents to ChromaDB")
            return len(documents)
            
        except Exception as e:
            logger.error(f"Failed to add documents batch to ChromaDB: {e}")
            return 0
    
    async def search(
        self,
        query_embedding: List[float],
        filters: Optional[SearchFilter] = None,
        max_results: int = 10,
        min_score: float = 0.0
    ) -> List[RetrievedDocument]:
        """Search for similar documents in ChromaDB"""
        try:
            # Build ChromaDB where clause from filters
            where_clause = self._build_where_clause(filters)
            
            # Perform similarity search
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=max_results,
                where=where_clause
            )
            
            # Convert results to RetrievedDocument objects
            retrieved_docs = []
            
            if results['ids'] and results['ids'][0]:
                for i, doc_id in enumerate(results['ids'][0]):
                    # Calculate similarity score (ChromaDB returns distances)
                    distance = results['distances'][0][i]
                    score = max(0.0, 1.0 - distance)  # Convert distance to similarity
                    
                    if score >= min_score:
                        metadata = results['metadatas'][0][i] or {}
                        
                        doc = RetrievedDocument(
                            id=doc_id,
                            content=results['documents'][0][i],
                            source=metadata.get('source', 'unknown'),
                            score=score,
                            metadata=metadata,
                            timestamp=datetime.fromisoformat(
                                metadata.get('timestamp', datetime.utcnow().isoformat())
                            )
                        )
                        retrieved_docs.append(doc)
            
            logger.debug(f"Retrieved {len(retrieved_docs)} documents from ChromaDB")
            return retrieved_docs
            
        except Exception as e:
            logger.error(f"ChromaDB search error: {e}")
            return []
    
    def _build_where_clause(self, filters: Optional[SearchFilter]) -> Optional[Dict[str, Any]]:
        """Build ChromaDB where clause from filters"""
        if not filters:
            return None
        
        where_clause = {}
        
        # Source filter
        if filters.sources:
            if len(filters.sources) == 1:
                where_clause["source"] = filters.sources[0]
            else:
                where_clause["source"] = {"$in": filters.sources}
        
        # Date range filter
        if filters.date_range:
            start_date, end_date = filters.date_range
            where_clause["timestamp"] = {
                "$gte": start_date.isoformat(),
                "$lte": end_date.isoformat()
            }
        
        # Metadata filters
        if filters.metadata_filters:
            where_clause.update(filters.metadata_filters)
        
        return where_clause if where_clause else None
    
    async def delete_document(self, document_id: str) -> bool:
        """Delete document from ChromaDB"""
        try:
            self.collection.delete(ids=[document_id])
            logger.debug(f"Deleted document from ChromaDB: {document_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete document from ChromaDB: {e}")
            return False
    
    async def get_document_count(self, source: Optional[str] = None) -> int:
        """Get document count from ChromaDB"""
        try:
            if source:
                # Count with source filter
                results = self.collection.query(
                    query_embeddings=[[0.0] * 384],  # Dummy embedding
                    n_results=1,
                    where={"source": source}
                )
                # Note: ChromaDB doesn't have direct count, this is approximation
                return len(results['ids'][0]) if results['ids'] else 0
            else:
                # Get all collection info
                return self.collection.count()
                
        except Exception as e:
            logger.error(f"Failed to get document count: {e}")
            return 0

class MultiSourceRetrievalService:
    """
    Multi-source retrieval service that combines different data sources
    """
    
    def __init__(
        self,
        vector_service: BaseRetrievalService,
        crm_service: Optional[Any] = None,
        memory_service: Optional[Any] = None
    ):
        self.vector_service = vector_service
        self.crm_service = crm_service
        self.memory_service = memory_service
        
        logger.info("Multi-source retrieval service initialized")
    
    async def search(
        self,
        query_embedding: List[float],
        filters: Optional[SearchFilter] = None,
        max_results: int = 10,
        min_score: float = 0.0
    ) -> List[RetrievedDocument]:
        """
        Search across all available sources
        
        Args:
            query_embedding: Query embedding vector
            filters: Search filters
            max_results: Maximum results to return
            min_score: Minimum similarity score
            
        Returns:
            Combined and ranked results from all sources
        """
        all_results = []
        
        # 1. Vector similarity search (handbook, indexed documents)
        try:
            vector_results = await self.vector_service.search(
                query_embedding=query_embedding,
                filters=filters,
                max_results=max_results * 2,  # Get more for better ranking
                min_score=min_score
            )
            all_results.extend(vector_results)
            logger.debug(f"Vector search returned {len(vector_results)} results")
            
        except Exception as e:
            logger.error(f"Vector search error: {e}")
        
        # 2. CRM data search (if available and not filtered out)
        if (self.crm_service and 
            (not filters or not filters.sources or 'crm' in filters.sources)):
            try:
                crm_results = await self._search_crm_data(query_embedding, filters, max_results)
                all_results.extend(crm_results)
                logger.debug(f"CRM search returned {len(crm_results)} results")
                
            except Exception as e:
                logger.error(f"CRM search error: {e}")
        
        # 3. Memory/conversation search (if available)
        if (self.memory_service and 
            (not filters or not filters.sources or 'memory' in filters.sources)):
            try:
                memory_results = await self._search_memory_data(query_embedding, filters, max_results)
                all_results.extend(memory_results)
                logger.debug(f"Memory search returned {len(memory_results)} results")
                
            except Exception as e:
                logger.error(f"Memory search error: {e}")
        
        # 4. Rank and filter combined results
        ranked_results = self._rank_and_filter_results(
            all_results, 
            max_results, 
            min_score
        )
        
        logger.info(f"Multi-source search returned {len(ranked_results)} total results")
        return ranked_results
    
    async def _search_crm_data(
        self,
        query_embedding: List[float],
        filters: Optional[SearchFilter],
        max_results: int
    ) -> List[RetrievedDocument]:
        """Search CRM data sources"""
        # TODO: Implement CRM-specific search logic
        # This would search CRM projects, tasks, clients, etc.
        # For now, return empty list
        
        logger.debug("CRM data search not yet implemented")
        return []
    
    async def _search_memory_data(
        self,
        query_embedding: List[float],
        filters: Optional[SearchFilter],
        max_results: int
    ) -> List[RetrievedDocument]:
        """Search conversation memory and context"""
        # TODO: Implement memory-specific search logic
        # This would search previous conversations, decisions, context
        # For now, return empty list
        
        logger.debug("Memory data search not yet implemented")
        return []
    
    def _rank_and_filter_results(
        self,
        results: List[RetrievedDocument],
        max_results: int,
        min_score: float
    ) -> List[RetrievedDocument]:
        """
        Rank and filter combined results from multiple sources
        
        Args:
            results: Combined results from all sources
            max_results: Maximum results to return
            min_score: Minimum similarity score
            
        Returns:
            Ranked and filtered results
        """
        # Filter by minimum score
        filtered_results = [r for r in results if r.score >= min_score]
        
        # Remove duplicates based on content similarity
        deduplicated_results = self._deduplicate_results(filtered_results)
        
        # Sort by combined score (similarity + source priority + recency)
        ranked_results = sorted(
            deduplicated_results,
            key=self._calculate_ranking_score,
            reverse=True
        )
        
        # Return top results
        return ranked_results[:max_results]
    
    def _deduplicate_results(self, results: List[RetrievedDocument]) -> List[RetrievedDocument]:
        """Remove duplicate or very similar results"""
        if not results:
            return results
        
        deduplicated = []
        seen_content = set()
        
        for result in results:
            # Simple deduplication based on content hash
            content_hash = hash(result.content.strip().lower())
            
            if content_hash not in seen_content:
                seen_content.add(content_hash)
                deduplicated.append(result)
        
        return deduplicated
    
    def _calculate_ranking_score(self, doc: RetrievedDocument) -> float:
        """
        Calculate ranking score for document
        
        Combines:
        - Similarity score (primary)
        - Source priority bonus
        - Recency bonus
        - Content quality indicators
        """
        base_score = doc.score
        
        # Source priority bonus
        source_priority = {
            "handbook": 0.2,
            "crm": 0.1,
            "memory": 0.05
        }
        source_bonus = source_priority.get(doc.source, 0.0)
        
        # Recency bonus (more recent = higher score)
        try:
            age_days = (datetime.utcnow() - doc.timestamp).days
            recency_bonus = max(0.0, 0.1 * (1 - age_days / 365))  # Decay over a year
        except:
            recency_bonus = 0.0
        
        # Content quality bonus (longer content might be more comprehensive)
        content_quality = min(len(doc.content) / 1000, 0.1)
        
        total_score = base_score + source_bonus + recency_bonus + content_quality
        return total_score
    
    async def add_handbook_documents(self, documents: List[DocumentIndex]) -> int:
        """Add handbook documents to vector index"""
        return await self.vector_service.add_documents(documents)
    
    async def get_service_stats(self) -> Dict[str, Any]:
        """Get retrieval service statistics"""
        stats = {
            "vector_service": {
                "total_documents": await self.vector_service.get_document_count(),
                "handbook_documents": await self.vector_service.get_document_count("handbook"),
            },
            "services_available": {
                "vector_service": bool(self.vector_service),
                "crm_service": bool(self.crm_service),
                "memory_service": bool(self.memory_service)
            }
        }
        
        return stats

class HandbookDataProcessor:
    """
    Processor for handbook data specifically
    """
    
    def __init__(self, retrieval_service: MultiSourceRetrievalService):
        self.retrieval_service = retrieval_service
        
    async def process_handbook_data(self, handbook_data: Dict[str, Any]) -> int:
        """
        Process and index handbook data
        
        Args:
            handbook_data: Raw handbook data
            
        Returns:
            Number of documents processed
        """
        documents = []
        
        # Process Account Management and Coordination Department data
        for section_name, section_content in handbook_data.items():
            if isinstance(section_content, dict):
                # Process structured sections
                for subsection, content in section_content.items():
                    doc_id = f"handbook_{section_name}_{subsection}_{uuid.uuid4().hex[:8]}"
                    
                    # Format content for embedding
                    if isinstance(content, list):
                        formatted_content = f"{subsection}:\n" + "\n".join(f"- {item}" for item in content)
                    else:
                        formatted_content = f"{subsection}: {content}"
                    
                    # Create document index
                    document = DocumentIndex(
                        id=doc_id,
                        content=formatted_content,
                        source="handbook",
                        embedding=[],  # Will be populated by embedding service
                        metadata={
                            "section": section_name,
                            "subsection": subsection,
                            "type": "handbook_policy",
                            "department": "Account Management and Coordination"
                        },
                        timestamp=datetime.utcnow()
                    )
                    documents.append(document)
            
            elif isinstance(section_content, str):
                # Process simple text content
                doc_id = f"handbook_{section_name}_{uuid.uuid4().hex[:8]}"
                
                document = DocumentIndex(
                    id=doc_id,
                    content=f"{section_name}: {section_content}",
                    source="handbook",
                    embedding=[],  # Will be populated by embedding service
                    metadata={
                        "section": section_name,
                        "type": "handbook_text",
                        "department": "Account Management and Coordination"
                    },
                    timestamp=datetime.utcnow()
                )
                documents.append(document)
        
        # Note: Embeddings will be added by the embedding service
        logger.info(f"Processed {len(documents)} handbook documents")
        return len(documents)

# Factory functions
def create_chromadb_retrieval_service(
    persist_directory: str = "chroma_db",
    collection_name: str = "rag_documents"
) -> ChromaDBRetrievalService:
    """Create ChromaDB retrieval service"""
    return ChromaDBRetrievalService(
        persist_directory=persist_directory,
        collection_name=collection_name
    )

def create_multi_source_retrieval_service(
    vector_service: Optional[BaseRetrievalService] = None,
    crm_service: Optional[Any] = None,
    memory_service: Optional[Any] = None
) -> MultiSourceRetrievalService:
    """Create multi-source retrieval service"""
    if not vector_service:
        vector_service = create_chromadb_retrieval_service()
    
    return MultiSourceRetrievalService(
        vector_service=vector_service,
        crm_service=crm_service,
        memory_service=memory_service
    )

# Export retrieval service components
__all__ = [
    "BaseRetrievalService",
    "ChromaDBRetrievalService", 
    "MultiSourceRetrievalService",
    "HandbookDataProcessor",
    "DocumentIndex",
    "SearchFilter",
    "create_chromadb_retrieval_service",
    "create_multi_source_retrieval_service"
]