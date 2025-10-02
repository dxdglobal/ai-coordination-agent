#!/usr/bin/env python3
"""
Create prompt storage table for AI coordination agent
This table will store user prompts, AI analysis, generated queries, and responses
"""

import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '92.113.22.65'),
    'user': os.getenv('DB_USER', 'u906714182_sqlrrefdvdv'),
    'password': os.getenv('DB_PASSWORD', '3@6*t:lU'),
    'database': os.getenv('DB_NAME', 'u906714182_sqlrrefdvdv'),
    'port': int(os.getenv('DB_PORT', 3306))
}

def create_prompt_storage_table():
    """Create table for storing prompts and their processing workflow"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create tblprompt_storage table
        create_table_query = """
        CREATE TABLE IF NOT EXISTS tblprompt_storage (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id VARCHAR(100) NOT NULL,
            user_prompt TEXT NOT NULL,
            prompt_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            
            -- OpenAI Analysis Results
            openai_intent_type VARCHAR(50),
            openai_target VARCHAR(100),
            openai_confidence DECIMAL(3,2),
            openai_explanation TEXT,
            openai_analysis_json TEXT,
            
            -- Generated Query Information
            generated_query TEXT,
            query_type VARCHAR(50),
            query_parameters JSON,
            
            -- Response Information
            response_data JSON,
            response_summary TEXT,
            response_timestamp TIMESTAMP NULL,
            
            -- Status and Metadata
            processing_status ENUM('pending', 'processing', 'completed', 'failed') DEFAULT 'pending',
            error_message TEXT NULL,
            processing_time_ms INT DEFAULT 0,
            
            -- Future Use and Learning
            user_feedback ENUM('positive', 'negative', 'neutral') NULL,
            is_successful_query BOOLEAN DEFAULT TRUE,
            used_for_training BOOLEAN DEFAULT FALSE,
            
            INDEX idx_session_id (session_id),
            INDEX idx_timestamp (prompt_timestamp),
            INDEX idx_intent_type (openai_intent_type),
            INDEX idx_status (processing_status)
        ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
        """
        
        cursor.execute(create_table_query)
        connection.commit()
        print("✅ Successfully created tblprompt_storage table")
        
        # Create indexes for better performance
        indexes = [
            "CREATE INDEX IF NOT EXISTS idx_prompt_search ON tblprompt_storage (user_prompt(200))",
            "CREATE INDEX IF NOT EXISTS idx_response_search ON tblprompt_storage (response_summary(200))",
            "CREATE INDEX IF NOT EXISTS idx_target_search ON tblprompt_storage (openai_target)"
        ]
        
        for index_query in indexes:
            try:
                cursor.execute(index_query)
                connection.commit()
            except mysql.connector.Error as e:
                print(f"⚠️  Index creation warning: {e}")
        
        print("✅ Created search indexes for prompt storage")
        
    except mysql.connector.Error as error:
        print(f"❌ Error creating prompt storage table: {error}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

def create_prompt_analytics_view():
    """Create view for prompt analytics and insights"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()
        
        # Create analytics view
        view_query = """
        CREATE OR REPLACE VIEW vw_prompt_analytics AS
        SELECT 
            DATE(prompt_timestamp) as date,
            openai_intent_type,
            COUNT(*) as prompt_count,
            AVG(openai_confidence) as avg_confidence,
            AVG(processing_time_ms) as avg_processing_time,
            SUM(CASE WHEN processing_status = 'completed' THEN 1 ELSE 0 END) as successful_count,
            SUM(CASE WHEN processing_status = 'failed' THEN 1 ELSE 0 END) as failed_count,
            SUM(CASE WHEN user_feedback = 'positive' THEN 1 ELSE 0 END) as positive_feedback,
            SUM(CASE WHEN user_feedback = 'negative' THEN 1 ELSE 0 END) as negative_feedback
        FROM tblprompt_storage 
        GROUP BY DATE(prompt_timestamp), openai_intent_type
        ORDER BY date DESC, prompt_count DESC
        """
        
        cursor.execute(view_query)
        connection.commit()
        print("✅ Successfully created vw_prompt_analytics view")
        
    except mysql.connector.Error as error:
        print(f"❌ Error creating analytics view: {error}")
    finally:
        if connection and connection.is_connected():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    print("🚀 Creating prompt storage system...")
    print(f"📊 Database: {DB_CONFIG['host']}/{DB_CONFIG['database']}")
    
    create_prompt_storage_table()
    create_prompt_analytics_view()
    
    print("\n✅ Prompt storage system created successfully!")
    print("\n📊 You can now:")
    print("  - Store user prompts and AI analysis")
    print("  - Track query generation and execution")
    print("  - Analyze prompt patterns and success rates")
    print("  - Build learning datasets for future improvements")