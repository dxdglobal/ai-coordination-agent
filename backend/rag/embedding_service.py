"""
Embedding Service - Task 1.4
============================

Comprehensive embedding service for the RAG pipeline.
Supports multiple embedding models and efficient vector operations.

Features:
- Multiple embedding providers (OpenAI, SentenceTransformers, HuggingFace)
- Batch embedding processing
- Embedding caching and optimization
- Text preprocessing and chunking
- Vector similarity calculations

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union, Tuple
from abc import ABC, abstractmethod
import asyncio
import hashlib
import pickle
from dataclasses import dataclass
from datetime import datetime
import numpy as np

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False

try:
    import chromadb
    CHROMADB_AVAILABLE = True
except ImportError:
    CHROMADB_AVAILABLE = False

from core.logging_config import get_logger

# Configure logging
logger = get_logger(__name__)

@dataclass
class EmbeddingResult:
    """Embedding result structure"""
    text: str
    embedding: List[float]
    model: str
    dimensions: int
    processing_time: float
    metadata: Dict[str, Any]

@dataclass
class TextChunk:
    """Text chunk for embedding"""
    id: str
    text: str
    source: str
    metadata: Dict[str, Any]
    start_pos: int = 0
    end_pos: int = 0

class BaseEmbeddingService(ABC):
    """Abstract base class for embedding services"""
    
    @abstractmethod
    async def embed_text(self, text: str) -> List[float]:
        """Embed single text"""
        pass
    
    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed batch of texts"""
        pass
    
    @abstractmethod
    def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        pass
    
    @abstractmethod
    def get_model_name(self) -> str:
        """Get model name"""
        pass

class OpenAIEmbeddingService(BaseEmbeddingService):
    """OpenAI embeddings service"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "text-embedding-ada-002",
        batch_size: int = 100
    ):
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI package not available. Install with: pip install openai")
        
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key required")
        
        self.model = model
        self.batch_size = batch_size
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Model dimensions mapping
        self.model_dimensions = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072
        }
        
        logger.info(f"OpenAI embedding service initialized with model: {model}")
    
    async def embed_text(self, text: str) -> List[float]:
        """Embed single text using OpenAI"""
        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )
            
            embedding = response.data[0].embedding
            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding
            
        except Exception as e:
            logger.error(f"OpenAI embedding error: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed batch of texts using OpenAI"""
        embeddings = []
        
        # Process in batches to respect API limits
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            
            try:
                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )
                
                batch_embeddings = [item.embedding for item in response.data]
                embeddings.extend(batch_embeddings)
                
                logger.debug(f"Generated embeddings for batch {i//self.batch_size + 1}")
                
            except Exception as e:
                logger.error(f"OpenAI batch embedding error: {e}")
                raise
        
        return embeddings
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        return self.model_dimensions.get(self.model, 1536)
    
    def get_model_name(self) -> str:
        """Get model name"""
        return self.model

class SentenceTransformerEmbeddingService(BaseEmbeddingService):
    """SentenceTransformers embedding service"""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        device: Optional[str] = None,
        batch_size: int = 32
    ):
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError("SentenceTransformers package not available. Install with: pip install sentence-transformers")
        
        self.model_name = model_name
        self.batch_size = batch_size
        
        try:
            self.model = SentenceTransformer(model_name, device=device)
            logger.info(f"SentenceTransformers embedding service initialized with model: {model_name}")
        except Exception as e:
            logger.error(f"Failed to load SentenceTransformers model: {e}")
            raise
    
    async def embed_text(self, text: str) -> List[float]:
        """Embed single text using SentenceTransformers"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None, lambda: self.model.encode([text], convert_to_numpy=True)[0]
            )
            
            logger.debug(f"Generated embedding for text: {text[:50]}...")
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"SentenceTransformers embedding error: {e}")
            raise
    
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Embed batch of texts using SentenceTransformers"""
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None, lambda: self.model.encode(texts, convert_to_numpy=True, batch_size=self.batch_size)
            )
            
            logger.debug(f"Generated embeddings for batch of {len(texts)} texts")
            return embeddings.tolist()
            
        except Exception as e:
            logger.error(f"SentenceTransformers batch embedding error: {e}")
            raise
    
    def get_dimensions(self) -> int:
        """Get embedding dimensions"""
        return self.model.get_sentence_embedding_dimension()
    
    def get_model_name(self) -> str:
        """Get model name"""
        return self.model_name

