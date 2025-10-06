"""
Script to create conversation history and AI learning tables
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.models import db, ConversationHistory, PromptTemplate, AILearningPattern
from app import create_app

def create_conversation_tables():
    """Create the conversation history and AI learning tables"""
    app = create_app()
    
    with app.app_context():
        try:
            # Create the tables
            db.create_all()
            
            print("✅ Successfully created conversation history tables:")
            print("   - conversation_history")
            print("   - prompt_templates") 
            print("   - ai_learning_patterns")
            
            # Verify tables were created
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            required_tables = ['conversation_history', 'prompt_templates', 'ai_learning_patterns']
            for table in required_tables:
                if table in tables:
                    print(f"✅ Table '{table}' created successfully")
                else:
                    print(f"❌ Table '{table}' was not created")
            
        except Exception as e:
            print(f"❌ Error creating tables: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    create_conversation_tables()