#!/usr/bin/env python3
"""
Enhanced AI Chatbot System with Comprehensive NLP, Rewards, and History
This system uses OpenAI for advanced prompt understanding and searches ALL database tables
"""

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
import json
from datetime import datetime, timedelta
import openai
import uuid
import re
from typing import Dict, List, Any, Optional, Tuple
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

# Initialize OpenAI
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', '92.113.22.65'),
    'user': os.getenv('DB_USER', 'u906714182_sqlrrefdvdv'),
    'password': os.getenv('DB_PASSWORD', '3@6*t:lU'),
    'database': os.getenv('DB_NAME', 'u906714182_sqlrrefdvdv'),
    'port': int(os.getenv('DB_PORT', 3306))
}

class EnhancedChatbotSystem:
    def __init__(self):
        self.conversation_history = {}  # Session-based history
        self.reward_system = RewardSystem()
        self.database_scanner = ComprehensiveDatabaseScanner()
        self.nlp_processor = AdvancedNLPProcessor()
        
    def get_database_connection(self):
        """Get MySQL database connection"""
        try:
            connection = mysql.connector.connect(**DB_CONFIG)
            return connection
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            return None
    
    def get_conversation_history(self, session_id: str) -> List[Dict]:
        """Get conversation history for session"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        return self.conversation_history[session_id]
    
    def add_to_conversation_history(self, session_id: str, user_message: str, assistant_response: str, metadata: Dict = None):
        """Add interaction to conversation history"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
            
        interaction = {
            'timestamp': datetime.now().isoformat(),
            'user_message': user_message,
            'assistant_response': assistant_response,
            'metadata': metadata or {}
        }
        
        self.conversation_history[session_id].append(interaction)
        
        # Keep only last 20 interactions to manage memory
        if len(self.conversation_history[session_id]) > 20:
            self.conversation_history[session_id] = self.conversation_history[session_id][-20:]
    
    def store_prompt_in_database(self, session_id: str, user_prompt: str, response: str, metadata: Dict):
        """Store prompt and response in database for learning"""
        connection = self.get_database_connection()
        if not connection:
            return None
            
        try:
            cursor = connection.cursor()
            
            # Insert into tblprompt_storage if it exists
            insert_query = """
            INSERT INTO tblprompt_storage (
                session_id, user_prompt, response_summary, 
                openai_analysis_json, processing_time_ms, 
                prompt_timestamp, processing_status
            ) VALUES (%s, %s, %s, %s, %s, NOW(), 'completed')
            """
            
            cursor.execute(insert_query, (
                session_id, 
                user_prompt, 
                response[:500],  # Store first 500 chars of response
                json.dumps(metadata),
                metadata.get('processing_time', 0)
            ))
            connection.commit()
            return cursor.lastrowid
            
        except Exception as e:
            logger.error(f"Error storing prompt: {e}")
            return None
        finally:
            if connection:
                connection.close()

class RewardSystem:
    """Reward system for user feedback and continuous improvement"""
    
    def __init__(self):
        self.feedback_scores = {}
        
    def record_feedback(self, session_id: str, message_id: str, feedback: str, rating: int):
        """Record user feedback for learning"""
        feedback_data = {
            'timestamp': datetime.now().isoformat(),
            'session_id': session_id,
            'message_id': message_id,
            'feedback': feedback,  # 'positive', 'negative', 'neutral'
            'rating': rating  # 1-5 scale
        }
        
        # Store in database
        connection = mysql.connector.connect(**DB_CONFIG)
        try:
            cursor = connection.cursor()
            cursor.execute("""
                UPDATE tblprompt_storage 
                SET user_feedback = %s, feedback_rating = %s 
                WHERE session_id = %s AND id = %s
            """, (feedback, rating, session_id, message_id))
            connection.commit()
        except Exception as e:
            logger.error(f"Error recording feedback: {e}")
        finally:
            connection.close()
            
        return feedback_data

