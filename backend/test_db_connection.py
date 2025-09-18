#!/usr/bin/env python3
"""
Test database connection and check if tables exist
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import Config
from sqlalchemy import create_engine, text, inspect
import mysql.connector

def test_database_connection():
    """Test the database connection and check table status"""
    print("🔍 Testing Database Connection...")
    print(f"Database Type: {Config.DATABASE_TYPE}")
    print(f"Database URI: {Config.SQLALCHEMY_DATABASE_URI}")
    
    try:
        # Test basic connection
        engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
        
        with engine.connect() as connection:
            # Test basic connectivity
            result = connection.execute(text("SELECT 1 as test"))
            test_value = result.fetchone()[0]
            print(f"✅ Basic connection test: {test_value}")
            
            # Get database info
            result = connection.execute(text("SELECT DATABASE() as current_db"))
            current_db = result.fetchone()[0]
            print(f"📍 Current database: {current_db}")
            
            # Check existing tables
            inspector = inspect(engine)
            tables = inspector.get_table_names()
            print(f"📊 Total tables found: {len(tables)}")
            
            if tables:
                print("📋 Existing tables:")
                for table in tables:
                    try:
                        result = connection.execute(text(f"SELECT COUNT(*) FROM `{table}`"))
                        count = result.fetchone()[0]
                        print(f"  - {table}: {count} records")
                    except Exception as e:
                        print(f"  - {table}: Error reading ({str(e)[:50]}...)")
            else:
                print("⚠️ No tables found in database")
            
            # Test our application tables specifically
            app_tables = ['projects', 'tasks', 'comments', 'labels', 'integrations', 'ai_actions']
            print("\n🎯 Application Tables Status:")
            
            for table in app_tables:
                try:
                    result = connection.execute(text(f"SELECT COUNT(*) FROM `{table}`"))
                    count = result.fetchone()[0]
                    print(f"  ✅ {table}: {count} records")
                except Exception as e:
                    print(f"  ❌ {table}: Table doesn't exist or error ({str(e)[:50]}...)")
            
        print("\n✅ Database connection test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ Database connection failed: {str(e)}")
        return False

def test_application_models():
    """Test if our application models can be imported and used"""
    print("\n🔍 Testing Application Models...")
    
    try:
        from models.models import db, Project, Task, Comment, Label, Integration, AIAction
        print("✅ All models imported successfully")
        
        # Try to create a Flask app context to test models
        from app import create_app
        app = create_app()
        
        with app.app_context():
            try:
                # Test querying each model
                project_count = Project.query.count()
                task_count = Task.query.count()
                comment_count = Comment.query.count()
                label_count = Label.query.count()
                integration_count = Integration.query.count()
                ai_action_count = AIAction.query.count()
                
                print(f"📊 Model Query Results:")
                print(f"  - Projects: {project_count}")
                print(f"  - Tasks: {task_count}")
                print(f"  - Comments: {comment_count}")
                print(f"  - Labels: {label_count}")
                print(f"  - Integrations: {integration_count}")
                print(f"  - AI Actions: {ai_action_count}")
                
                print("✅ All models working correctly with database!")
                return True
                
            except Exception as e:
                print(f"❌ Model query failed: {str(e)}")
                return False
                
    except Exception as e:
        print(f"❌ Model import failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 60)
    print("🔍 AI COORDINATION AGENT - DATABASE CONNECTION TEST")
    print("=" * 60)
    
    # Test basic database connection
    db_connected = test_database_connection()
    
    # Test application models
    models_working = test_application_models()
    
    print("\n" + "=" * 60)
    print("📋 SUMMARY:")
    print(f"Database Connection: {'✅ WORKING' if db_connected else '❌ FAILED'}")
    print(f"Application Models: {'✅ WORKING' if models_working else '❌ FAILED'}")
    
    if db_connected and models_working:
        print("🎉 Database is fully connected and ready!")
    else:
        print("⚠️ Database issues detected - see details above")
    print("=" * 60)