class EmbeddingService:
    """
    Main embedding service with caching and preprocessing
    """
    
    def __init__(
        self,
        provider: BaseEmbeddingService,
        cache_dir: Optional[str] = None,
        enable_caching: bool = True,
        chunk_size: int = 512,
        chunk_overlap: int = 50
    ):
        self.provider = provider
        self.enable_caching = enable_caching
        self.cache_dir = cache_dir or "cache/embeddings"
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        
        # Initialize cache
        if enable_caching:
            os.makedirs(self.cache_dir, exist_ok=True)
        
        logger.info(f"Embedding service initialized with {provider.get_model_name()}")
    
    async def embed_query(self, query: str) -> List[float]:
        """
        Embed a search query
        
        Args:
            query: Query text
            
        Returns:
            Query embedding
        """
        # Preprocess query
        processed_query = self._preprocess_text(query)
        
        # Check cache first
        if self.enable_caching:
            cached_embedding = await self._get_cached_embedding(processed_query)
            if cached_embedding:
                logger.debug("Using cached embedding for query")
                return cached_embedding
        
        # Generate embedding
        embedding = await self.provider.embed_text(processed_query)
        
        # Cache embedding
        if self.enable_caching:
            await self._cache_embedding(processed_query, embedding)
        
        return embedding
    
    async def embed_document(self, text: str, source: str = "unknown") -> List[EmbeddingResult]:
        """
        Embed a document with chunking
        
        Args:
            text: Document text
            source: Document source
            
        Returns:
            List of embedding results for chunks
        """
        # Split text into chunks
        chunks = self._chunk_text(text, source)
        
        # Embed chunks
        embedding_results = []
        chunk_texts = [chunk.text for chunk in chunks]
        
        # Batch embed for efficiency
        embeddings = await self.provider.embed_batch(chunk_texts)
        
        for chunk, embedding in zip(chunks, embeddings):
            result = EmbeddingResult(
                text=chunk.text,
                embedding=embedding,
                model=self.provider.get_model_name(),
                dimensions=self.provider.get_dimensions(),
                processing_time=0.0,  # TODO: Add timing
                metadata={
                    "chunk_id": chunk.id,
                    "source": chunk.source,
                    "start_pos": chunk.start_pos,
                    "end_pos": chunk.end_pos,
                    **chunk.metadata
                }
            )
            embedding_results.append(result)
        
        logger.info(f"Embedded document into {len(embedding_results)} chunks")
        return embedding_results
    
    async def embed_handbook_data(self, handbook_data: Dict[str, Any]) -> List[EmbeddingResult]:
        """
        Embed handbook data specifically
        
        Args:
            handbook_data: Structured handbook data
            
        Returns:
            List of embedding results
        """
        embedding_results = []
        
        # Process different sections of handbook data
        for section_name, section_content in handbook_data.items():
            if isinstance(section_content, str):
                # Simple text content
                results = await self.embed_document(
                    text=section_content,
                    source=f"handbook_{section_name}"
                )
                embedding_results.extend(results)
                
            elif isinstance(section_content, dict):
                # Structured content - flatten and embed
                flattened_text = self._flatten_dict_content(section_content)
                results = await self.embed_document(
                    text=flattened_text,
                    source=f"handbook_{section_name}"
                )
                embedding_results.extend(results)
                
            elif isinstance(section_content, list):
                # List content - join and embed
                joined_text = "\n".join(str(item) for item in section_content)
                results = await self.embed_document(
                    text=joined_text,
                    source=f"handbook_{section_name}"
                )
                embedding_results.extend(results)
        
        logger.info(f"Embedded handbook data: {len(embedding_results)} chunks from {len(handbook_data)} sections")
        return embedding_results
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess text for embedding"""
        # Clean and normalize text
        text = text.strip()
        text = " ".join(text.split())  # Normalize whitespace
        
        # Truncate if too long for single embedding
        max_length = 8000  # Conservative limit for most models
        if len(text) > max_length:
            text = text[:max_length]
            logger.warning(f"Text truncated to {max_length} characters")
        
        return text
    
    def _chunk_text(self, text: str, source: str) -> List[TextChunk]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            source: Source identifier
            
        Returns:
            List of text chunks
        """
        chunks = []
        text = self._preprocess_text(text)
        
        # Simple word-based chunking
        words = text.split()
        
        for i in range(0, len(words), self.chunk_size - self.chunk_overlap):
            chunk_words = words[i:i + self.chunk_size]
            chunk_text = " ".join(chunk_words)
            
            chunk_id = f"{source}_{i//self.chunk_size}_{hashlib.md5(chunk_text.encode()).hexdigest()[:8]}"
            
            chunk = TextChunk(
                id=chunk_id,
                text=chunk_text,
                source=source,
                metadata={"word_count": len(chunk_words)},
                start_pos=i,
                end_pos=i + len(chunk_words)
            )
            chunks.append(chunk)
        
        return chunks
    
    def _flatten_dict_content(self, data: Dict[str, Any], prefix: str = "") -> str:
        """Flatten dictionary content into text"""
        parts = []
        
        for key, value in data.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                parts.append(self._flatten_dict_content(value, full_key))
            elif isinstance(value, list):
                parts.append(f"{full_key}: {'; '.join(str(item) for item in value)}")
            else:
                parts.append(f"{full_key}: {value}")
        
        return "\n".join(parts)
    
    async def _get_cached_embedding(self, text: str) -> Optional[List[float]]:
        """Get cached embedding if available"""
        if not self.enable_caching:
            return None
        
        # Create cache key
        cache_key = hashlib.md5(f"{text}_{self.provider.get_model_name()}".encode()).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        try:
            if os.path.exists(cache_path):
                with open(cache_path, "rb") as f:
                    cached_data = pickle.load(f)
                    return cached_data["embedding"]
        except Exception as e:
            logger.warning(f"Failed to load cached embedding: {e}")
        
        return None
    
    async def _cache_embedding(self, text: str, embedding: List[float]):
        """Cache embedding for future use"""
        if not self.enable_caching:
            return
        
        # Create cache key
        cache_key = hashlib.md5(f"{text}_{self.provider.get_model_name()}".encode()).hexdigest()
        cache_path = os.path.join(self.cache_dir, f"{cache_key}.pkl")
        
        try:
            cache_data = {
                "text": text,
                "embedding": embedding,
                "model": self.provider.get_model_name(),
                "timestamp": datetime.utcnow().isoformat()
            }
            
            with open(cache_path, "wb") as f:
                pickle.dump(cache_data, f)
                
        except Exception as e:
            logger.warning(f"Failed to cache embedding: {e}")
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """
        Calculate cosine similarity between embeddings
        
        Args:
            embedding1: First embedding
            embedding2: Second embedding
            
        Returns:
            Similarity score between -1 and 1
        """
        try:
            # Convert to numpy arrays
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # Calculate cosine similarity
            dot_product = np.dot(vec1, vec2)
            norms = np.linalg.norm(vec1) * np.linalg.norm(vec2)
            
            if norms == 0:
                return 0.0
            
            similarity = dot_product / norms
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Similarity calculation error: {e}")
            return 0.0
    
    def get_service_info(self) -> Dict[str, Any]:
        """Get embedding service information"""
        return {
            "provider": self.provider.get_model_name(),
            "dimensions": self.provider.get_dimensions(),
            "caching_enabled": self.enable_caching,
            "cache_dir": self.cache_dir,
            "chunk_size": self.chunk_size,
            "chunk_overlap": self.chunk_overlap
        }

