#!/usr/bin/env python3
"""
Migration script to populate existing tasks into the vector database
"""
import os
import sys

# Add current directory to path to import local modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.models import db, Task
from services.vector_service import VectorDatabaseService
from app import app

def migrate_existing_tasks():
    """Migrate existing tasks to vector database"""
    with app.app_context():
        vector_service = VectorDatabaseService()
        
        # Get all existing tasks
        tasks = Task.query.all()
        
        if not tasks:
            print("No existing tasks found. You may want to run test_semantic_search.py to create sample tasks.")
            return
        
        print(f"Found {len(tasks)} existing tasks. Migrating to vector database...")
        
        success_count = 0
        error_count = 0
        
        for task in tasks:
            try:
                task_dict = task.to_dict()
                success = vector_service.store_task_embedding(task.id, task_dict)
                
                if success:
                    success_count += 1
                    print(f"✓ Migrated task {task.id}: {task.title[:50]}...")
                else:
                    error_count += 1
                    print(f"✗ Failed to migrate task {task.id}: {task.title[:50]}...")
            
            except Exception as e:
                error_count += 1
                print(f"✗ Error migrating task {task.id}: {str(e)}")
        
        print(f"\nMigration completed:")
        print(f"  Successfully migrated: {success_count} tasks")
        print(f"  Errors: {error_count} tasks")
        
        # Get vector database stats
        try:
            stats = vector_service.get_collection_stats()
            print(f"\nVector Database Stats:")
            for collection, count in stats.items():
                print(f"  {collection}: {count}")
        except Exception as e:
            print(f"Error getting stats: {e}")

if __name__ == "__main__":
    migrate_existing_tasks()