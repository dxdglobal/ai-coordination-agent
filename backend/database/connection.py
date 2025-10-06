"""
Database Connection Management - Task 1.3
==========================================

SQLAlchemy database connection and session management for FastAPI backend.
Supports multiple database types and integrates with existing Task 1.1 setup.

Features:
- Multi-database support (PostgreSQL, MySQL, SQLite)
- Connection pooling and session management
- Async and sync session support
- Database migration utilities
- Health checks and monitoring

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import os
import logging
from typing import Generator, Optional, Dict, Any
from contextlib import contextmanager, asynccontextmanager
from sqlalchemy import create_engine, MetaData, inspect, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool, QueuePool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError
import asyncio
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)

# Database configuration
class DatabaseConfig:
    """Database configuration settings"""
    
    def __init__(self):
        # Default to SQLite for development
        self.DATABASE_URL = os.getenv(
            "DATABASE_URL", 
            "sqlite:///./ai_coordination_agent.db"
        )
        
        # Database type detection
        if self.DATABASE_URL.startswith("postgresql"):
            self.DB_TYPE = "postgresql"
            self.POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
            self.MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
            self.POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        elif self.DATABASE_URL.startswith("mysql"):
            self.DB_TYPE = "mysql"
            self.POOL_SIZE = int(os.getenv("DB_POOL_SIZE", "10"))
            self.MAX_OVERFLOW = int(os.getenv("DB_MAX_OVERFLOW", "20"))
            self.POOL_TIMEOUT = int(os.getenv("DB_POOL_TIMEOUT", "30"))
        else:
            self.DB_TYPE = "sqlite"
            self.POOL_SIZE = 1
            self.MAX_OVERFLOW = 0
            self.POOL_TIMEOUT = 10
        
        # Connection parameters
        self.ECHO_SQL = os.getenv("ECHO_SQL", "false").lower() == "true"
        self.POOL_RECYCLE = int(os.getenv("DB_POOL_RECYCLE", "3600"))  # 1 hour
        self.POOL_PRE_PING = os.getenv("DB_POOL_PRE_PING", "true").lower() == "true"

# Global database configuration
db_config = DatabaseConfig()

# Create base class for models
Base = declarative_base()
metadata = MetaData()

class DatabaseManager:
    """Database connection and session manager"""
    
    def __init__(self):
        self.config = db_config
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        self._initialized = False
    
    def create_engine(self) -> Engine:
        """Create database engine with appropriate configuration"""
        try:
            if self.config.DB_TYPE == "sqlite":
                # SQLite configuration
                engine = create_engine(
                    self.config.DATABASE_URL,
                    echo=self.config.ECHO_SQL,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 20
                    }
                )
            else:
                # PostgreSQL/MySQL configuration
                engine = create_engine(
                    self.config.DATABASE_URL,
                    echo=self.config.ECHO_SQL,
                    poolclass=QueuePool,
                    pool_size=self.config.POOL_SIZE,
                    max_overflow=self.config.MAX_OVERFLOW,
                    pool_timeout=self.config.POOL_TIMEOUT,
                    pool_recycle=self.config.POOL_RECYCLE,
                    pool_pre_ping=self.config.POOL_PRE_PING
                )
            
            logger.info(f"Database engine created for {self.config.DB_TYPE}")
            return engine
            
        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            raise
    
    def initialize(self):
        """Initialize database connection and session"""
        if self._initialized:
            return
        
        try:
            self.engine = self.create_engine()
            
            # Create session factory
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # Test connection
            self.test_connection()
            
            self._initialized = True
            logger.info("Database manager initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database manager: {e}")
            raise
    
    async def initialize_async(self):
        """Async initialization for FastAPI lifespan"""
        return self.initialize()
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            with self.engine.connect() as connection:
                result = connection.execute(text("SELECT 1"))
                result.fetchone()
            logger.info("Database connection test successful")
            return True
        except Exception as e:
            logger.error(f"Database connection test failed: {e}")
            return False
    
    def create_tables(self):
        """Create all database tables"""
        try:
            # Import models to ensure they're registered
            from database.models import Base
            
            # Create tables
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created/verified")
            
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            raise
    
    async def create_tables_async(self):
        """Async table creation for FastAPI lifespan"""
        return self.create_tables()
    
    def get_session(self) -> Session:
        """Get database session"""
        if not self._initialized:
            self.initialize()
        
        return self.SessionLocal()
    
    @contextmanager
    def session_scope(self):
        """Provide a transactional scope around a series of operations"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def close(self):
        """Close database connections"""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connections closed")
    
    async def close_async(self):
        """Async close for FastAPI lifespan"""
        return self.close()
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get database information and statistics"""
        try:
            with self.engine.connect() as connection:
                # Get database version and info
                if self.config.DB_TYPE == "postgresql":
                    version_query = "SELECT version()"
                elif self.config.DB_TYPE == "mysql":
                    version_query = "SELECT VERSION()"
                else:
                    version_query = "SELECT sqlite_version()"
                
                version_result = connection.execute(text(version_query))
                version = version_result.fetchone()[0]
                
                # Get table count
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()
                
                return {
                    "database_type": self.config.DB_TYPE,
                    "database_url": self.config.DATABASE_URL.split("@")[-1] if "@" in self.config.DATABASE_URL else self.config.DATABASE_URL,
                    "version": version,
                    "table_count": len(tables),
                    "tables": tables,
                    "pool_size": self.config.POOL_SIZE,
                    "pool_status": {
                        "size": self.engine.pool.size() if hasattr(self.engine.pool, 'size') else None,
                        "checked_in": self.engine.pool.checkedin() if hasattr(self.engine.pool, 'checkedin') else None,
                        "checked_out": self.engine.pool.checkedout() if hasattr(self.engine.pool, 'checkedout') else None,
                    }
                }
                
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}

# Global database manager instance
db_manager = DatabaseManager()

# Dependency for FastAPI routes
def get_database_session() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session.
    
    Usage:
        @app.get("/items/")
        def read_items(db: Session = Depends(get_database_session)):
            return db.query(Item).all()
    """
    session = db_manager.get_session()
    try:
        yield session
    finally:
        session.close()