# Factory functions
def create_openai_embedding_service(
    api_key: Optional[str] = None,
    model: str = "text-embedding-ada-002"
) -> EmbeddingService:
    """Create OpenAI embedding service"""
    provider = OpenAIEmbeddingService(api_key=api_key, model=model)
    return EmbeddingService(provider=provider)

def create_sentence_transformer_embedding_service(
    model_name: str = "all-MiniLM-L6-v2"
) -> EmbeddingService:
    """Create SentenceTransformers embedding service"""
    provider = SentenceTransformerEmbeddingService(model_name=model_name)
    return EmbeddingService(provider=provider)

def create_default_embedding_service() -> EmbeddingService:
    """Create default embedding service based on available packages"""
    if OPENAI_AVAILABLE and os.getenv("OPENAI_API_KEY"):
        logger.info("Using OpenAI embedding service")
        return create_openai_embedding_service()
    elif SENTENCE_TRANSFORMERS_AVAILABLE:
        logger.info("Using SentenceTransformers embedding service")
        return create_sentence_transformer_embedding_service()
    else:
        raise RuntimeError(
            "No embedding service available. Install either:\n"
            "- OpenAI: pip install openai (and set OPENAI_API_KEY)\n"
            "- SentenceTransformers: pip install sentence-transformers"
        )

# Export embedding service components
__all__ = [
    "EmbeddingService",
    "BaseEmbeddingService",
    "OpenAIEmbeddingService",
    "SentenceTransformerEmbeddingService",
    "EmbeddingResult",
    "TextChunk",
    "create_openai_embedding_service",
    "create_sentence_transformer_embedding_service",
    "create_default_embedding_service"
]