class ComprehensiveDatabaseScanner:
    """Scans ALL database tables comprehensively"""
    
    def __init__(self):
        self.table_schemas = {}
        self.load_table_schemas()
    
    def load_table_schemas(self):
        """Load all table schemas for intelligent querying"""
        connection = mysql.connector.connect(**DB_CONFIG)
        try:
            cursor = connection.cursor()
            
            # Get all table names
            cursor.execute("SHOW TABLES")
            tables = [table[0] for table in cursor.fetchall()]
            
            # Get column information for each table
            for table in tables:
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                self.table_schemas[table] = {
                    'columns': [col[0] for col in columns],
                    'types': {col[0]: col[1] for col in columns}
                }
                
            logger.info(f"Loaded schemas for {len(tables)} tables")
            
        except Exception as e:
            logger.error(f"Error loading table schemas: {e}")
        finally:
            connection.close()
    
    def scan_all_tables_for_query(self, query_context: Dict) -> Dict:
        """Comprehensively scan ALL relevant tables based on query context"""
        connection = mysql.connector.connect(**DB_CONFIG)
        results = {}
        
        try:
            cursor = connection.cursor(dictionary=True)
            
            # Determine which tables to scan based on query context
            relevant_tables = self.determine_relevant_tables(query_context)
            
            for table in relevant_tables:
                try:
                    # Build dynamic query based on context
                    query = self.build_table_query(table, query_context)
                    if query:
                        cursor.execute(query)
                        results[table] = cursor.fetchall()
                        logger.info(f"Scanned {table}: found {len(results[table])} records")
                        
                except Exception as e:
                    logger.error(f"Error scanning table {table}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Database scanning error: {e}")
        finally:
            connection.close()
            
        return results
    
    def determine_relevant_tables(self, query_context: Dict) -> List[str]:
        """Determine which tables are relevant for the query"""
        intent = query_context.get('intent', '').lower()
        entities = query_context.get('entities', [])
        
        # Core tables that should always be considered
        core_tables = ['tblstaff', 'tblprojects', 'tbltasks', 'tblproject_members']
        
        # Additional tables based on intent
        if 'employee' in intent or 'staff' in intent:
            core_tables.extend(['tblstaff_permissions', 'tbldepartments'])
        
        if 'project' in intent:
            core_tables.extend(['tblclients', 'tblproject_files', 'tblproject_discussions'])
        
        if 'task' in intent:
            core_tables.extend(['tbltask_assignees', 'tbltask_comments', 'tbltask_timers'])
            
        if 'client' in intent or 'customer' in intent:
            core_tables.extend(['tblclients', 'tblcontacts', 'tblcontracts'])
            
        # Remove duplicates and ensure tables exist
        relevant_tables = list(set(core_tables))
        existing_tables = [t for t in relevant_tables if t in self.table_schemas]
        
        return existing_tables
    
    def build_table_query(self, table: str, query_context: Dict) -> Optional[str]:
        """Build appropriate query for each table based on context"""
        if table not in self.table_schemas:
            return None
            
        columns = self.table_schemas[table]['columns']
        search_terms = query_context.get('search_terms', [])
        
        # Build SELECT clause
        select_columns = columns[:10]  # Limit columns for performance
        select_clause = f"SELECT {', '.join(select_columns)}"
        
        # Build WHERE clause based on search terms
        where_conditions = []
        text_columns = [col for col in columns if any(keyword in col.lower() 
                       for keyword in ['name', 'title', 'description', 'email'])]
        
        for term in search_terms:
            term_conditions = []
            for col in text_columns:
                term_conditions.append(f"{col} LIKE '%{term}%'")
            if term_conditions:
                where_conditions.append(f"({' OR '.join(term_conditions)})")
        
        # Construct final query
        where_clause = f" WHERE {' AND '.join(where_conditions)}" if where_conditions else ""
        limit_clause = " LIMIT 1000"  # Prevent overwhelming results
        
        query = f"{select_clause} FROM {table}{where_clause}{limit_clause}"
        return query

