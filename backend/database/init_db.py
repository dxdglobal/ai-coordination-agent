#!/usr/bin/env python3
"""
Database in            print(f"📊 Created tables: {', '.join(tables)}")tialization script            print("📊 Creating sample data...")for AI Coordination Agent
This script will test the database connection and create all tables
ENHANCED VERSION - Includes Task 1.1 completion features
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app, db
from services.crm_sync_service import crm_sync_service
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def init_database():
    """Initialize the database and create all tables"""
    try:
        app = create_app()
        
        with app.app_context():
            # Test database connection
            print("🔍 Testing AI database connection...")
            with db.engine.connect() as connection:
                connection.execute(db.text("SELECT 1"))
            print("✅ AI database connection successful!")
            
            # Create all tables
            print("📋 Creating database tables...")
            db.create_all()
            print("✅ All tables created successfully!")
            
            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"� Created tables: {', '.join(tables)}")
            
            # Verify Task 1.1 completion requirements
            required_tables = [
                'users', 'projects', 'tasks', 'comments', 
                'notifications', 'memory_embeddings', 'employees',
                'conversation_history', 'prompt_templates'
            ]
            
            missing_tables = [table for table in required_tables if table not in tables]
            
            if missing_tables:
                print(f"⚠️  Missing tables: {', '.join(missing_tables)}")
                return False
            else:
                print("✅ All Task 1.1 required tables present!")
            
            return True
            
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        logger.error(f"Database init error: {e}")
        return False

def test_crm_connection():
    """Test CRM database connection for Task 1.1 completion"""
    try:
        print("🔍 Testing CRM database connection...")
        
        # Test CRM connection
        crm_conn = crm_sync_service.get_crm_connection()
        cursor = crm_conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tblstaff WHERE active = 1")
        staff_count = cursor.fetchone()[0]
        cursor.close()
        crm_conn.close()
        
        print(f"✅ CRM connection successful! Found {staff_count} active staff members")
        return True
        
    except Exception as e:
        print(f"⚠️  CRM connection failed: {str(e)}")
        logger.warning(f"CRM connection error: {e}")
        return False

def test_vector_database():
    """Test vector database functionality"""
    try:
        print("🔍 Testing vector database...")
        
        from services.vector_service import VectorDatabaseService
        vector_service = VectorDatabaseService()
        
        if hasattr(vector_service, 'client') and vector_service.client is not None:
            print("✅ ChromaDB vector database ready!")
            return True
        else:
            print("⚠️  ChromaDB not available (install chromadb package)")
            return False
            
    except Exception as e:
        print(f"⚠️  Vector database test failed: {str(e)}")
        logger.warning(f"Vector DB error: {e}")
        return False

def create_sample_data():
    """Create sample data for testing"""
    try:
        app = create_app()
        
        with app.app_context():
            from models.models import User, Project, Task, TaskStatus, Priority
            
            # Check if sample data already exists
            if User.query.count() > 0:
                print("📊 Sample data already exists, skipping creation")
                return True
            
            print("� Creating sample data...")
            
            # Create sample user
            sample_user = User(
                crm_user_id=999,
                email='ai.agent@dxdglobal.com',
                name='AI Agent Test User',
                role='admin',
                is_active=True
            )
            db.session.add(sample_user)
            
            # Create sample project
            sample_project = Project(
                name='AI Coordination Agent Development',
                description='Main project for AI coordination system development',
                status=TaskStatus.IN_PROGRESS
            )
            db.session.add(sample_project)
            db.session.flush()  # Get the ID
            
            # Create sample tasks
            sample_tasks = [
                Task(
                    title='Database Schema Design',
                    description='Complete Task 1.1 - Database Design & Setup',
                    status=TaskStatus.DONE,
                    priority=Priority.HIGH,
                    project_id=sample_project.id
                ),
                Task(
                    title='CRM Integration',
                    description='Connect to existing CRM database for data sync',
                    status=TaskStatus.DONE,
                    priority=Priority.HIGH,
                    project_id=sample_project.id
                ),
                Task(
                    title='Vector Database Setup',
                    description='Enable semantic search with embeddings',
                    status=TaskStatus.DONE,
                    priority=Priority.MEDIUM,
                    project_id=sample_project.id
                )
            ]
            
            for task in sample_tasks:
                db.session.add(task)
            
            db.session.commit()
            print("✅ Sample data created successfully!")
            return True
            
    except Exception as e:
        print(f"⚠️  Sample data creation failed: {str(e)}")
        logger.warning(f"Sample data error: {e}")
        return False

def verify_task_1_1_completion():
    """Verify Task 1.1 requirements are met"""
    print("\n" + "="*60)
    print("🎯 TASK 1.1 COMPLETION VERIFICATION")
    print("="*60)
    
    checks = {
        'ai_database': False,
        'crm_connection': False,
        'vector_database': False,
        'required_tables': False,
        'sample_data': False
    }
    
    # 1. AI Memory Database Schema
    checks['ai_database'] = init_database()
    
    # 2. CRM Database Connection
    checks['crm_connection'] = test_crm_connection()
    
    # 3. Vector Database (Semantic Search)
    checks['vector_database'] = test_vector_database()
    
    # 4. Create sample data
    checks['sample_data'] = create_sample_data()
    
    # Summary
    completed_checks = sum(checks.values())
    total_checks = len(checks)
    completion_percentage = (completed_checks / total_checks) * 100
    
    print(f"\n📊 TASK 1.1 COMPLETION STATUS:")
    print(f"   ✅ Completed: {completed_checks}/{total_checks} ({completion_percentage:.1f}%)")
    
    for check_name, status in checks.items():
        status_icon = "✅" if status else "❌"
        print(f"   {status_icon} {check_name.replace('_', ' ').title()}")
    
    if completion_percentage >= 80:
        print(f"\n🎉 TASK 1.1 STATUS: {'COMPLETE' if completion_percentage == 100 else 'MOSTLY COMPLETE'}")
        print("   ✅ AI memory database schema created")
        print("   ✅ Tables for users, projects, tasks, comments, notifications")
        print("   ✅ Memory embeddings for semantic search")
        print("   ✅ CRM database connection enabled")
        
        if checks['vector_database']:
            print("   ✅ ChromaDB/Vector database ready")
        else:
            print("   ⚠️  Vector database optional (ChromaDB not installed)")
        
        return True
    else:
        print(f"\n❌ TASK 1.1 STATUS: INCOMPLETE ({completion_percentage:.1f}%)")
        print("   Please resolve the failed checks above")
        return False

if __name__ == "__main__":
    print("🚀 Initializing AI Coordination Agent Database...")
    print("🎯 Task 1.1 - Database Design & Setup")
    print("=" * 50)
    
    success = verify_task_1_1_completion()
    
    if success:
        print("=" * 50)
        print("✅ Task 1.1 Database initialization completed successfully!")
        print("🎉 Ready for AI Coordination Agent operations!")
    else:
        print("=" * 50)
        print("❌ Task 1.1 initialization incomplete!")
        print("💡 Check the errors above and retry")
        print("Please check your database configuration and try again.")
        sys.exit(1)