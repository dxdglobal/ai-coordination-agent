"""
Enhanced AI service for generating SQL queries and comprehensive responses
This service integrates OpenAI analysis with database query generation and prompt storage
"""

import openai
import json
import mysql.connector
import time
from datetime import datetime
from typing import Dict, Any, Optional, Tuple
import os
from dotenv import load_dotenv

load_dotenv()

class EnhancedAIQueryService:
    def __init__(self):
        self.api_key = os.getenv('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
        
        self.db_config = {
            'host': os.getenv('DB_HOST', '92.113.22.65'),
            'user': os.getenv('DB_USER', 'u906714182_sqlrrefdvdv'),
            'password': os.getenv('DB_PASSWORD', '3@6*t:lU'),
            'database': os.getenv('DB_NAME', 'u906714182_sqlrrefdvdv'),
            'port': int(os.getenv('DB_PORT', 3306))
        }
    
    def store_prompt_record(self, session_id: str, user_prompt: str) -> Optional[int]:
        """Create initial prompt record in database"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            insert_query = """
            INSERT INTO tblprompt_storage (
                session_id, user_prompt, processing_status
            ) VALUES (%s, %s, 'pending')
            """
            
            cursor.execute(insert_query, (session_id, user_prompt))
            connection.commit()
            
            prompt_id = cursor.lastrowid
            return prompt_id
            
        except mysql.connector.Error as error:
            print(f"❌ Error storing prompt record: {error}")
            return None
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def update_openai_analysis(self, prompt_id: int, analysis_result: Dict[str, Any]) -> bool:
        """Update prompt record with OpenAI analysis results"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            update_query = """
            UPDATE tblprompt_storage SET
                openai_intent_type = %s,
                openai_target = %s,
                openai_confidence = %s,
                openai_explanation = %s,
                openai_analysis_json = %s,
                processing_status = 'processing'
            WHERE id = %s
            """
            
            cursor.execute(update_query, (
                analysis_result.get('intent_type'),
                analysis_result.get('target'),
                analysis_result.get('confidence', 0.0),
                analysis_result.get('explanation'),
                json.dumps(analysis_result),
                prompt_id
            ))
            connection.commit()
            return True
            
        except mysql.connector.Error as error:
            print(f"❌ Error updating OpenAI analysis: {error}")
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def generate_sql_query(self, user_prompt: str, intent_analysis: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Generate SQL query based on user prompt and intent analysis"""
        try:
            # Enhanced system prompt for SQL generation
            system_prompt = f"""
You are an expert SQL query generator for a CRM database. Based on the user prompt and intent analysis, generate the most appropriate SQL query.

DATABASE SCHEMA:
- tblstaff: id, name, email, position, department, hire_date, status
- tblprojects: id, name, description, start_date, end_date, status, priority, budget
- tblproject_members: id, project_id, staff_id, role, assigned_date
- tbltasks: id, project_id, assigned_to, title, description, status, priority, due_date, created_date
- tblprompt_storage: id, session_id, user_prompt, openai_intent_type, response_data

INTENT ANALYSIS:
- Intent Type: {intent_analysis.get('intent_type', 'unknown')}
- Target: {intent_analysis.get('target', 'None')}
- Wants List: {intent_analysis.get('wants_list', False)}
- Wants Details: {intent_analysis.get('wants_details', False)}
- Search Terms: {intent_analysis.get('search_terms', [])}

Generate a SQL query that:
1. Returns relevant data based on the intent
2. Includes proper JOINs when needed
3. Filters data appropriately
4. Orders results logically
5. Limits results if needed (use LIMIT 50 for large datasets)

ALSO provide query metadata including:
- query_type: (select, count, analysis)
- estimated_results: (low, medium, high)
- tables_used: [list of tables]
- requires_joins: boolean

Return response as JSON with 'sql_query' and 'metadata' fields.
"""

            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Generate SQL query for: {user_prompt}"}
            ]
            
            if not self.api_key:
                # Fallback query generation without OpenAI
                return self.generate_fallback_query(intent_analysis)
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=500,
                temperature=0.1
            )
            
            result = json.loads(response.choices[0].message.content)
            sql_query = result.get('sql_query', '')
            metadata = result.get('metadata', {})
            
            return sql_query, metadata
            
        except Exception as e:
            print(f"❌ Error generating SQL query: {e}")
            return self.generate_fallback_query(intent_analysis)
    
    def generate_fallback_query(self, intent_analysis: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Generate fallback SQL query without OpenAI"""
        intent_type = intent_analysis.get('intent_type', 'general_search')
        target = intent_analysis.get('target')
        
        if intent_type == 'employee_list':
            sql_query = "SELECT id, name, email, position, department FROM tblstaff WHERE status = 'active' ORDER BY name LIMIT 50"
            metadata = {'query_type': 'select', 'estimated_results': 'medium', 'tables_used': ['tblstaff'], 'requires_joins': False}
            
        elif intent_type == 'employee_projects_list' and target:
            sql_query = f"""
            SELECT p.id, p.name, p.description, p.status, pm.role 
            FROM tblprojects p 
            JOIN tblproject_members pm ON p.id = pm.project_id 
            JOIN tblstaff s ON pm.staff_id = s.id 
            WHERE s.name LIKE '%{target}%' 
            ORDER BY p.status, p.name LIMIT 50
            """
            metadata = {'query_type': 'select', 'estimated_results': 'medium', 'tables_used': ['tblprojects', 'tblproject_members', 'tblstaff'], 'requires_joins': True}
            
        elif intent_type == 'project_tasks' and target:
            sql_query = f"""
            SELECT t.id, t.title, t.description, t.status, t.priority, t.due_date, s.name as assigned_to_name
            FROM tbltasks t 
            LEFT JOIN tblstaff s ON t.assigned_to = s.id 
            JOIN tblprojects p ON t.project_id = p.id 
            WHERE p.name LIKE '%{target}%' 
            ORDER BY t.priority DESC, t.due_date LIMIT 50
            """
            metadata = {'query_type': 'select', 'estimated_results': 'medium', 'tables_used': ['tbltasks', 'tblstaff', 'tblprojects'], 'requires_joins': True}
            
        else:
            # General search across multiple tables
            search_terms = intent_analysis.get('search_terms', [])
            search_term = search_terms[0] if search_terms else 'active'
            sql_query = f"""
            SELECT 'employee' as type, id, name, email as info FROM tblstaff WHERE name LIKE '%{search_term}%' OR email LIKE '%{search_term}%'
            UNION
            SELECT 'project' as type, id, name, description as info FROM tblprojects WHERE name LIKE '%{search_term}%' OR description LIKE '%{search_term}%'
            ORDER BY type, name LIMIT 20
            """
            metadata = {'query_type': 'select', 'estimated_results': 'low', 'tables_used': ['tblstaff', 'tblprojects'], 'requires_joins': False}
        
        return sql_query, metadata
    
    def execute_query_safely(self, sql_query: str, metadata: Dict[str, Any]) -> Tuple[bool, Any]:
        """Execute SQL query with safety checks"""
        try:
            # Safety checks
            sql_lower = sql_query.lower().strip()
            if not sql_lower.startswith('select'):
                return False, "Only SELECT queries are allowed"
            
            if any(dangerous in sql_lower for dangerous in ['drop', 'delete', 'update', 'insert', 'alter', 'create']):
                return False, "Potentially dangerous SQL detected"
            
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute(sql_query)
            results = cursor.fetchall()
            
            return True, results
            
        except mysql.connector.Error as error:
            return False, f"Database error: {error}"
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def complete_prompt_processing(self, prompt_id: int, sql_query: str, metadata: Dict[str, Any], 
                                 query_results: Any, processing_time: int) -> bool:
        """Complete prompt processing and store final results"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            cursor = connection.cursor()
            
            # Prepare response data
            response_data = {
                'query_results': query_results if isinstance(query_results, list) else str(query_results),
                'result_count': len(query_results) if isinstance(query_results, list) else 0,
                'metadata': metadata
            }
            
            # Generate response summary
            if isinstance(query_results, list):
                response_summary = f"Found {len(query_results)} results matching your query"
            else:
                response_summary = str(query_results)
            
            update_query = """
            UPDATE tblprompt_storage SET
                generated_query = %s,
                query_type = %s,
                query_parameters = %s,
                response_data = %s,
                response_summary = %s,
                response_timestamp = NOW(),
                processing_status = 'completed',
                processing_time_ms = %s,
                is_successful_query = %s
            WHERE id = %s
            """
            
            cursor.execute(update_query, (
                sql_query,
                metadata.get('query_type', 'select'),
                json.dumps(metadata),
                json.dumps(response_data),
                response_summary,
                processing_time,
                isinstance(query_results, list),
                prompt_id
            ))
            connection.commit()
            return True
            
        except mysql.connector.Error as error:
            print(f"❌ Error completing prompt processing: {error}")
            return False
        finally:
            if connection and connection.is_connected():
                cursor.close()
                connection.close()
    
    def process_user_prompt(self, session_id: str, user_prompt: str, intent_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Complete workflow: Store prompt → Generate query → Execute → Store results"""
        start_time = time.time()
        
        # Step 1: Store initial prompt record
        prompt_id = self.store_prompt_record(session_id, user_prompt)
        if not prompt_id:
            return {'error': 'Failed to store prompt record'}
        
        # Step 2: Update with OpenAI analysis
        self.update_openai_analysis(prompt_id, intent_analysis)
        
        # Step 3: Generate SQL query
        sql_query, metadata = self.generate_sql_query(user_prompt, intent_analysis)
        
        # Step 4: Execute query safely
        success, results = self.execute_query_safely(sql_query, metadata)
        
        # Step 5: Complete processing and store results
        processing_time = int((time.time() - start_time) * 1000)
        self.complete_prompt_processing(prompt_id, sql_query, metadata, results, processing_time)
        
        # Return comprehensive response
        return {
            'prompt_id': prompt_id,
            'sql_query': sql_query,
            'query_metadata': metadata,
            'success': success,
            'results': results,
            'processing_time_ms': processing_time,
            'session_id': session_id
        }

# Global instance
enhanced_ai_service = EnhancedAIQueryService()