# Alternative dependency with automatic transaction handling
def get_database_session_with_transaction() -> Generator[Session, None, None]:
    """
    FastAPI dependency to get database session with automatic transaction handling.
    Commits on success, rolls back on exception.
    """
    with db_manager.session_scope() as session:
        yield session

# Health check function
def check_database_health() -> Dict[str, Any]:
    """
    Check database health and return status information.
    
    Returns:
        Dict containing health status and database information
    """
    try:
        # Test connection
        is_healthy = db_manager.test_connection()
        
        if is_healthy:
            # Get database info
            db_info = db_manager.get_database_info()
            return {
                "status": "healthy",
                "timestamp": datetime.utcnow().isoformat(),
                "database": db_info
            }
        else:
            return {
                "status": "unhealthy",
                "timestamp": datetime.utcnow().isoformat(),
                "error": "Connection test failed"
            }
            
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return {
            "status": "unhealthy", 
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

# Migration utilities
class DatabaseMigration:
    """Database migration utilities"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def backup_database(self, backup_path: str) -> bool:
        """Create database backup (SQLite only)"""
        if self.db_manager.config.DB_TYPE != "sqlite":
            logger.warning("Backup only supported for SQLite databases")
            return False
        
        try:
            import shutil
            db_path = self.db_manager.config.DATABASE_URL.replace("sqlite:///", "")
            shutil.copy2(db_path, backup_path)
            logger.info(f"Database backed up to {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Database backup failed: {e}")
            return False
    
    def get_migration_status(self) -> Dict[str, Any]:
        """Get current migration status"""
        try:
            inspector = inspect(self.db_manager.engine)
            tables = inspector.get_table_names()
            
            # Check if migration table exists
            has_migration_table = "alembic_version" in tables
            
            return {
                "has_migration_table": has_migration_table,
                "total_tables": len(tables),
                "tables": tables
            }
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {"error": str(e)}

# Initialize database on module import
try:
    db_manager.initialize()
except Exception as e:
    logger.warning(f"Database initialization failed on import: {e}")
    # Continue without crashing - will retry later

# Export commonly used items
__all__ = [
    "DatabaseManager",
    "DatabaseConfig", 
    "db_manager",
    "get_database_session",
    "get_database_session_with_transaction",
    "check_database_health",
    "DatabaseMigration",
    "Base",
    "metadata"
]