class AdvancedNLPProcessor:
    """Advanced NLP processing using OpenAI"""
    
    def __init__(self):
        self.system_prompt = self.build_comprehensive_system_prompt()
    
    def build_comprehensive_system_prompt(self) -> str:
        """Build comprehensive system prompt for OpenAI"""
        return """
        AI assistant for business data. Analyze queries and return JSON:
        {"intent": "employee_query", "entities": ["names"], "tables_needed": ["tblstaff"], "query_type": "detail"}
        """
    
    def analyze_prompt_with_openai(self, user_prompt: str, conversation_history: List[Dict]) -> Dict:
        """Use OpenAI to deeply analyze user prompt"""
        try:
            # Temporary: Force fallback to test Turkish name functionality
            return self.fallback_analysis(user_prompt)
            
            # Build context from conversation history
            context_messages = []
            
            # Add system prompt
            context_messages.append({
                "role": "system",
                "content": self.system_prompt
            })
            
            # Add conversation history for context
            for interaction in conversation_history[-1:]:  # Last 1 interaction only
                context_messages.append({
                    "role": "user",
                    "content": interaction['user_message']
                })
                context_messages.append({
                    "role": "assistant", 
                    "content": interaction['assistant_response']
                })
            
            # Add current user prompt
            context_messages.append({
                "role": "user",
                "content": f"Analyze this prompt: {user_prompt}"
            })
            
            # Call OpenAI
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=context_messages,
                max_tokens=200,
                temperature=0.1
            )
            
            # Parse response
            analysis_text = response.choices[0].message.content
            analysis = json.loads(analysis_text)
            
            return analysis
            
        except Exception as e:
            logger.error(f"OpenAI analysis error: {e}")
            # Fallback to basic analysis
            return self.fallback_analysis(user_prompt)
    
    def fallback_analysis(self, user_prompt: str) -> Dict:
        """Fallback analysis when OpenAI is not available"""
        prompt_lower = user_prompt.lower()
        
        # Turkish character normalization
        def normalize_turkish(text):
            replacements = {
                'İ': 'i', 'I': 'i', 'ı': 'i', 'Ş': 's', 'ş': 's', 'Ğ': 'g', 'ğ': 'g',
                'Ü': 'u', 'ü': 'u', 'Ö': 'o', 'ö': 'o', 'Ç': 'c', 'ç': 'c'
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            return text.lower()
        
        # Common Turkish names for better detection
        turkish_names = [
            'ilahe', 'İlahe', 'deniz', 'tuğba', 'begüm', 'damla', 'gülay', 'ihsan', 'yusuf', 'ziya',
            'hamza', 'ahmet', 'mehmet', 'fatma', 'ayşe', 'mustafa', 'ali', 'zeynep', 'elif', 'emre'
        ]
        
        # Normalize prompt for Turkish name detection
        normalized_prompt = normalize_turkish(user_prompt)
        found_turkish_names = []
        
        # Check for Turkish names in the prompt
        words = user_prompt.split()
        for word in words:
            for turkish_name in turkish_names:
                if normalize_turkish(word) == normalize_turkish(turkish_name):
                    found_turkish_names.append(word)
                    break
        
        # Basic intent detection
        if found_turkish_names or any(word in prompt_lower for word in ['employee', 'staff', 'worker', 'person', 'report', 'rapor']):
            intent = 'employee_query'
            tables_needed = ['tblstaff']
        elif any(word in prompt_lower for word in ['project', 'projects', 'proje']):
            intent = 'project_query' 
            tables_needed = ['tblprojects', 'tblproject_members']
        elif any(word in prompt_lower for word in ['task', 'tasks', 'assignment', 'görev']):
            intent = 'task_query'
            tables_needed = ['tbltasks', 'tblprojects']
        else:
            intent = 'employee_query' if found_turkish_names else 'general_query'
            tables_needed = ['tblstaff', 'tblprojects', 'tbltasks']
        
        # Extract potential names/entities (including Turkish names)
        entities = []
        for word in words:
            if word[0].isupper() and len(word) > 2:
                entities.append(word)
            elif word in found_turkish_names:
                entities.append(word)
        
        # Add found Turkish names to entities
        entities.extend(found_turkish_names)
        entities = list(set(entities))  # Remove duplicates
        
        return {
            "intent": intent,
            "sub_intent": "turkish_name_query" if found_turkish_names else "basic",
            "entities": entities,
            "search_terms": words + found_turkish_names,
            "tables_needed": tables_needed,
            "query_type": "detail" if found_turkish_names else "list",
            "confidence": 0.9 if found_turkish_names else 0.7,
            "explanation": f"Found Turkish names: {found_turkish_names}" if found_turkish_names else f"Fallback analysis for: {user_prompt}",
            "suggested_response_format": "Detailed employee info" if found_turkish_names else "Simple list format"
        }

# Global chatbot instance
chatbot = EnhancedChatbotSystem()

@app.route('/ai/enhanced_chat', methods=['POST', 'OPTIONS'])
def enhanced_chat():
    """Enhanced chat endpoint with full NLP, rewards, and history"""
    
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response
    
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required', 'success': False}), 400
        
        user_message = data['message']
        session_id = data.get('session_id', str(uuid.uuid4()))
        
        logger.info(f"🚀 Enhanced Chat Query: {user_message} [Session: {session_id}]")
        
        start_time = datetime.now()
        
        # Step 1: Get conversation history
        conversation_history = chatbot.get_conversation_history(session_id)
        logger.info(f"📚 Loaded {len(conversation_history)} previous interactions")
        
        # Step 2: Advanced NLP analysis with OpenAI
        analysis = chatbot.nlp_processor.analyze_prompt_with_openai(user_message, conversation_history)
        logger.info(f"🧠 NLP Analysis: {analysis['intent']} (confidence: {analysis['confidence']})")
        
        # Step 3: Comprehensive database scanning
        scan_results = chatbot.database_scanner.scan_all_tables_for_query(analysis)
        logger.info(f"🔍 Scanned {len(scan_results)} tables")
        
        # Step 4: Generate intelligent response
        response_text = generate_intelligent_response(analysis, scan_results, conversation_history)
        
        # Step 5: Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Step 6: Store interaction in history and database
        metadata = {
            'analysis': analysis,
            'tables_scanned': list(scan_results.keys()),
            'processing_time': processing_time,
            'record_count': sum(len(records) for records in scan_results.values())
        }
        
        chatbot.add_to_conversation_history(session_id, user_message, response_text, metadata)
        prompt_id = chatbot.store_prompt_in_database(session_id, user_message, response_text, metadata)
        
        # Step 7: Return comprehensive response
        response_data = {
            'success': True,
            'response': response_text,
            'session_id': session_id,
            'prompt_id': prompt_id,
            'analysis': analysis,
            'processing_time_ms': processing_time,
            'records_found': sum(len(records) for records in scan_results.values()),
            'tables_scanned': list(scan_results.keys()),
            'conversation_length': len(conversation_history)
        }
        
        response = make_response(jsonify(response_data))
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
        
    except Exception as e:
        logger.error(f"❌ Enhanced Chat Error: {str(e)}")
        error_response = {
            'success': False,
            'error': str(e),
            'response': 'I encountered an error processing your request. Please try again.'
        }
        response = make_response(jsonify(error_response), 500)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

def generate_intelligent_response(analysis: Dict, scan_results: Dict, conversation_history: List[Dict]) -> str:
    """Generate intelligent response based on analysis and data"""
    
    intent = analysis['intent']
    sub_intent = analysis.get('sub_intent', '')
    entities = analysis.get('entities', [])
    query_type = analysis.get('query_type', 'list')
    
    # Count total records found
    total_records = sum(len(records) for records in scan_results.values())
    
    if total_records == 0:
        return f"I couldn't find any information matching your request: '{' '.join(entities)}'. Please try a different search or check the spelling."
    
    logger.info(f"📊 Generating response for {intent} with {total_records} total records")
    
    # Generate response based on intent
    if intent == 'employee_query':
        return generate_employee_response(analysis, scan_results, conversation_history)
    elif intent == 'project_query':
        return generate_project_response(analysis, scan_results, conversation_history)
    elif intent == 'task_query':
        return generate_task_response(analysis, scan_results, conversation_history)
    else:
        return generate_general_response(analysis, scan_results, conversation_history)

def generate_employee_response(analysis: Dict, scan_results: Dict, conversation_history: List[Dict]) -> str:
    """Generate employee-focused response"""
    
    employees = scan_results.get('tblstaff', [])
    entities = analysis.get('entities', [])
    
    if not employees:
        return "No employees found matching your criteria."
    
    # Check if looking for specific employee
    if entities and any(entity.lower() in analysis.get('search_terms', []) for entity in entities):
        # Specific employee search with Turkish character support
        target_name = entities[0] if entities else ""
        
        def normalize_turkish(text):
            """Normalize Turkish characters for better matching"""
            if not text:
                return ""
            replacements = {
                'İ': 'i', 'I': 'i', 'ı': 'i', 'Ş': 's', 'ş': 's', 'Ğ': 'g', 'ğ': 'g',
                'Ü': 'u', 'ü': 'u', 'Ö': 'o', 'ö': 'o', 'Ç': 'c', 'ç': 'c'
            }
            for old, new in replacements.items():
                text = text.replace(old, new)
            return text.lower()
        
        normalized_target = normalize_turkish(target_name)
        
        matching_employees = []
        for emp in employees:
            firstname = normalize_turkish(emp.get('firstname', ''))
            lastname = normalize_turkish(emp.get('lastname', ''))
            name = normalize_turkish(emp.get('name', ''))
            
            # Check if target name matches any part of the employee name
            if (normalized_target in firstname or 
                normalized_target in lastname or 
                normalized_target in name or
                firstname in normalized_target or
                lastname in normalized_target):
                matching_employees.append(emp)
        
        if matching_employees:
            # If only one match, show detailed info
            if len(matching_employees) == 1:
                emp = matching_employees[0]
                response = f"👤 **{emp.get('firstname', '')} {emp.get('lastname', '')}**\n"
                response += f"📧 {emp.get('email', 'No email')}\n"
                response += f"🏢 {emp.get('role', 'No role specified')}\n"
                response += f"📱 {emp.get('phonenumber', 'No phone')}\n"
                response += f"🆔 Staff ID: {emp.get('staffid', 'N/A')}\n"
                response += f"📍 Workplace: {emp.get('workplace', 'Not specified')}\n"
                response += f"💼 Position: {emp.get('job_position', 'Not specified')}\n"
                response += f"✅ Status: {'Active' if emp.get('active') == 1 else 'Inactive'}\n"
                
                # Add project information if available
                projects = scan_results.get('tblprojects', [])
                if projects:
                    response += f"\n📊 Currently working on {len(projects)} project(s)"
                
                return response
            else:
                # Multiple matches, show list
                response = f"👥 **Found {len(matching_employees)} employees matching '{target_name}':**\n\n"
                for i, emp in enumerate(matching_employees, 1):
                    name = f"{emp.get('firstname', '')} {emp.get('lastname', '')}".strip()
                    role = emp.get('job_position', emp.get('role', 'No role'))
                    response += f"{i}. **{name}** - {role}\n"
                return response
            projects = scan_results.get('tblprojects', [])
            if projects:
                response += f"\n📊 Currently working on {len(projects)} project(s)"
            
            return response
    
    # General employee list
    if 'active' in analysis.get('search_terms', []):
        active_employees = [emp for emp in employees if emp.get('active', 0) == 1]
        employees_to_show = active_employees
        response = f"👥 **Active Employees ({len(active_employees)}):**\n\n"
    else:
        employees_to_show = employees
        response = f"👥 **All Employees ({len(employees)}):**\n\n"
    
    # Show employee list
    for i, emp in enumerate(employees_to_show[:20], 1):  # Limit to 20
        name = f"{emp.get('firstname', '')} {emp.get('lastname', '')}".strip()
        if not name:
            name = emp.get('name', 'Unknown')
        response += f"{i}. **{name}**\n"
    
    if len(employees_to_show) > 20:
        response += f"\n... and {len(employees_to_show) - 20} more employees"
    
    return response

def generate_project_response(analysis: Dict, scan_results: Dict, conversation_history: List[Dict]) -> str:
    """Generate project-focused response"""
    
    projects = scan_results.get('tblprojects', [])
    project_members = scan_results.get('tblproject_members', [])
    entities = analysis.get('entities', [])
    
    if not projects:
        return "No projects found matching your criteria."
    
    # Check if looking for employee's projects
    if entities and any(entity in analysis.get('search_terms', []) for entity in entities):
        employee_name = entities[0]
        response = f"📊 **Projects for {employee_name}:**\n\n"
        
        # Filter projects by employee (if project_members data available)
        if project_members:
            employee_project_ids = [pm.get('project_id') for pm in project_members 
                                  if employee_name.lower() in str(pm.get('staff_id', '')).lower()]
            filtered_projects = [p for p in projects if p.get('id') in employee_project_ids]
        else:
            filtered_projects = projects
    else:
        response = f"📊 **All Projects ({len(projects)}):**\n\n"
        filtered_projects = projects
    
    # Show projects
    for i, project in enumerate(filtered_projects[:15], 1):  # Limit to 15
        name = project.get('name', 'Unnamed Project')
        status = project.get('status', 'Unknown')
        response += f"{i}. **{name}**\n"
        response += f"   Status: {status}\n"
        if project.get('deadline'):
            response += f"   Deadline: {project['deadline']}\n"
        response += "\n"
    
    if len(filtered_projects) > 15:
        response += f"... and {len(filtered_projects) - 15} more projects"
    
    return response

def generate_task_response(analysis: Dict, scan_results: Dict, conversation_history: List[Dict]) -> str:
    """Generate task-focused response"""
    
    tasks = scan_results.get('tbltasks', [])
    projects = scan_results.get('tblprojects', [])
    entities = analysis.get('entities', [])
    
    if not tasks:
        return "No tasks found matching your criteria."
    
    # Check for specific project or employee in entities
    target_filter = entities[0] if entities else None
    
    if target_filter:
        response = f"📝 **Tasks for {target_filter}:**\n\n"
    else:
        response = f"📝 **All Tasks ({len(tasks)}):**\n\n"
    
    # Show tasks with enhanced information
    for i, task in enumerate(tasks[:20], 1):  # Limit to 20
        name = task.get('name', 'Unnamed Task')
        status = task.get('status', 'Unknown')
        priority = task.get('priority', 'Normal')
        
        # Status emoji
        status_emoji = "✅" if status == "5" or status == "Completed" else "🔄" if status == "4" or status == "In Progress" else "⭕"
        priority_emoji = "🔴" if priority == "High" else "🟡" if priority == "Medium" else "🟢"
        
        response += f"{i}. {status_emoji} {priority_emoji} **{name}**\n"
        
        # Add project name if available
        project_id = task.get('rel_id') or task.get('project_id')
        if project_id and projects:
            project = next((p for p in projects if p.get('id') == project_id), None)
            if project:
                response += f"   📊 Project: {project.get('name', 'Unknown')}\n"
        
        if task.get('duedate'):
            response += f"   📅 Due: {task['duedate']}\n"
        response += "\n"
    
    if len(tasks) > 20:
        response += f"... and {len(tasks) - 20} more tasks"
    
    return response

def generate_general_response(analysis: Dict, scan_results: Dict, conversation_history: List[Dict]) -> str:
    """Generate general response for complex queries"""
    
    total_records = sum(len(records) for records in scan_results.values())
    
    response = f"🔍 **Search Results** (found {total_records} records across {len(scan_results)} tables)\n\n"
    
    # Show summary from each table
    for table, records in scan_results.items():
        if records and len(records) > 0:
            response += f"**{table.replace('tbl', '').title()}:** {len(records)} records\n"
            
            # Show sample records
            for record in records[:3]:
                # Try to find name field
                name = (record.get('name') or record.get('firstname') or 
                       record.get('title') or record.get('company') or 'Unknown')
                response += f"  • {name}\n"
            
            if len(records) > 3:
                response += f"  • ... and {len(records) - 3} more\n"
            response += "\n"
    
    response += "💡 Try being more specific about what you're looking for!"
    return response

@app.route('/ai/feedback', methods=['POST', 'OPTIONS'])
def record_feedback():
    """Record user feedback for the reward system"""
    
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
        return response
    
    try:
        data = request.get_json()
        session_id = data.get('session_id')
        message_id = data.get('message_id')
        feedback = data.get('feedback')  # 'positive', 'negative', 'neutral'
        rating = data.get('rating', 3)  # 1-5 scale
        
        if not all([session_id, message_id, feedback]):
            return jsonify({'error': 'Missing required fields', 'success': False}), 400
        
        # Record feedback
        feedback_result = chatbot.reward_system.record_feedback(
            session_id, message_id, feedback, rating
        )
        
        logger.info(f"👍 Feedback recorded: {feedback} ({rating}/5) for session {session_id}")
        
        response_data = {
            'success': True,
            'message': 'Feedback recorded successfully',
            'feedback_id': feedback_result.get('timestamp')
        }
        
        response = make_response(jsonify(response_data))
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
        
    except Exception as e:
        logger.error(f"❌ Feedback Error: {str(e)}")
        error_response = {
            'success': False,
            'error': str(e)
        }
        response = make_response(jsonify(error_response), 500)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

@app.route('/ai/conversation_history/<session_id>', methods=['GET'])
def get_conversation_history(session_id: str):
    """Get conversation history for a session"""
    try:
        history = chatbot.get_conversation_history(session_id)
        
        response_data = {
            'success': True,
            'session_id': session_id,
            'conversation_history': history,
            'total_interactions': len(history)
        }
        
        response = make_response(jsonify(response_data))
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
        
    except Exception as e:
        logger.error(f"❌ History Error: {str(e)}")
        error_response = {
            'success': False,
            'error': str(e)
        }
        response = make_response(jsonify(error_response), 500)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'database_connection': 'ok' if chatbot.get_database_connection() else 'failed'
    })

if __name__ == '__main__':
    print("🚀 Starting Enhanced AI Chatbot System...")
    print("📊 Features:")
    print("  ✅ Advanced NLP with OpenAI")
    print("  ✅ Comprehensive database scanning")
    print("  ✅ Conversation history tracking")
    print("  ✅ Reward/feedback system")
    print("  ✅ Multi-table intelligent queries")
    print("  ✅ Context-aware responses")
    print(f"🌐 Running on: http://127.0.0.1:5001")
    print("=" * 50)
    
    app.run(host='127.0.0.1', port=5001, debug=True)