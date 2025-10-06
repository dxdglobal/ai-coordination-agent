#!/usr/bin/env python3
"""
PostgreSQL pgvector Setup Script
Enables vector similarity search for AI memory embeddings
"""

import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
import logging
from typing import Optional, List, Dict, Any

logger = logging.getLogger(__name__)

class PgVectorSetup:
    """Setup and manage PostgreSQL pgvector extension"""
    
    def __init__(self, connection_string: Optional[str] = None):
        """Initialize with PostgreSQL connection"""
        self.connection_string = connection_string or self._build_connection_string()
        
    def _build_connection_string(self) -> str:
        """Build connection string from environment variables"""
        host = os.getenv('DB_HOST', 'localhost')
        port = os.getenv('DB_PORT', '5432')
        database = os.getenv('DB_NAME', 'ai_coordination_agent')
        user = os.getenv('DB_USER', 'postgres')
        password = os.getenv('DB_PASSWORD', '')
        
        return f"postgresql://{user}:{password}@{host}:{port}/{database}"
    
    def test_connection(self) -> bool:
        """Test PostgreSQL connection"""
        try:
            conn = psycopg2.connect(self.connection_string)
            conn.close()
            return True
        except Exception as e:
            logger.error(f"PostgreSQL connection failed: {e}")
            return False
    
    def setup_pgvector_extension(self) -> Dict[str, Any]:
        """Setup pgvector extension and tables"""
        try:
            conn = psycopg2.connect(self.connection_string)
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            cursor = conn.cursor()
            
            result = {
                'status': 'success',
                'operations': [],
                'errors': []
            }
            
            # 1. Create pgvector extension
            try:
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                result['operations'].append("✅ pgvector extension enabled")
            except Exception as e:
                result['errors'].append(f"Extension creation failed: {e}")
            
            # 2. Create vector embeddings table
            try:
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS vector_embeddings (
                        id SERIAL PRIMARY KEY,
                        content TEXT NOT NULL,
                        content_type VARCHAR(50) NOT NULL,
                        embedding vector(1536),  -- OpenAI ada-002 dimensions
                        source_id VARCHAR(100),
                        source_table VARCHAR(50),
                        keywords JSONB,
                        summary TEXT,
                        access_count INTEGER DEFAULT 0,
                        similarity_threshold FLOAT DEFAULT 0.8,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        last_accessed TIMESTAMP
                    );
                """)
                result['operations'].append("✅ vector_embeddings table created")
            except Exception as e:
                result['errors'].append(f"Vector table creation failed: {e}")
            
            # 3. Create indexes for performance
            indexes = [
                ("vector_embeddings_content_type_idx", "content_type"),
                ("vector_embeddings_source_idx", "source_table, source_id"),
                ("vector_embeddings_created_idx", "created_at")
            ]
            
            for index_name, columns in indexes:
                try:
                    cursor.execute(f"""
                        CREATE INDEX IF NOT EXISTS {index_name} 
                        ON vector_embeddings({columns});
                    """)
                    result['operations'].append(f"✅ Index {index_name} created")
                except Exception as e:
                    result['errors'].append(f"Index {index_name} failed: {e}")
            
            # 4. Create vector similarity index (IVFFlat)
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS vector_embeddings_embedding_idx 
                    ON vector_embeddings 
                    USING ivfflat (embedding vector_cosine_ops) 
                    WITH (lists = 100);
                """)
                result['operations'].append("✅ Vector similarity index created")
            except Exception as e:
                result['errors'].append(f"Vector index failed: {e}")
            
            # 5. Create helper functions
            self._create_vector_functions(cursor, result)
            
            cursor.close()
            conn.close()
            
            if result['errors']:
                result['status'] = 'partial_success'
            
            return result
            
        except Exception as e:
            logger.error(f"pgvector setup failed: {e}")
            return {
                'status': 'error',
                'message': str(e),
                'operations': [],
                'errors': [str(e)]
            }
    
    def _create_vector_functions(self, cursor, result: Dict):
        """Create helper functions for vector operations"""
        
        # Function to find similar content
        try:
            cursor.execute("""
                CREATE OR REPLACE FUNCTION find_similar_content(
                    query_embedding vector(1536),
                    content_type_filter VARCHAR(50) DEFAULT NULL,
                    similarity_threshold FLOAT DEFAULT 0.8,
                    max_results INTEGER DEFAULT 10
                )
                RETURNS TABLE(
                    id INTEGER,
                    content TEXT,
                    content_type VARCHAR(50),
                    similarity_score FLOAT,
                    source_id VARCHAR(100),
                    source_table VARCHAR(50)
                ) AS $$
                BEGIN
                    RETURN QUERY
                    SELECT 
                        ve.id,
                        ve.content,
                        ve.content_type,
                        1 - (ve.embedding <=> query_embedding) as similarity_score,
                        ve.source_id,
                        ve.source_table
                    FROM vector_embeddings ve
                    WHERE 
                        (content_type_filter IS NULL OR ve.content_type = content_type_filter)
                        AND (1 - (ve.embedding <=> query_embedding)) >= similarity_threshold
                    ORDER BY ve.embedding <=> query_embedding
                    LIMIT max_results;
                END;
                $$ LANGUAGE plpgsql;
            """)
            result['operations'].append("✅ find_similar_content function created")
        except Exception as e:
            result['errors'].append(f"Function creation failed: {e}")
        
        # Function to update access tracking
        try:
            cursor.execute("""
                CREATE OR REPLACE FUNCTION update_embedding_access(embedding_id INTEGER)
                RETURNS VOID AS $$
                BEGIN
                    UPDATE vector_embeddings 
                    SET 
                        access_count = access_count + 1,
                        last_accessed = CURRENT_TIMESTAMP
                    WHERE id = embedding_id;
                END;
                $$ LANGUAGE plpgsql;
            """)
            result['operations'].append("✅ update_embedding_access function created")
        except Exception as e:
            result['errors'].append(f"Access function creation failed: {e}")
    
    def insert_embedding(self, content: str, content_type: str, 
                        embedding: List[float], **metadata) -> Optional[int]:
        """Insert a new embedding into the vector database"""
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO vector_embeddings 
                (content, content_type, embedding, source_id, source_table, keywords, summary)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id;
            """, (
                content,
                content_type,
                embedding,
                metadata.get('source_id'),
                metadata.get('source_table'),
                metadata.get('keywords'),
                metadata.get('summary')
            ))
            
            embedding_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            
            return embedding_id
            
        except Exception as e:
            logger.error(f"Embedding insertion failed: {e}")
            return None
    
    def search_similar(self, query_embedding: List[float], 
                      content_type: Optional[str] = None,
                      similarity_threshold: float = 0.8,
                      max_results: int = 10) -> List[Dict[str, Any]]:
        """Search for similar content using vector similarity"""
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT * FROM find_similar_content(%s, %s, %s, %s);
            """, (query_embedding, content_type, similarity_threshold, max_results))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    'id': row[0],
                    'content': row[1],
                    'content_type': row[2],
                    'similarity_score': row[3],
                    'source_id': row[4],
                    'source_table': row[5]
                })
            
            cursor.close()
            conn.close()
            
            return results
            
        except Exception as e:
            logger.error(f"Vector search failed: {e}")
            return []
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector database"""
        try:
            conn = psycopg2.connect(self.connection_string)
            cursor = conn.cursor()
            
            # Get embedding counts by type
            cursor.execute("""
                SELECT 
                    content_type,
                    COUNT(*) as count,
                    AVG(access_count) as avg_access,
                    MAX(created_at) as latest_entry
                FROM vector_embeddings 
                GROUP BY content_type
                ORDER BY count DESC;
            """)
            
            content_stats = []
            for row in cursor.fetchall():
                content_stats.append({
                    'content_type': row[0],
                    'count': row[1],
                    'avg_access': float(row[2]) if row[2] else 0,
                    'latest_entry': row[3].isoformat() if row[3] else None
                })
            
            # Get total stats
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_embeddings,
                    SUM(access_count) as total_accesses,
                    AVG(similarity_threshold) as avg_threshold
                FROM vector_embeddings;
            """)
            
            total_stats = cursor.fetchone()
            
            cursor.close()
            conn.close()
            
            return {
                'total_embeddings': total_stats[0],
                'total_accesses': total_stats[1],
                'avg_threshold': float(total_stats[2]) if total_stats[2] else 0.8,
                'content_type_breakdown': content_stats,
                'timestamp': os.path.datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Stats retrieval failed: {e}")
            return {'error': str(e)}

# Global pgvector instance
pgvector_service = PgVectorSetup()

if __name__ == "__main__":
    print("🔧 Setting up PostgreSQL pgvector...")
    
    # Test connection
    if pgvector_service.test_connection():
        print("✅ PostgreSQL connection successful!")
        
        # Setup pgvector
        result = pgvector_service.setup_pgvector_extension()
        
        print(f"\n📊 Setup Status: {result['status']}")
        
        for operation in result['operations']:
            print(operation)
        
        if result['errors']:
            print("\n⚠️ Errors encountered:")
            for error in result['errors']:
                print(f"   - {error}")
        
        print("\n🎉 pgvector setup completed!")
        
    else:
        print("❌ PostgreSQL connection failed!")
        print("Make sure PostgreSQL is running and credentials are correct.")