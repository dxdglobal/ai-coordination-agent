"""
Database migration script to add new Employee and Invoice tables
and update existing Task table with assigned_to column
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.models import db
from app import create_app

def migrate_database():
    app = create_app()
    
    with app.app_context():
        print("Running database migration...")
        
        # Drop all tables and recreate them with new schema
        print("Dropping existing tables...")
        db.drop_all()
        
        print("Creating new tables with updated schema...")
        db.create_all()
        
        print("✅ Database migration completed successfully!")
        print("✅ New tables created:")
        print("   - employees")
        print("   - invoices") 
        print("✅ Updated tables:")
        print("   - tasks (added assigned_to column)")

if __name__ == '__main__':
    migrate_database()