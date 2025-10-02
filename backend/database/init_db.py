#!/usr/bin/env python3
"""
Database initialization script for AI Coordination Agent
This script will test the database connection and create all tables
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db

def init_database():
    """Initialize the database and create all tables"""
    try:
        app = create_app()
        
        with app.app_context():
            # Test database connection
            print("Testing database connection...")
            with db.engine.connect() as connection:
                connection.execute(db.text("SELECT 1"))
            print("✅ Database connection successful!")
            
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            print("✅ All tables created successfully!")
            
            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            print(f"📋 Created tables: {', '.join(tables)}")
            
            return True
            
    except Exception as e:
        print(f"❌ Database initialization failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Initializing AI Coordination Agent Database...")
    print("=" * 50)
    
    success = init_database()
    
    if success:
        print("=" * 50)
        print("✅ Database initialization completed successfully!")
        print("🎉 Your AI Coordination Agent is ready to use!")
    else:
        print("=" * 50)
        print("❌ Database initialization failed!")
        print("Please check your database configuration and try again.")
        sys.exit(1)