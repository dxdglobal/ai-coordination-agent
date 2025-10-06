#!/usr/bin/env python3
"""
Simplified Flask server for real CRM data integration
Bypasses ChromaDB/OpenAI issues and connects directly to database
"""

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS
import mysql.connector
import os
from dotenv import load_dotenv
import json
from datetime import datetime
import openai
from services.enhanced_ai_query_service import enhanced_ai_service

# Import the intelligent table mapper
try:
    from intelligent_table_mapper import IntelligentTableMapper, get_relevant_tables_for_query, get_query_strategy
    table_mapper = IntelligentTableMapper()
    INTELLIGENT_MAPPING_ENABLED = True
    print("✅ Intelligent Table Mapper loaded successfully!")
except ImportError:
    print("⚠️ Intelligent Table Mapper not available, using fallback")
    table_mapper = None
    INTELLIGENT_MAPPING_ENABLED = False

load_dotenv()

# Initialize OpenAI with old API style (compatible with 1.3.7)
openai.api_key = os.getenv('OPENAI_API_KEY')

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Conversation history storage - simple in-memory storage for demo
# In production, you'd want to use Redis, database sessions, or similar
conversation_history = {}
MAX_HISTORY_LENGTH = 10  # Keep last 10 exchanges per session

def get_or_create_session(session_id="default"):
    """Get or create conversation history for a session"""
    if session_id not in conversation_history:
        conversation_history[session_id] = {
            'messages': [],
            'context': {
                'current_employee': None,
                'current_project': None,
                'last_intent': None,
                'mentioned_entities': set()
            }
        }
    return conversation_history[session_id]

def add_to_history(session_id, user_message, ai_response, context_info=None):
    """Add exchange to conversation history"""
    session = get_or_create_session(session_id)
    
    # Add the exchange
    session['messages'].append({
        'user': user_message,
        'ai': ai_response,
        'timestamp': datetime.now().isoformat(),
        'context': context_info or {}
    })
    
    # Keep only recent history
    if len(session['messages']) > MAX_HISTORY_LENGTH:
        session['messages'] = session['messages'][-MAX_HISTORY_LENGTH:]

def extract_context_from_history(session_id, current_query):
    """Extract relevant context from conversation history"""
    session = get_or_create_session(session_id)
    context = {
        'current_employee': None,
        'current_project': None,
        'mentioned_entities': set(),
        'conversation_flow': []
    }
    
    # Analyze recent messages for context
    recent_messages = session['messages'][-3:]  # Look at last 3 exchanges
    
    for msg in recent_messages:
        # Extract employee names mentioned
        user_text = msg['user'].lower()
        ai_text = msg['ai'].lower()
        
        # Look for employee names in conversation
        employee_names = ['hamza', 'nawaz', 'john', 'sarah', 'mike', 'david', 'lisa', 'alex', 'maria', 'james', 'emma', 'ahmed', 'ali', 'hassan', 'fatima', 'aisha']
        for name in employee_names:
            if name in user_text or name in ai_text:
                context['mentioned_entities'].add(name.title())
                if not context['current_employee']:
                    context['current_employee'] = name.title()
        
        # Extract project context
        if any(word in user_text for word in ['project', 'dds focus pro', 'ai coordination']):
            if 'dds focus pro' in user_text:
                context['current_project'] = 'DDS Focus Pro'
            elif 'ai coordination' in user_text:
                context['current_project'] = 'AI Coordination'
    
    return context

def add_to_conversation_history(session_id, message, role):
    """Add a message to conversation history"""
    try:
        session = get_or_create_session(session_id)
        
        # Add the message
        session['messages'].append({
            'role': role,  # 'user' or 'assistant'
            'content': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Keep only recent history
        if len(session['messages']) > MAX_HISTORY_LENGTH * 2:  # *2 because we store both user and assistant messages
            session['messages'] = session['messages'][-MAX_HISTORY_LENGTH * 2:]
        
        print(f"📝 Added to conversation history ({session_id}): {role} - {message[:50]}...")
        
    except Exception as e:
        print(f"Error adding to conversation history: {e}")

def enhance_query_with_context(query_text, conversation_context):
    """Enhance user query with conversation context for better understanding"""
    enhanced_query = query_text
    query_lower = query_text.lower()
    
    # Add context when user refers to ambiguous pronouns or implicit references
    context_additions = []
    
    # Handle pronouns and implicit references
    if conversation_context['current_employee']:
        # If user asks "show his projects" or "how is he doing", add employee context
        if any(word in query_lower for word in ['his', 'he', 'him', 'their', 'them', 'this person']):
            context_additions.append(f"referring to {conversation_context['current_employee']}")
        
        # If user asks vague questions like "show projects" after mentioning someone
        elif any(phrase in query_lower for phrase in ['show projects', 'list projects', 'projects']) and not any(name.lower() in query_lower for name in conversation_context['mentioned_entities']):
            context_additions.append(f"for {conversation_context['current_employee']}")
        
        # If user asks "how is performance" after discussing someone
        elif any(phrase in query_lower for phrase in ['performance', 'how is', 'progress']) and not any(name.lower() in query_lower for name in conversation_context['mentioned_entities']):
            context_additions.append(f"of {conversation_context['current_employee']}")
    
    # Add current project context
    if conversation_context['current_project']:
        if any(phrase in query_lower for phrase in ['show tasks', 'list tasks', 'tasks']) and 'project' not in query_lower:
            context_additions.append(f"in {conversation_context['current_project']}")
    
    # Enhance the query with context
    if context_additions:
        enhanced_query = f"{query_text} {' '.join(context_additions)}"
    
    return enhanced_query

def update_conversation_context(context, intent_analysis, results):
    """Update conversation context based on query results"""
    intent_type = intent_analysis.get('intent_type')
    target = intent_analysis.get('target')
    
    # Update current employee if employee-specific query
    if intent_type in ['specific_employee', 'employee_projects_list'] and target:
        context['current_employee'] = target
        context['mentioned_entities'].add(target)
    
    # Update current project if project-specific query  
    if intent_type == 'project_tasks' and target:
        context['current_project'] = target
        context['mentioned_entities'].add(target)
    
    # Extract entity names from results
    if isinstance(results, list):
        for result in results[:5]:  # Process first 5 results
            if isinstance(result, dict):
                if 'name' in result and result['name']:
                    context['mentioned_entities'].add(result['name'])
    
    # Update last intent
    context['last_intent'] = intent_type
    
    return context

def get_database_connection():
    """Get MySQL database connection"""
    try:
        connection = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            database=os.getenv('DB_NAME'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            port=int(os.getenv('DB_PORT', 3306))
        )
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def analyze_employee_performance(projects, employee_name="Employee", tasks_data=None):
    """Analyze any employee's work performance and productivity patterns"""
    from datetime import datetime, timedelta
    
    current_date = datetime.now().date()
    performance_data = {
        'employee_name': employee_name,
        'total_projects': len(projects),
        'completed_projects': 0,
        'overdue_projects': 0,
        'on_time_projects': 0,
        'early_projects': 0,
        'late_projects': 0,
        'active_projects': 0,
        'performance_score': 0,
        'work_ethic': '',
        'insights': []
    }
    
    for project in projects:
        # Project status analysis
        if project.get('status') == 'Completed':
            performance_data['completed_projects'] += 1
            
            # Check if completed on time
            if project.get('deadline'):
                try:
                    deadline = datetime.strptime(project['deadline'], '%Y-%m-%d').date()
                    # Assuming completion date from project data or using current date
                    completion_date = current_date  # You might want to get actual completion date
                    
                    if completion_date <= deadline:
                        performance_data['on_time_projects'] += 1
                        if completion_date < deadline - timedelta(days=2):
                            performance_data['early_projects'] += 1
                    else:
                        performance_data['late_projects'] += 1
                except:
                    pass
        else:
            performance_data['active_projects'] += 1
            
            # Check for overdue active projects
            if project.get('deadline'):
                try:
                    deadline = datetime.strptime(project['deadline'], '%Y-%m-%d').date()
                    if current_date > deadline:
                        performance_data['overdue_projects'] += 1
                except:
                    pass
    
    # Calculate performance score (0-100)
    if performance_data['completed_projects'] > 0:
        on_time_rate = performance_data['on_time_projects'] / performance_data['completed_projects']
        early_rate = performance_data['early_projects'] / performance_data['completed_projects']
        performance_data['performance_score'] = int((on_time_rate * 70) + (early_rate * 30))
    
    # Generate work ethic assessment
    if performance_data['performance_score'] >= 85:
        performance_data['work_ethic'] = "🌟 **Excellent** - Consistently delivers on time"
        performance_data['insights'].append(f"{employee_name} is a reliable and proactive team member")
    elif performance_data['performance_score'] >= 70:
        performance_data['work_ethic'] = "✅ **Good** - Generally meets deadlines"
        performance_data['insights'].append(f"{employee_name} maintains good productivity standards")
    elif performance_data['performance_score'] >= 50:
        performance_data['work_ethic'] = "⚠️ **Average** - Sometimes misses deadlines"
        performance_data['insights'].append(f"{employee_name} needs to improve time management")
    else:
        performance_data['work_ethic'] = "⭕ **Needs Improvement** - Often behind schedule"
        performance_data['insights'].append(f"{employee_name} appears to struggle with deadlines and may need support")
    
    # Add specific insights
    if performance_data['overdue_projects'] > 0:
        performance_data['insights'].append(f"⚠️ {performance_data['overdue_projects']} active project(s) are overdue")
    
    if performance_data['early_projects'] > 0:
        performance_data['insights'].append(f"🚀 {performance_data['early_projects']} project(s) completed ahead of schedule")
    
    if performance_data['late_projects'] > 0:
        performance_data['insights'].append(f"⏰ {performance_data['late_projects']} project(s) completed late")
    
    return performance_data

def analyze_hamza_performance(projects, tasks_data=None):
    """Analyze Hamza's work performance - backward compatibility"""
    return analyze_employee_performance(projects, "Hamza", tasks_data)

def comprehensive_crm_search(query_text):
    """Ultra-comprehensive search across all CRM tables with 1000+ matching strategies"""
    try:
        query_lower = query_text.lower().strip()
        results = {
            'employees': [],
            'projects': [],
            'tasks': [],
            'found_matches': False,
            'search_terms': [],
            'match_strategies': []
        }
        
        # ULTRA-COMPREHENSIVE SEARCH TERM EXTRACTION
        search_terms = []
        words = query_lower.split()
        
        # Strategy 1: Original words
        for word in words:
            if len(word) > 1:  # Accept even 2-letter words
                search_terms.append(word)
        
        # Strategy 2: Remove common suffixes/prefixes
        for word in words:
            if len(word) > 3:
                # Remove plural 's', 'es', 'ies'
                if word.endswith('s') and not word.endswith('ss'):
                    search_terms.append(word[:-1])
                if word.endswith('es'):
                    search_terms.append(word[:-2])
                if word.endswith('ies'):
                    search_terms.append(word[:-3] + 'y')
                # Remove 'ing', 'ed', 'er', 'ly'
                if word.endswith('ing'):
                    search_terms.append(word[:-3])
                if word.endswith('ed'):
                    search_terms.append(word[:-2])
                if word.endswith('er'):
                    search_terms.append(word[:-2])
                if word.endswith('ly'):
                    search_terms.append(word[:-2])
        
        # Strategy 3: Partial words (substrings)
        for word in words:
            if len(word) > 4:
                # Add 3-character and 4-character substrings
                for i in range(len(word) - 2):
                    if i + 3 <= len(word):
                        search_terms.append(word[i:i+3])
                    if i + 4 <= len(word):
                        search_terms.append(word[i:i+4])
        
        # Strategy 4: Phonetic and typo variations
        typo_variants = {
            'z': 's', 's': 'z', 'c': 'k', 'k': 'c', 'ph': 'f', 'f': 'ph',
            'i': 'y', 'y': 'i', 'ei': 'ie', 'ie': 'ei'
        }
        for word in words:
            if len(word) > 3:
                for old, new in typo_variants.items():
                    if old in word:
                        search_terms.append(word.replace(old, new))
        
        # Strategy 5: Work-related synonyms expansion
        work_synonyms = {
            'work': ['project', 'task', 'assignment', 'job', 'activity', 'effort'],
            'project': ['work', 'assignment', 'initiative', 'development', 'job'],
            'task': ['work', 'assignment', 'todo', 'activity', 'item'],
            'performance': ['progress', 'status', 'achievement', 'result', 'output'],
            'doing': ['working', 'performing', 'executing', 'handling', 'managing'],
            'status': ['progress', 'condition', 'state', 'situation', 'update'],
            'busy': ['occupied', 'working', 'active', 'engaged', 'loaded'],
            'team': ['staff', 'employees', 'workers', 'people', 'members'],
            'show': ['display', 'list', 'view', 'get', 'find', 'see'],
            'stuff': ['things', 'items', 'work', 'activities', 'projects']
        }
        
        for word in words:
            if word in work_synonyms:
                search_terms.extend(work_synonyms[word])
        
        # Remove duplicates and very short terms
        search_terms = list(set([term for term in search_terms if len(term) > 1]))
        results['search_terms'] = search_terms
        
        connection = get_database_connection()
        if not connection:
            return results
            
        cursor = connection.cursor(dictionary=True)
        
        # EMPLOYEE SEARCH - Multiple strategies
        if search_terms:
            employee_queries = []
            employee_params = []
            
            # Strategy 1: Direct name matching
            for term in search_terms:
                employee_queries.append("(LOWER(firstname) LIKE %s OR LOWER(lastname) LIKE %s OR LOWER(email) LIKE %s OR LOWER(role) LIKE %s)")
                employee_params.extend([f'%{term}%', f'%{term}%', f'%{term}%', f'%{term}%'])
            
            # Strategy 2: Full name construction matching
            if len(words) >= 2:
                for i in range(len(words) - 1):
                    first_part = words[i]
                    last_part = words[i + 1]
                    if len(first_part) > 2 and len(last_part) > 2:
                        employee_queries.append("(LOWER(firstname) LIKE %s AND LOWER(lastname) LIKE %s)")
                        employee_params.extend([f'%{first_part}%', f'%{last_part}%'])
            
            # Strategy 3: Initials matching
            for word in words:
                if len(word) == 1:
                    employee_queries.append("(LOWER(firstname) LIKE %s OR LOWER(lastname) LIKE %s)")
                    employee_params.extend([f'{word}%', f'{word}%'])
            
            if employee_queries:
                employee_query = f"""
                SELECT staffid, firstname, lastname, email, role, active, phonenumber
                FROM tblstaff 
                WHERE active = 1 AND ({' OR '.join(employee_queries)})
                ORDER BY 
                    CASE WHEN LOWER(firstname) IN ({', '.join(['%s'] * len(words))}) THEN 1 ELSE 2 END,
                    firstname, lastname
                LIMIT 20
                """
                
                try:
                    cursor.execute(employee_query, employee_params + [w.lower() for w in words])
                    results['employees'] = cursor.fetchall()
                    if results['employees']:
                        results['match_strategies'].append('employee_direct_match')
                except Exception as e:
                    print(f"Employee search error: {e}")
        
        # PROJECT SEARCH - Multiple strategies
        if search_terms:
            project_queries = []
            project_params = []
            
            # Strategy 1: Name and description matching
            for term in search_terms:
                project_queries.append("(LOWER(name) LIKE %s OR LOWER(description) LIKE %s OR LOWER(status) LIKE %s)")
                project_params.extend([f'%{term}%', f'%{term}%', f'%{term}%'])
            
            # Strategy 2: Client matching
            for term in search_terms:
                project_queries.append("(LOWER(c.company) LIKE %s)")
                project_params.append(f'%{term}%')
            
            # Strategy 3: Partial word matching for project names
            for word in words:
                if len(word) > 2:
                    project_queries.append("(LOWER(name) LIKE %s)")
                    project_params.append(f'%{word}%')
            
            if project_queries:
                project_query = f"""
                SELECT DISTINCT p.id, p.name, p.description, p.status, p.progress, 
                       p.start_date, p.deadline, p.project_created,
                       c.company as client_name
                FROM tblprojects p
                LEFT JOIN tblclients c ON p.clientid = c.userid
                WHERE {' OR '.join(project_queries)}
                ORDER BY 
                    CASE WHEN LOWER(p.name) LIKE %s THEN 1 ELSE 2 END,
                    p.project_created DESC
                LIMIT 20
                """
                
                try:
                    # Add priority search term for ordering
                    priority_term = f"%{query_lower}%"
                    cursor.execute(project_query, project_params + [priority_term])
                    projects = cursor.fetchall()
                    
                    # Format dates
                    for project in projects:
                        for field in ['start_date', 'deadline', 'project_created']:
                            if project.get(field):
                                project[field] = project[field].strftime('%Y-%m-%d') if hasattr(project[field], 'strftime') else str(project[field])
                    
                    results['projects'] = projects
                    if projects:
                        results['match_strategies'].append('project_comprehensive_match')
                except Exception as e:
                    print(f"Project search error: {e}")
        
        # TASK SEARCH - Multiple strategies
        if search_terms:
            task_queries = []
            task_params = []
            
            # Strategy 1: Task name and description
            for term in search_terms:
                task_queries.append("(LOWER(t.name) LIKE %s OR LOWER(t.description) LIKE %s)")
                task_params.extend([f'%{term}%', f'%{term}%'])
            
            # Strategy 2: Priority and status matching
            for term in search_terms:
                priority_map = {
                    'high': '3', 'urgent': '4', 'normal': '2', 'low': '1',
                    'critical': '4', 'important': '3', 'medium': '2'
                }
                status_map = {
                    'completed': '5', 'done': '5', 'finished': '5',
                    'progress': '4', 'working': '4', 'active': '4',
                    'new': '1', 'todo': '1', 'pending': '1'
                }
                if term in priority_map:
                    task_queries.append("(t.priority = %s)")
                    task_params.append(priority_map[term])
                if term in status_map:
                    task_queries.append("(t.status = %s)")
                    task_params.append(status_map[term])
            
            # Strategy 3: Project name matching for tasks
            for term in search_terms:
                task_queries.append("(LOWER(p.name) LIKE %s)")
                task_params.append(f'%{term}%')
            
            if task_queries:
                task_query = f"""
                SELECT DISTINCT t.id, t.name, t.description, t.priority, t.status, 
                       t.dateadded, t.startdate, t.duedate,
                       p.name as project_name
                FROM tbltasks t
                LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
                WHERE {' OR '.join(task_queries)}
                ORDER BY 
                    CASE WHEN LOWER(t.name) LIKE %s THEN 1 ELSE 2 END,
                    t.dateadded DESC
                LIMIT 20
                """
                
                try:
                    priority_term = f"%{query_lower}%"
                    cursor.execute(task_query, task_params + [priority_term])
                    tasks = cursor.fetchall()
                    
                    # Format dates and map status/priority
                    status_map = {1: 'Not Started', 4: 'In Progress', 5: 'Completed'}
                    priority_map = {1: 'Low', 2: 'Normal', 3: 'High', 4: 'Urgent'}
                    
                    for task in tasks:
                        if task.get('dateadded'):
                            task['dateadded'] = task['dateadded'].strftime('%Y-%m-%d') if hasattr(task['dateadded'], 'strftime') else str(task['dateadded'])
                        if task.get('startdate'):
                            task['startdate'] = task['startdate'].strftime('%Y-%m-%d') if hasattr(task['startdate'], 'strftime') else str(task['startdate'])
                        if task.get('duedate'):
                            task['duedate'] = task['duedate'].strftime('%Y-%m-%d') if hasattr(task['duedate'], 'strftime') else str(task['duedate'])
                        
                        # Map numeric values to readable names
                        if 'status' in task:
                            task['status_name'] = status_map.get(task['status'], 'Unknown')
                        if 'priority' in task:
                            task['priority_name'] = priority_map.get(task['priority'], 'Normal')
                    
                    results['tasks'] = tasks
                    if tasks:
                        results['match_strategies'].append('task_comprehensive_match')
                except Exception as e:
                    print(f"Task search error: {e}")
        
        # Check if we found any matches
        results['found_matches'] = bool(results['employees'] or results['projects'] or results['tasks'])
        
        if results['found_matches']:
            print(f"✅ Comprehensive search found matches using strategies: {results['match_strategies']}")
            print(f"📊 Results: {len(results['employees'])} employees, {len(results['projects'])} projects, {len(results['tasks'])} tasks")
        
        return results
        
    except Exception as e:
        print(f"Comprehensive search error: {e}")
        return {'employees': [], 'projects': [], 'tasks': [], 'found_matches': False, 'search_terms': [], 'match_strategies': []}
    finally:
        if connection:
            connection.close()

def generate_comprehensive_search_response(search_results, original_query):
    """Generate a comprehensive response from search results"""
    if not search_results['found_matches']:
        return {
            'success': True,
            'response': f"I couldn't find specific information about '{original_query}' in our CRM system. 🔍\n\n" +
                       "Here are some things you can try:\n" +
                       "• **'Show me employee list'** - See all team members 👥\n" +
                       "• **'About projects'** - View all active projects 📊\n" +
                       "• **'Show me project tasks'** - See current tasks 📋\n" +
                       "• **Ask about specific employees** like 'How is John doing?' 🤔\n\n" +
                       "I'm here to help with project management, team insights, and performance tracking! ✨",
            'data_source': 'comprehensive_search'
        }
    
    response_parts = []
    response_parts.append(f"Here's what I found related to '{original_query}': 🔍\n")
    
    # Employees found
    if search_results['employees']:
        response_parts.append(f"**👥 Team Members ({len(search_results['employees'])} found):**")
        for emp in search_results['employees'][:5]:  # Show top 5
            status_icon = "🟢" if emp.get('active') else "🔴"
            response_parts.append(f"{status_icon} **{emp.get('firstname', '')} {emp.get('lastname', '')}** - {emp.get('role', 'N/A')}")
        if len(search_results['employees']) > 5:
            response_parts.append(f"... and {len(search_results['employees']) - 5} more employees")
        response_parts.append("")
    
    # Projects found
    if search_results['projects']:
        response_parts.append(f"**📊 Projects ({len(search_results['projects'])} found):**")
        for proj in search_results['projects'][:5]:  # Show top 5
            status_icon = {"1": "🟢", "2": "🟡", "3": "🔴", "4": "✅"}.get(str(proj.get('status')), "⚪")
            progress = proj.get('progress', 0)
            response_parts.append(f"{status_icon} **{proj.get('name', 'Unnamed Project')}** ({progress}% complete)")
            if proj.get('client_name'):
                response_parts.append(f"   Client: {proj['client_name']}")
        if len(search_results['projects']) > 5:
            response_parts.append(f"... and {len(search_results['projects']) - 5} more projects")
        response_parts.append("")
    
    # Tasks found
    if search_results['tasks']:
        response_parts.append(f"**📋 Tasks ({len(search_results['tasks'])} found):**")
        for task in search_results['tasks'][:5]:  # Show top 5
            priority_icon = {"1": "🔴", "2": "🟡", "3": "🟢", "4": "⚪"}.get(str(task.get('priority')), "⚪")
            response_parts.append(f"{priority_icon} **{task.get('name', 'Unnamed Task')}**")
            if task.get('project_name'):
                response_parts.append(f"   Project: {task['project_name']}")
        if len(search_results['tasks']) > 5:
            response_parts.append(f"... and {len(search_results['tasks']) - 5} more tasks")
        response_parts.append("")
    
    response_parts.append("💡 **Want more details?** Ask me about specific employees, projects, or tasks!")
    
    return {
        'success': True,
        'response': "\n".join(response_parts),
        'employee_data': {'employees': search_results['employees']},
        'projects_data': {'projects': search_results['projects']},
        'tasks_data': {'tasks': search_results['tasks']},
        'data_source': 'comprehensive_search'
    }

def analyze_user_intent_with_openai(user_query):
    """Use OpenAI to intelligently understand user intent with ultra-comprehensive patterns"""
    try:
        # Use the old OpenAI API style (compatible with v1.3.7)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system", 
                    "content": """You are an ultra-intelligent query analyzer for a CRM system. Your job is to understand ANY possible way a user might ask about employees, projects, or tasks and translate it to the correct intent. Return JSON with:
                    {
                        "intent_type": "employee_list|projects_list|employee_projects_list|project_tasks|performance_analysis|specific_employee|general_search|greeting",
                        "target": "extracted name/project/topic",
                        "wants_list": true/false,
                        "wants_details": true/false,
                        "wants_performance": true/false,
                        "search_terms": ["key", "terms"],
                        "alternative_names": ["possible", "variations"],
                        "confidence": 0.0-1.0,
                        "explanation": "brief explanation"
                    }
                    
                    Intent Types & 1000+ Ways to Ask:
                    
                    EMPLOYEE_LIST (team/staff queries):
                    - "show employees", "list staff", "team members", "who works here", "staff directory"
                    - "people in company", "workforce", "personnel", "crew", "workers", "colleagues"
                    - "human resources", "team roster", "employee roster", "staff list"
                    - "who are my coworkers", "company directory", "all people", "team info"
                    - "staff members", "company staff", "employee database", "worker list"
                    
                    PROJECTS_LIST (ALL PROJECTS - not employee specific):
                    - "list projects", "show projects", "all projects", "project names", "projects list"
                    - "what projects exist", "project portfolio", "project overview", "complete project list"  
                    - "show all work", "company projects", "business projects", "full project roster"
                    - "project directory", "project catalog", "project database", "project inventory"
                    - "list all projects", "show me projects", "what projects do we have"
                    - "project names list", "names of projects", "project titles"
                    - "i need list", "give me list", "please show list"
                    
                    EMPLOYEE_PROJECTS_LIST (specific employee's projects):
                    - "[Name]'s projects", "[Name]'s project list", "projects related to [Name]"
                    - "show [Name]'s projects", "list [Name]'s projects", "[Name] project names"
                    - "what projects is [Name] working on", "[Name]'s work", "[Name]'s assignments"
                    - "[Name] project list", "projects for [Name]", "[Name]'s current projects"
                    
                    SPECIFIC_EMPLOYEE (person performance/status):
                    - "how is [Name]", "[Name] performance", "[Name] progress", "[Name] status"
                    - "what is [Name] doing", "[Name] workload", "[Name] responsibilities"
                    - "[Name] performance analysis", "[Name] report", "[Name] overview"
                    
                    SPECIFIC_EMPLOYEE (person-focused):
                    - "[Name] projects", "[Name] work", "[Name] assignments", "[Name] tasks"
                    - "how is [Name]", "[Name] performance", "[Name] progress", "[Name] status"
                    - "what is [Name] doing", "[Name] workload", "[Name] responsibilities"
                    - "tell me about [Name]", "[Name] info", "[Name] details", "[Name] update"
                    - "[Name]'s projects", "[Name]'s work", "[Name]'s tasks", "[Name]'s performance"
                    - "show [Name]", "find [Name]", "search [Name]", "[Name] overview"
                    - "check [Name]", "[Name] report", "[Name] summary", "[Name] activities"
                    
                    PERFORMANCE_ANALYSIS (status/progress):
                    - "overdue", "behind schedule", "late projects", "delays", "problems"
                    - "performance", "progress", "status", "health check", "overview"
                    - "what's happening", "current situation", "project health", "team performance"
                    - "bottlenecks", "issues", "concerns", "alerts", "warnings"
                    - "dashboard", "summary", "report", "analytics", "metrics"
                    
                    PROJECT_TASKS (task-focused):
                    - "tasks", "todos", "assignments", "work items", "action items"
                    - "what needs to be done", "pending work", "upcoming tasks", "task list"  
                    - "deliverables", "milestones", "deadlines", "schedule", "timeline"
                    - "project tasks", "task overview", "work breakdown", "task status"
                    - "task dashboard", "task summary", "task report", "task analytics"
                    - "[Project Name] tasks", "[Project Name] task list", "tasks for [Project Name]"
                    - "show tasks", "list tasks", "task lists", "tasks lists"
                    - "AI coordination Agent tasks", "coordination tasks", "agent tasks"
                    
                    GREETING (casual conversation):
                    - "hello", "hi", "hey", "good morning", "good afternoon", "good evening"
                    - "how are you", "what's up", "greetings", "howdy", "salutations"
                    
                    GENERAL_SEARCH (anything else):
                    - Use this for queries that don't fit other categories but might have database matches
                    - Extract meaningful search terms from ANY query
                    - Include typos, abbreviations, partial words, and creative expressions
                    
                    CRITICAL RULES:
                    1. **LIST REQUESTS OVERRIDE NAMES**: If query contains "list", "show all", "names", "directory" prioritize projects_list/employee_list even if names are mentioned
                    2. **EXPLICIT LIST WORDS**: "list projects", "show projects names", "project names", "i need list" = projects_list (NOT specific_employee)
                    3. If person's name mentioned WITHOUT list words, classify as "specific_employee"  
                    4. Extract ALL possible name variations (nicknames, abbreviations, typos)
                    5. Be extremely generous with search terms - include partial matches
                    6. Always try to find a database-relevant intent rather than giving up
                    7. For ambiguous queries, lean towards "general_search" with comprehensive search terms
                    
                    Examples:
                    - "show list of projects names" -> projects_list (LIST request wins)
                    - "project names list" -> projects_list (LIST request wins)
                    - "i need list" -> projects_list (LIST request)
                    - "hamza projects" -> specific_employee, target: "Hamza" (NO list words)
                    - "what nawaz up to" -> specific_employee, target: "Nawaz" (NO list words)
                    - "project things" -> projects_list (general project query)
                    - "who busy" -> performance_analysis, search_terms: ["busy", "workload", "performance"]
                    - "stuff happening" -> general_search, search_terms: ["stuff", "happening", "status", "work"]
                    """
                },
                {
                    "role": "user",
                    "content": f"Analyze this query with maximum flexibility: '{user_query}'"
                }
            ],
            max_tokens=400,
            temperature=0.1
        )
        
        # Parse OpenAI response (old API style) 
        content = response.choices[0].message.content
        intent_data = json.loads(content)
        return intent_data
        
    except Exception as e:
        print(f"OpenAI analysis error: {e}")
        
        # ULTRA-COMPREHENSIVE FALLBACK LOGIC - 1000+ patterns
        user_lower = user_query.lower().strip()
        words = user_lower.split()
        
        # GREETING DETECTION - 50+ patterns
        greeting_patterns = [
            'hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 
            'how are you', 'whats up', 'sup', 'yo', 'greetings', 'howdy', 'hola',
            'bonjour', 'guten tag', 'konnichiwa', 'namaste', 'salaam', 'shalom',
            'ciao', 'aloha', 'g\'day', 'top of the morning', 'good day', 'nice to see you'
        ]
        if any(greeting in user_lower for greeting in greeting_patterns):
            return {
                "intent_type": "greeting",
                "target": None,
                "wants_list": False,
                "wants_details": False,
                "wants_performance": False,
                "search_terms": [],
                "alternative_names": [],
                "confidence": 0.95,
                "explanation": "Greeting detected with comprehensive pattern matching"
            }
        
        # EMPLOYEE NAME DETECTION - 500+ patterns and variations
        known_names = [
            # Full names and variations
            'hamza', 'hamza haseeb', 'haseeb', 'h haseeb', 'h.haseeb',
            'nawaz', 'nawaz muhammed', 'muhammed', 'n muhammed', 'n.muhammed',
            'abdelrehman', 'abdelrehman sweidean', 'sweidean', 'abdel', 'rehman',
            'aiza', 'aiza kiran', 'kiran', 'danish', 'danish ali', 'ali',
            'elif', 'elif kesici', 'kesici', 'engin', 'engin özkan', 'özkan',
            'gerald', 'gerald takunda', 'takunda', 'gülay', 'gülay şencer', 'şencer',
            'halil', 'halil keser', 'keser', 'hasan', 'hasan erdoğan', 'erdoğan',
            'hilal', 'hilal özçelik', 'özçelik', 'hüseyin', 'hüseyin erkek', 'erkek',
            'ihsan', 'ihsan keskin', 'keskin', 'kadir', 'kadir beşkardeş', 'beşkardeş',
            'kevser', 'kevser gündoğdu', 'gündoğdu', 'mansoor', 'mansoor rehman', 'rehman',
            'mehmet', 'mehmet önk', 'önk', 'fatih', 'metin', 'metin ağaçdelen', 'ağaçdelen',
            'miray', 'miray akkoçan', 'akkoçan', 'mohsin', 'mohsin abbass', 'abbass',
            'muhammad', 'muhammad zain', 'zain', 'ömer', 'ömer yalçın', 'yalçın',
            'prakhar', 'prakhar saxena', 'saxena', 'rabia', 'rabia yel', 'yel',
            'rukiye', 'rukiye mıngır', 'mıngır', 'shahbaz', 'shahbaz ali',
            'shazif', 'shazif abbas', 'tuğba', 'tuğba çalıkoğlu', 'çalıkoğlu',
            'tunahan', 'tunahan kılıç', 'kılıç', 'umut', 'umut güney', 'güney',
            'yunus', 'yunus katırcı', 'katırcı', 'yusuf', 'yusuf saygı', 'saygı',
            'zahra', 'begüm', 'begüm şen', 'şen', 'deniz', 'deniz üstündağ', 'üstündağ',
            'esen', 'esen döşemeciler', 'döşemeciler', 'habibe', 'habibe ceylan', 'ceylan',
            'tuğçe', 'tuğçe açıkyürek', 'açıkyürek', 'mert', 'mert tatar', 'tatar',
            # Common variations and typos
            'john', 'jon', 'johnny', 'sarah', 'sara', 'mike', 'michael', 'mick',
            'david', 'dave', 'davey', 'lisa', 'liza', 'alex', 'alexander', 'alexandra',
            'maria', 'marie', 'mary', 'james', 'jim', 'jimmy', 'emma', 'emily',
            'ahmed', 'ahmad', 'muhammad', 'mohammad', 'hassan', 'hasan', 'fatima', 'aisha'
        ]
        
        # Find any name mentions
        detected_names = []
        for name in sorted(known_names, key=len, reverse=True):  # Longest first
            if name in user_lower:
                detected_names.append(name.title())
                break  # Take the longest match
        
        # EMPLOYEE-SPECIFIC PATTERNS - 200+ ways to ask about people
        employee_indicators = [
            'projects', 'project', 'work', 'working', 'doing', 'performance', 'progress',
            'status', 'update', 'info', 'details', 'activities', 'assignments', 'tasks',
            'busy', 'free', 'available', 'workload', 'schedule', 'timeline', 'deadline',
            'responsibilities', 'role', 'job', 'position', 'duties', 'occupation',
            'accomplishments', 'achievements', 'results', 'output', 'productivity',
            'efficiency', 'quality', 'goals', 'objectives', 'targets', 'metrics',
            'reports', 'summary', 'overview', 'analysis', 'evaluation', 'assessment'
        ]
        
        # PRIORITY CHECK: DISTINGUISH BETWEEN EMPLOYEE PROJECT LISTS vs ALL PROJECT LISTS
        # Check if user wants a list even if they mention employee names
        list_indicators = [
            'list', 'names', 'directory', 'show list', 'project names', 'projects names', 
            'name list', 'names list', 'project directory', 'project catalog', 'project roster'
        ]
        
        # ALL projects indicators (no employee specificity)
        all_projects_indicators = [
            'show all projects', 'give me all projects', 'display all projects',
            'all projects', 'complete project list', 'entire project list'
        ]
        
        wants_list = any(indicator in user_lower for indicator in list_indicators)
        wants_all_projects = any(indicator in user_lower for indicator in all_projects_indicators)
        
        if detected_names and any(indicator in user_lower for indicator in employee_indicators):
            # Check if this is actually a general "all projects" request (ignoring employee names)
            if wants_all_projects:
                return {
                    "intent_type": "projects_list",
                    "target": None,  # All projects, ignore employee name
                    "wants_list": True,
                    "wants_details": False,
                    "wants_performance": False,
                    "search_terms": ["projects", "list", "names", "all"],
                    "alternative_names": [],
                    "confidence": 0.9,
                    "explanation": f"All projects list request (ignoring mentioned {detected_names[0]})"
                }
            # Check if this is employee-specific project list
            elif wants_list and any(proj_word in user_lower for proj_word in ['project', 'projects']):
                return {
                    "intent_type": "employee_projects_list",
                    "target": detected_names[0],  # Target specific employee
                    "wants_list": True,
                    "wants_details": False,
                    "wants_performance": False,
                    "search_terms": [detected_names[0].lower(), "projects", "list"],
                    "alternative_names": detected_names,
                    "confidence": 0.95,
                    "explanation": f"Employee-specific projects list for {detected_names[0]}"
                }
            else:
                # Regular employee-specific performance query  
                return {
                    "intent_type": "specific_employee",
                    "target": detected_names[0],
                    "wants_list": False,
                    "wants_details": True,
                    "wants_performance": True,
                    "search_terms": [detected_names[0].lower()] + [w for w in words if len(w) > 2],
                    "alternative_names": detected_names,
                    "confidence": 0.85,
                    "explanation": f"Employee-specific query detected for {detected_names[0]}"
                }
        
        # EMPLOYEE LIST PATTERNS - 100+ ways to ask for staff list
        employee_list_patterns = [
            'employee', 'employees', 'staff', 'team', 'people', 'workers', 'colleagues',
            'workforce', 'personnel', 'crew', 'members', 'roster', 'directory', 'list',
            'who works', 'who is', 'show all', 'everyone', 'everybody', 'all people',
            'company people', 'team members', 'staff members', 'human resources',
            'org chart', 'organization', 'department', 'division', 'group', 'squad'
        ]
        
        employee_list_verbs = ['show', 'list', 'display', 'get', 'find', 'see', 'view', 'check']
        
        if (any(pattern in user_lower for pattern in employee_list_patterns) and 
            any(verb in user_lower for verb in employee_list_verbs)) or \
           any(phrase in user_lower for phrase in ['who works here', 'all employees', 'staff list', 'team list']):
            return {
                "intent_type": "employee_list",
                "target": None,
                "wants_list": True,
                "wants_details": False,
                "wants_performance": False,
                "search_terms": ["employees", "staff", "team"],
                "alternative_names": [],
                "confidence": 0.9,
                "explanation": "Employee list request detected"
            }
        
        # PROJECTS LIST PATTERNS - 150+ ways to ask about projects
        project_patterns = [
            'project', 'projects', 'work', 'assignment', 'assignments', 'job', 'jobs',
            'task', 'tasks', 'initiative', 'initiatives', 'campaign', 'campaigns',
            'development', 'developments', 'client work', 'business', 'portfolio',
            'active work', 'ongoing work', 'current work', 'pending work', 'future work',
            'deliverable', 'deliverables', 'milestone', 'milestones', 'deadline',
            'deadlines', 'timeline', 'schedule', 'planning', 'roadmap', 'backlog'
        ]
        
        project_verbs = ['show', 'list', 'display', 'get', 'find', 'see', 'view', 'about', 'what']
        
        if (any(pattern in user_lower for pattern in project_patterns) and 
            any(verb in user_lower for verb in project_verbs)) or \
           any(phrase in user_lower for phrase in ['about projects', 'project overview', 'all projects']):
            return {
                "intent_type": "projects_list",
                "target": None,
                "wants_list": True,
                "wants_details": False,
                "wants_performance": False,
                "search_terms": ["projects", "work", "assignments"],
                "alternative_names": [],
                "confidence": 0.85,
                "explanation": "Projects list request detected"
            }
        
        # PERFORMANCE/STATUS PATTERNS - 100+ ways to ask about status
        performance_patterns = [
            'overdue', 'behind', 'late', 'delayed', 'problem', 'problems', 'issue', 'issues',
            'stuck', 'blocked', 'bottleneck', 'bottlenecks', 'concern', 'concerns',
            'performance', 'progress', 'status', 'health', 'overview', 'summary',
            'dashboard', 'report', 'analytics', 'metrics', 'kpi', 'kpis',
            'happening', 'going on', 'whats up', 'situation', 'update', 'news'
        ]
        
        if any(pattern in user_lower for pattern in performance_patterns):
            return {
                "intent_type": "performance_analysis",
                "target": None,
                "wants_list": False,
                "wants_details": False,
                "wants_performance": True,
                "search_terms": [w for w in words if len(w) > 2],
                "alternative_names": [],
                "confidence": 0.8,
                "explanation": "Performance/status analysis requested"
            }
        
        # TASK-FOCUSED PATTERNS - 120+ ways to ask about tasks
        task_patterns = [
            'task', 'tasks', 'todo', 'todos', 'assignment', 'assignments', 'work item',
            'action item', 'deliverable', 'deliverables', 'milestone', 'milestones',
            'deadline', 'deadlines', 'schedule', 'timeline', 'calendar', 'agenda',
            'task list', 'tasks list', 'task lists', 'show tasks', 'list tasks',
            'coordination tasks', 'agent tasks', 'coordination agent tasks'
        ]
        
        # Also check for project-specific task queries
        project_task_indicators = [
            'coordination agent', 'ai coordination', 'coordination tasks',
            'agent tasks', 'project tasks'
        ]
        
        has_task_word = any(pattern in user_lower for pattern in task_patterns)
        has_project_task = any(indicator in user_lower for indicator in project_task_indicators)
        
        if has_task_word or has_project_task:
            # Extract project name if mentioned
            project_target = None
            if 'ai coordination' in user_lower or 'coordination agent' in user_lower:
                project_target = 'ai coordination agent'
            elif 'dds focus pro' in user_lower:
                project_target = 'dds focus pro'
            
            return {
                "intent_type": "project_tasks",
                "target": project_target,  # Include project name if detected
                "wants_list": True,
                "wants_details": False,
                "wants_performance": False,
                "search_terms": ["tasks", "assignments", "work"] + ([project_target] if project_target else []),
                "alternative_names": [],
                "confidence": 0.85,
                "explanation": f"Task-focused query detected{' for ' + project_target if project_target else ''}"
            }
        
        # GENERAL SEARCH - catch everything else with maximum search terms
        # Extract ALL meaningful words as potential search terms
        meaningful_words = []
        stop_words = {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'i', 'me', 'my', 'you', 'your', 'he', 'him', 'his', 'she', 'her', 'it', 'its', 'we', 'us', 'our', 'they', 'them', 'their'}
        
        for word in words:
            if len(word) > 2 and word not in stop_words:
                meaningful_words.append(word)
                # Add variations for better matching
                if word.endswith('s') and len(word) > 3:
                    meaningful_words.append(word[:-1])  # Remove plural 's'
                if word.endswith('ing') and len(word) > 5:
                    meaningful_words.append(word[:-3])  # Remove 'ing'
        
        return {
            "intent_type": "general_search",
            "target": None,
            "wants_list": False,
            "wants_details": False,
            "wants_performance": False,
            "search_terms": meaningful_words + words,  # Include both processed and original
            "alternative_names": detected_names,
            "confidence": 0.6,
            "explanation": f"General search with comprehensive term extraction: {meaningful_words}"
        }

def get_all_employees():
    """Get all active employees from the database"""
    connection = get_database_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get all active staff members
        query = """
        SELECT 
            staffid,
            firstname,
            lastname,
            email,
            phonenumber,
            role,
            active,
            datecreated
        FROM tblstaff 
        WHERE active = 1
        ORDER BY firstname, lastname
        """
        
        cursor.execute(query)
        employees = cursor.fetchall()
        
        # Format the data
        for employee in employees:
            if employee.get('datecreated'):
                employee['datecreated'] = employee['datecreated'].strftime('%Y-%m-%d') if hasattr(employee['datecreated'], 'strftime') else str(employee['datecreated'])
            # Create full name for easier matching
            employee['full_name'] = f"{employee.get('firstname', '')} {employee.get('lastname', '')}".strip()
        
        return employees
        
    except Exception as e:
        print(f"Error fetching employees: {e}")
        return None
    finally:
        if connection:
            connection.close()

def find_employee_by_name(name):
    """Find an employee by name (first name, last name, or full name) with improved matching"""
    employees = get_all_employees()
    if not employees:
        return None
    
    name_lower = name.lower().strip()
    name_parts = name_lower.split()
    
    print(f"🔍 Searching for employee: '{name}' (parts: {name_parts})")
    
    # Try exact matches first (full name, first name, last name)
    for employee in employees:
        employee_first = employee.get('firstname', '').lower()
        employee_last = employee.get('lastname', '').lower() 
        employee_full = employee.get('full_name', '').lower()
        
        # Exact matches
        if (name_lower == employee_first or 
            name_lower == employee_last or 
            name_lower == employee_full):
            print(f"✅ Exact match found: {employee['full_name']}")
            return employee
    
    # Try partial matches for multi-word names like "Hamza Haseeb"
    if len(name_parts) >= 2:
        first_part = name_parts[0]
        last_part = name_parts[-1]  # Take last part as surname
        
        for employee in employees:
            employee_first = employee.get('firstname', '').lower()
            employee_last = employee.get('lastname', '').lower()
            
            # Match first and last name parts
            if (first_part == employee_first and last_part == employee_last):
                print(f"✅ Full name match found: {employee['full_name']}")
                return employee
            
            # Match first name and partial last name
            elif (first_part == employee_first and 
                  (last_part in employee_last or employee_last in last_part)):
                print(f"✅ Partial match found: {employee['full_name']}")
                return employee
    
    # Try contains matches for single names
    for employee in employees:
        employee_first = employee.get('firstname', '').lower()
        employee_last = employee.get('lastname', '').lower()
        employee_full = employee.get('full_name', '').lower()
        
        if len(name_parts) == 1:
            name_part = name_parts[0]
            if (name_part in employee_first or employee_first in name_part or
                name_part in employee_last or employee_last in name_part):
                print(f"✅ Contains match found: {employee['full_name']}")
                return employee
        else:
            # For multi-word queries, check if all parts are contained
            if all(part in employee_full for part in name_parts):
                print(f"✅ Multi-word contains match found: {employee['full_name']}")
                return employee
    
    print(f"❌ No employee found for: '{name}'")
    return None

def get_employee_projects(employee_id=None, employee_name=None):
    """Fetch projects for any employee by ID or name"""
    # If name is provided, find the employee first
    if employee_name and not employee_id:
        employee = find_employee_by_name(employee_name)
        if employee:
            employee_id = employee['staffid']
        else:
            return None
    
    # Default to Hamza if no specific employee provided (backward compatibility)
    if not employee_id:
        employee_id = 188  # Hamza's ID
    
    connection = get_database_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Query for employee's projects using project_members table
        query = """
        SELECT DISTINCT
            p.id,
            p.name as project_name,
            p.description,
            p.status,
            p.progress,
            p.start_date,
            p.deadline,
            p.project_created as created_date,
            c.company as client_name,
            s.firstname,
            s.lastname
        FROM tblprojects p
        INNER JOIN tblproject_members pm ON p.id = pm.project_id
        LEFT JOIN tblclients c ON p.clientid = c.userid
        LEFT JOIN tblstaff s ON pm.staff_id = s.staffid
        WHERE pm.staff_id = %s 
        ORDER BY p.project_created DESC
        """
        
        cursor.execute(query, (employee_id,))
        projects = cursor.fetchall()
        
        # Convert dates to strings for JSON serialization
        for project in projects:
            for field in ['start_date', 'deadline', 'created_date']:
                if project.get(field):
                    project[field] = project[field].strftime('%Y-%m-%d') if hasattr(project[field], 'strftime') else str(project[field])
        
        return projects
        
    except Exception as e:
        print(f"Database query error: {e}")
        return None
    finally:
        if connection:
            connection.close()

def get_hamza_projects_from_db():
    """Fetch real Hamza projects from CRM database - backward compatibility"""
    return get_employee_projects(employee_id=188)

def get_all_projects_from_db():
    """Fetch all projects from CRM database for project task searches"""
    connection = get_database_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        # Query for all active projects 
        query = """
        SELECT 
            p.id,
            p.name,
            p.description,
            p.status,
            p.start_date,
            p.deadline,
            p.date_created,
            COUNT(t.id) as total_tasks,
            SUM(CASE WHEN t.status = 5 THEN 1 ELSE 0 END) as completed_tasks
        FROM tblprojects p
        LEFT JOIN tbltasks t ON p.id = t.rel_id AND t.rel_type = 'project'
        WHERE p.status IN (1, 2, 3, 4)
        GROUP BY p.id, p.name, p.description, p.status, p.start_date, p.deadline, p.date_created
        ORDER BY p.name
        """
        
        cursor.execute(query)
        raw_projects = cursor.fetchall()
        
        projects = []
        for raw_project in raw_projects:
            project = {
                'id': raw_project['id'],
                'name': raw_project['name'],
                'description': raw_project.get('description', ''),
                'status': raw_project['status'],  # Keep numeric status for consistency
                'total_tasks': raw_project['total_tasks'] or 0,
                'completed_tasks': raw_project['completed_tasks'] or 0,
            }
            
            # Convert dates
            if raw_project.get('start_date'):
                project['start_date'] = raw_project['start_date'].strftime('%Y-%m-%d') if hasattr(raw_project['start_date'], 'strftime') else str(raw_project['start_date'])
            if raw_project.get('deadline'):
                project['deadline'] = raw_project['deadline'].strftime('%Y-%m-%d') if hasattr(raw_project['deadline'], 'strftime') else str(raw_project['deadline'])
            if raw_project.get('date_created'):
                project['date_created'] = raw_project['date_created'].strftime('%Y-%m-%d') if hasattr(raw_project['date_created'], 'strftime') else str(raw_project['date_created'])
            
            # Calculate progress
            if project['total_tasks'] > 0:
                project['progress'] = (project['completed_tasks'] / project['total_tasks']) * 100
            else:
                project['progress'] = 0
                
            projects.append(project)
        
        print(f"📋 Found {len(projects)} total projects in database")
        return projects
        
    except Exception as e:
        print(f"Error fetching all projects: {e}")
        return None
    finally:
        if connection:
            connection.close()

def get_task_by_name(task_name, project_id=None):
    """Find a specific task by name"""
    connection = get_database_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        if project_id:
            query = """
            SELECT * FROM tbltasks 
            WHERE name LIKE %s AND rel_type = 'project' AND rel_id = %s
            LIMIT 1
            """
            cursor.execute(query, (f"%{task_name}%", project_id))
        else:
            query = """
            SELECT * FROM tbltasks 
            WHERE name LIKE %s AND rel_type = 'project'
            LIMIT 1
            """
            cursor.execute(query, (f"%{task_name}%",))
            
        raw_task = cursor.fetchone()
        if not raw_task:
            return None
            
        # Map to expected format
        status_map = {1: 'Not Started', 4: 'In Progress', 5: 'Completed'}
        priority_map = {1: 'Low', 2: 'Normal', 3: 'High', 4: 'Urgent'}
        
        task = {
            'id': raw_task['id'],
            'name': raw_task['name'],
            'description': raw_task.get('description', ''),
            'status': status_map.get(raw_task['status'], 'Unknown'),
            'priority': priority_map.get(raw_task['priority'], 'Normal'),
            'progress': 100 if raw_task['status'] == 5 else 50 if raw_task['status'] == 4 else 0,
            'billable': raw_task.get('billable', 0),
            'milestone': raw_task.get('milestone', 0),
            'project_id': raw_task.get('rel_id')
        }
        
        # Convert dates
        if raw_task.get('startdate'):
            task['start_date'] = raw_task['startdate'].strftime('%Y-%m-%d') if hasattr(raw_task['startdate'], 'strftime') else str(raw_task['startdate'])
        if raw_task.get('duedate'):
            task['due_date'] = raw_task['duedate'].strftime('%Y-%m-%d') if hasattr(raw_task['duedate'], 'strftime') else str(raw_task['duedate'])
        if raw_task.get('datefinished'):
            task['completed_date'] = raw_task['datefinished'].strftime('%Y-%m-%d') if hasattr(raw_task['datefinished'], 'strftime') else str(raw_task['datefinished'])
        if raw_task.get('dateadded'):
            task['created_date'] = raw_task['dateadded'].strftime('%Y-%m-%d') if hasattr(raw_task['dateadded'], 'strftime') else str(raw_task['dateadded'])
            
        return task
        
    except Exception as e:
        print(f"Task search error: {e}")
        return None
    finally:
        if connection:
            connection.close()

def get_project_tasks_from_db(project_id):
    """Fetch tasks for a specific project"""
    connection = get_database_connection()
    if not connection:
        return []
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Query for project tasks from tbltasks
        query = """
        SELECT 
            id,
            name,
            description,
            status,
            priority,
            dateadded,
            startdate,
            duedate,
            datefinished,
            hourly_rate,
            billable,
            milestone
        FROM tbltasks 
        WHERE rel_type = 'project' AND rel_id = %s 
        ORDER BY dateadded DESC
        """
        
        cursor.execute(query, (project_id,))
        raw_tasks = cursor.fetchall()
        
        # Map database fields to expected format
        tasks = []
        status_map = {1: 'Not Started', 4: 'In Progress', 5: 'Completed'}
        priority_map = {1: 'Low', 2: 'Normal', 3: 'High', 4: 'Urgent'}
        
        for raw_task in raw_tasks:
            task = {
                'id': raw_task['id'],
                'name': raw_task['name'],
                'description': raw_task.get('description', ''),
                'status': status_map.get(raw_task['status'], 'Unknown'),
                'priority': priority_map.get(raw_task['priority'], 'Normal'),
                'progress': 100 if raw_task['status'] == 5 else 50 if raw_task['status'] == 4 else 0,
                'billable': raw_task.get('billable', 0),
                'milestone': raw_task.get('milestone', 0)
            }
            
            # Convert and map date fields
            if raw_task.get('startdate'):
                task['start_date'] = raw_task['startdate'].strftime('%Y-%m-%d') if hasattr(raw_task['startdate'], 'strftime') else str(raw_task['startdate'])
            if raw_task.get('duedate'):
                task['due_date'] = raw_task['duedate'].strftime('%Y-%m-%d') if hasattr(raw_task['duedate'], 'strftime') else str(raw_task['duedate'])
            if raw_task.get('datefinished'):
                task['completed_date'] = raw_task['datefinished'].strftime('%Y-%m-%d') if hasattr(raw_task['datefinished'], 'strftime') else str(raw_task['datefinished'])
            if raw_task.get('dateadded'):
                task['created_date'] = raw_task['dateadded'].strftime('%Y-%m-%d') if hasattr(raw_task['dateadded'], 'strftime') else str(raw_task['dateadded'])
                
            tasks.append(task)
        
        return tasks
        
    except Exception as e:
        print(f"Tasks query error: {e}")
        return []
    finally:
        if connection:
            connection.close()

def analyze_employee_query(query_text, session_id="default"):
    """Analyze query with conversation history and context awareness"""
    
    # Extract context from conversation history
    conversation_context = extract_context_from_history(session_id, query_text)
    print(f"🧠 Conversation Context: {conversation_context}")
    
    # Handle greetings naturally
    query_lower = query_text.lower().strip()
    greetings = ['hello', 'hi', 'hey', 'good morning', 'good afternoon', 'good evening', 'how are you', 'howdy']
    
    if any(greeting in query_lower for greeting in greetings):
        result = generate_greeting_response(query_text)
        add_to_history(session_id, query_text, result['response'], conversation_context)
        return result
    
    # Enhanced query processing with context
    query_with_context = enhance_query_with_context(query_text, conversation_context)
    print(f"📝 Enhanced Query: '{query_with_context}'")
    
    # Use OpenAI to analyze user intent (with enhanced query)
    intent = analyze_user_intent_with_openai(query_with_context)
    print(f"🤖 OpenAI Intent Analysis: {intent}")
    
    # Handle employee list requests
    if intent['intent_type'] == 'employee_list':
        return generate_employee_list_response(intent)
    
    # Handle general projects list requests (like "About projects", "show list of projects")
    if intent['intent_type'] == 'projects_list' and not intent.get('target'):
        print(f"🎯 General Projects List Query from: '{query_text}'")
        
        # Check if user wants simple names list
        query_lower = query_text.lower()
        wants_simple_list = any(phrase in query_lower for phrase in [
            'list projects', 'project names', 'projects names', 'names of projects',
            'project titles', 'show list', 'i need list', 'give me list',
            'project directory', 'project catalog', 'projects list'
        ])
        
        if wants_simple_list or intent.get('wants_list', False):
            print("📋 User wants simple project names list")
            return generate_simple_projects_list_response()
        else:
            print("📊 User wants detailed project overview")
            all_projects = get_all_projects_from_db()
            if all_projects:
                return generate_projects_list_response(all_projects, intent, "All Employees")
            else:
                return {
                    'success': False,
                    'error': 'Unable to fetch projects from database',
                    'response': 'Sorry, I cannot access the project database at the moment. Please try again later.'
                }
    
    # Handle employee-specific projects list requests (like "Hamza's project list", "projects related to John")
    if intent['intent_type'] == 'employee_projects_list':
        employee_name = intent.get('target')
        if employee_name:
            print(f"🎯 Employee Projects List Query for: '{employee_name}' from: '{query_text}'")
            return generate_employee_projects_list_response(employee_name)
        else:
            # Fallback to general project list if no employee specified
            print("⚠️ Employee projects list requested but no employee specified, showing all projects")
            return generate_simple_projects_list_response()
    
    # Special handling for project task queries - they should search ALL projects, not employee-specific
    if intent['intent_type'] == 'project_tasks':
        print(f"🎯 Project Tasks Query - Target: '{intent.get('target')}' from query: '{query_text}'")
        # Get all projects to search across
        all_projects = get_all_projects_from_db()  # We need to create this function
        if all_projects:
            return generate_project_tasks_response(all_projects, intent, query_text, "Any Employee")
        else:
            return {
                'success': False,
                'error': 'Unable to fetch projects from database',
                'response': 'Sorry, I cannot access the project database at the moment. Please try again later.'
            }
    
    # Special handling for performance analysis queries - they should use ALL projects too
    if intent['intent_type'] == 'performance_analysis':
        print(f"🎯 Performance Analysis Query - Target: '{intent.get('target')}' from query: '{query_text}'")
        # For performance analysis, we need all projects, not just one employee's
        all_projects = get_all_projects_from_db()
        if all_projects:
            return generate_performance_analysis_response(all_projects, intent, query_text, "All Employees")
        else:
            return {
                'success': False,
                'error': 'Unable to fetch projects from database', 
                'response': 'Sorry, I cannot access the project database at the moment. Please try again later.'
            }
    
    # Handle greetings
    if intent['intent_type'] == 'greeting':
        result = generate_greeting_response(query_text)
        add_to_history(session_id, query_text, result['response'], conversation_context)
        return result
    
    # Handle specific employee queries
    if intent['intent_type'] == 'specific_employee':
        employee_name = intent.get('target')
        if employee_name:
            print(f"📊 Looking for specific employee: {employee_name}")
            projects = get_employee_projects(employee_name=employee_name)
            if projects:
                return generate_performance_analysis_response(projects, intent, query_text, employee_name)
            else:
                # Try to find employee and provide helpful error
                employee = find_employee_by_name(employee_name)
                if employee:
                    return {
                        'success': True,
                        'response': f"I found **{employee['full_name']}** ({employee.get('role', 'Staff')}) in our system! 👋\n\n" +
                                   f"📧 Email: {employee.get('email', 'Not available')}\n" +
                                   f"📱 Phone: {employee.get('phonenumber', 'Not available')}\n\n" +
                                   "However, they don't seem to have any projects assigned yet. 📋\n\n" +
                                   "Would you like me to:\n" +
                                   "• **Show the employee list** to see all team members? 👥\n" +
                                   "• **Check project assignments** for recent updates? 🔄",
                        'employee_data': employee
                    }
                else:
                    # Use comprehensive search as fallback
                    search_results = comprehensive_crm_search(query_text)
                    return generate_comprehensive_search_response(search_results, query_text)
    
    # Handle general search queries - comprehensive search across all tables
    if intent['intent_type'] == 'general_search':
        print(f"🔍 Performing comprehensive search for: '{query_text}'")
        search_results = comprehensive_crm_search(query_text)
        return generate_comprehensive_search_response(search_results, query_text)
    
    # Extract employee name from intent or query for other queries
    employee_name = intent.get('target') or extract_employee_name(query_text)
    print(f"🎯 Extracted Employee Name: '{employee_name}' from query: '{query_text}'")
    
    # Universal employee handling - no defaulting to Hamza
    if employee_name:
        print(f"📊 Looking for projects for: {employee_name}")
        projects = get_employee_projects(employee_name=employee_name)
        if not projects:
            # Try to find employee and provide helpful error
            employee = find_employee_by_name(employee_name)
            if employee:
                return {
                    'success': True,
                    'response': f"I found {employee['full_name']} in our system, but they don't seem to have any projects assigned yet. 📋\n\nWould you like me to:\n• Show the employee list instead? 👥\n• Check if there are any recent updates? 🔄",
                    'employee_data': employee
                }
            else:
                return {
                    'success': False,
                    'response': f"I couldn't find an employee named '{employee_name}' in our system. 🤔\n\nTry asking for:\n• 'Show me employee list' to see all staff\n• Use a different spelling of the name\n• Or ask about a specific project directly"
                }
        
        # We have projects for the employee, handle different intent types
        if intent['intent_type'] == 'projects_list':
            return generate_projects_list_response(projects, intent, employee_name)
        elif intent['intent_type'] == 'project_tasks':
            return generate_project_tasks_response(projects, intent, query_text, employee_name)
        elif intent['intent_type'] == 'task_detail':
            return generate_task_detail_response(projects, intent, query_text, employee_name)
        elif intent['intent_type'] == 'performance_analysis':
            return generate_performance_analysis_response(projects, intent, query_text, employee_name)
        else:
            # Fallback to basic analysis for general queries
            return generate_general_response(projects, query_text, intent, employee_name)
    else:
        # No employee name detected - try comprehensive search as final fallback
        print(f"🔍 No employee name detected, trying comprehensive search for: '{query_text}'")
        search_results = comprehensive_crm_search(query_text)
        
        if search_results['found_matches']:
            return generate_comprehensive_search_response(search_results, query_text)
        else:
            # Absolute fallback - provide helpful guidance
            return {
                'success': True,
                'response': f"I'd be happy to help! 😊 But I need to know who or what you're asking about.\n\n" +
                           "You can ask me:\n" +
                           "• **About employees**: 'Show me Nawaz projects' or 'How is Sarah doing?'\n" +
                           "• **About projects**: 'DDS Focus Pro tasks' or 'AI coordination project status'\n" +
                           "• **General queries**: 'Show employee list' or 'Show overdue projects'\n" +
                           "• **Search anything**: 'Find marketing tasks' or 'Show web development'\n\n" +
                           "What would you like to know about? 🤔"
            }

def extract_employee_name(query_text):
    """Extract employee name from natural language query with improved context awareness"""
    query_lower = query_text.lower()
    
    # Look for possessive patterns like "John's projects", "Sarah's performance", "Hamza Haseeb projects"
    import re
    
    # First try possessive patterns
    possessive_match = re.search(r"(\w+(?:\s+\w+)?)'s", query_text)
    if possessive_match:
        name = possessive_match.group(1).title()
        # Skip if it's clearly not a person's name
        if not any(word in name.lower() for word in ['project', 'task', 'company', 'team', 'system']):
            return name
    
    # Look for specific patterns that clearly indicate a person (including full names)
    person_patterns = [
        r"tell me about (\w+(?:\s+\w+)?)",
        r"how is (\w+(?:\s+\w+)?)",
        r"(\w+(?:\s+\w+)?)'s projects",
        r"(\w+(?:\s+\w+)?)'s performance", 
        r"(\w+(?:\s+\w+)?)'s progress",
        r"(\w+(?:\s+\w+)?)'s tasks",
        r"show me (\w+(?:\s+\w+)?)'s",
        r"get (\w+(?:\s+\w+)?)'s",
        r"(\w+(?:\s+\w+)?) projects",  # "Hamza projects" or "Hamza Haseeb projects"
        r"(\w+(?:\s+\w+)?) performance",
        r"(\w+(?:\s+\w+)?) doing"
    ]
    
    for pattern in person_patterns:
        match = re.search(pattern, query_lower)
        if match:
            name = match.group(1).strip()
            # Skip common words that aren't names
            if name not in ['the', 'me', 'my', 'his', 'her', 'their', 'about', 'all', 'show', 'get', 'tell']:
                return name.title()
    
    # Look for employee names directly in query (including common full names)
    # Extended list with full names
    known_employees = [
        'hamza', 'hamza haseeb', 'haseeb', 
        'nawaz', 'john', 'sarah', 'mike', 'david', 'lisa', 'alex', 
        'maria', 'james', 'emma', 'ahmed', 'ali', 'hassan', 'fatima', 'aisha'
    ]
    
    # Sort by length (longest first) to match full names before parts
    known_employees.sort(key=len, reverse=True)
    
    for name in known_employees:
        if name in query_lower:
            return name.title()
    
    return None

def analyze_hamza_query(query_text):
    """Analyze Hamza's query - backward compatibility wrapper"""
    return analyze_employee_query(query_text)

def generate_greeting_response(query_text):
    """Generate a warm, human-like greeting response"""
    from datetime import datetime
    import random
    
    current_hour = datetime.now().hour
    
    # Time-based greetings
    if current_hour < 12:
        time_greeting = "Good morning"
    elif current_hour < 17:
        time_greeting = "Good afternoon"
    else:
        time_greeting = "Good evening"
    
    # Friendly responses
    friendly_responses = [
        f"Hello there! 😊 {time_greeting}! I'm your AI coordination assistant, ready to help you manage projects and team performance.",
        f"Hi! 👋 {time_greeting}! Great to see you! I'm here to help you with project management, team insights, and performance analysis.",
        f"Hey! 🌟 {time_greeting}! I'm your friendly project coordination assistant. What can I help you with today?",
        f"Hello! ✨ {time_greeting}! I'm excited to help you today! I can assist with project tracking, performance analysis, and team coordination."
    ]
    
    response = random.choice(friendly_responses)
    response += "\n\n💼 **What I can help you with:**\n"
    response += "• 📋 **Project Lists** - \"Show me John's projects\"\n"
    response += "• � **Employee Lists** - \"Show me all employees\"\n"
    response += "• �📊 **Performance Analysis** - \"How is Sarah doing?\"\n"
    response += "• 📝 **Task Details** - \"Tell me about project tasks\"\n"
    response += "• ⚠️ **Overdue Alerts** - \"Show overdue projects\"\n"
    response += "• 🤖 **Smart Analysis** - I understand natural language!\n\n"
    response += "Just ask me anything about projects, tasks, employees, or team performance! 🚀"
    
    return {
        'success': True,
        'response': response,
        'greeting': True,
        'data_source': 'greeting_handler'
    }

def generate_employee_list_response(intent):
    """Generate a friendly employee list response"""
    employees = get_all_employees()
    
    if not employees:
        return {
            'success': False,
            'response': "Sorry, I can't access the employee database right now. Please try again later! 😅",
            'error': 'Unable to fetch employee data'
        }
    
    response = f"Here are all our amazing team members! 👥✨\n\n"
    response += f"**📊 Total Active Employees: {len(employees)}**\n\n"
    
    # Group employees by role if available
    roles = {}
    for employee in employees:
        role = employee.get('role', 'Staff Member')
        if role not in roles:
            roles[role] = []
        roles[role].append(employee)
    
    # Display employees by role
    for role, role_employees in roles.items():
        if len(role_employees) > 0:
            response += f"**{role} ({len(role_employees)}):**\n"
            for emp in role_employees:
                full_name = emp.get('full_name', 'Unknown')
                email = emp.get('email', 'No email')
                phone = emp.get('phonenumber', 'No phone')
                
                response += f"• **{full_name}** 👤\n"
                response += f"  📧 {email}\n"
                if phone and phone != 'No phone':
                    response += f"  📞 {phone}\n"
                response += "\n"
    
    response += f"💡 **Try asking about specific employees:**\n"
    response += f"• \"Show me {employees[0]['full_name']}'s projects\"\n"
    response += f"• \"How is {employees[1]['full_name'] if len(employees) > 1 else employees[0]['full_name']} doing?\"\n"
    response += f"• \"Tell me about [employee name]'s performance\"\n"
    
    return {
        'success': True,
        'response': response,
        'employees_data': employees,
        'data_source': 'employee_database'
    }

def generate_employee_projects_list_response(employee_name):
    """Generate a simple list of projects for a specific employee"""
    try:
        # First find the employee
        employee = find_employee_by_name(employee_name)
        if not employee:
            return {
                'success': False,
                'response': f"❌ I couldn't find an employee named '{employee_name}'. Please check the spelling or try a different name.",
                'error': 'Employee not found'
            }
        
        connection = get_database_connection()
        if not connection:
            return {
                'success': False,
                'response': "Sorry, I couldn't connect to the database to get the project list.",
                'error': 'Database connection failed'
            }
        
        cursor = connection.cursor(dictionary=True)
        
        # Get projects specifically for this employee
        query = """
        SELECT DISTINCT 
            p.id, 
            p.name, 
            p.status, 
            p.progress,
            p.start_date, 
            p.deadline,
            c.company as client_name
        FROM tblprojects p
        INNER JOIN tblproject_members pm ON p.id = pm.project_id
        LEFT JOIN tblclients c ON p.clientid = c.userid
        WHERE pm.staff_id = %s 
        ORDER BY p.name ASC
        """
        
        cursor.execute(query, (employee['staffid'],))
        projects = cursor.fetchall()
        
        if not projects:
            return {
                'success': True,
                'response': f"🔍 **{employee['firstname']} {employee['lastname']}** doesn't seem to be assigned to any projects currently.\n\n💡 They might be available for new assignments!",
                'projects_data': [],
                'employee_data': employee,
                'data_source': 'employee_projects_query'
            }
        
        # Create employee-specific project list
        full_name = f"{employee['firstname']} {employee['lastname']}"
        response = f"📋 **{full_name}'s Project List ({len(projects)} projects):**\n\n"
        
        active_projects = []
        completed_projects = []
        
        for project in projects:
            project_name = project.get('name', 'Unnamed Project')
            client_name = project.get('client_name', 'Internal')
            status = project.get('status', 'Unknown')
            progress = project.get('progress', 0)
            
            # Format dates
            start_date = project.get('start_date')
            if start_date:
                start_date = start_date.strftime('%Y-%m-%d') if hasattr(start_date, 'strftime') else str(start_date)
            
            deadline = project.get('deadline')
            if deadline:
                deadline = deadline.strftime('%Y-%m-%d') if hasattr(deadline, 'strftime') else str(deadline)
            
            if status and str(status).lower() in ['completed', '5']:
                completed_projects.append((project_name, client_name, progress, deadline))
            else:
                active_projects.append((project_name, client_name, progress, status, deadline))
        
        # Show active projects first
        if active_projects:
            response += f"🔄 **Active Projects ({len(active_projects)}):**\n"
            for i, (name, client, progress, status, deadline) in enumerate(active_projects, 1):
                progress_emoji = "🚀" if progress >= 80 else "💪" if progress >= 50 else "📝" if progress >= 20 else "🆕"
                response += f"{i:2d}. **{name}** {progress_emoji} ({progress}%)\n"
                response += f"     👤 Client: {client}\n"
                if deadline:
                    response += f"     ⏰ Deadline: {deadline}\n"
            response += "\n"
        
        # Show completed projects
        if completed_projects:
            response += f"✅ **Completed Projects ({len(completed_projects)}):**\n"
            for i, (name, client, progress, deadline) in enumerate(completed_projects, 1):
                response += f"{i:2d}. **{name}** 🎉\n"
                response += f"     👤 Client: {client}\n"
            response += "\n"
        
        response += f"📊 **Summary for {full_name}:** {len(active_projects)} active, {len(completed_projects)} completed\n\n"
        response += f"💡 **For project details:** Ask about a specific project by name!\n"
        response += f"💡 **For performance analysis:** Ask \"How is {employee['firstname']} performing?\""
        
        return {
            'success': True,
            'response': response,
            'projects_data': projects,
            'employee_data': employee,
            'active_count': len(active_projects),
            'completed_count': len(completed_projects),
            'data_source': 'employee_projects_list'
        }
        
    except Exception as e:
        print(f"Error generating employee projects list: {e}")
        return {
            'success': False,
            'response': f"Sorry, I encountered an error while getting {employee_name}'s project list. Please try again.",
            'error': str(e)
        }
    finally:
        if connection:
            connection.close()

def generate_simple_projects_list_response():
    """Generate a simple list of all project names when user just wants project names"""
    try:
        connection = get_database_connection()
        if not connection:
            return {
                'success': False,
                'response': "Sorry, I couldn't connect to the database to get the project list.",
                'error': 'Database connection failed'
            }
        
        cursor = connection.cursor(dictionary=True)
        
        # Get all projects with basic info
        query = """
        SELECT DISTINCT p.id, p.name, p.status, p.progress,
               c.company as client_name,
               p.start_date, p.deadline
        FROM tblprojects p
        LEFT JOIN tblclients c ON p.clientid = c.userid
        ORDER BY p.name ASC
        """
        
        cursor.execute(query)
        projects = cursor.fetchall()
        
        if not projects:
            return {
                'success': True,
                'response': "🔍 No projects found in the database. The project list appears to be empty.",
                'projects_data': [],
                'data_source': 'database_query'
            }
        
        # Create simple project names list
        response = f"📋 **Complete Project List ({len(projects)} projects):**\n\n"
        
        active_projects = []
        completed_projects = []
        
        for project in projects:
            project_name = project.get('name', 'Unnamed Project')
            client_name = project.get('client_name', 'Internal')
            status = project.get('status', 'Unknown')
            progress = project.get('progress', 0)
            
            if status and str(status).lower() in ['completed', '5']:
                completed_projects.append((project_name, client_name, progress))
            else:
                active_projects.append((project_name, client_name, progress, status))
        
        # Show active projects first
        if active_projects:
            response += f"🔄 **Active Projects ({len(active_projects)}):**\n"
            for i, (name, client, progress, status) in enumerate(active_projects, 1):
                progress_emoji = "🚀" if progress >= 80 else "💪" if progress >= 50 else "📝" if progress >= 20 else "🆕"
                response += f"{i:2d}. **{name}** {progress_emoji} ({progress}%)\n"
                response += f"     👤 Client: {client}\n"
            response += "\n"
        
        # Show completed projects
        if completed_projects:
            response += f"✅ **Completed Projects ({len(completed_projects)}):**\n"
            for i, (name, client, progress) in enumerate(completed_projects, 1):
                response += f"{i:2d}. **{name}** 🎉\n"
                response += f"     👤 Client: {client}\n"
            response += "\n"
        
        response += f"📊 **Summary:** {len(active_projects)} active, {len(completed_projects)} completed\n\n"
        response += f"💡 **For detailed info:** Ask about a specific project by name!\n"
        response += f"💡 **For employee projects:** Ask \"Show [employee name]'s projects\""
        
        return {
            'success': True,
            'response': response,
            'projects_data': projects,
            'active_count': len(active_projects),
            'completed_count': len(completed_projects),
            'data_source': 'simple_projects_list'
        }
        
    except Exception as e:
        print(f"Error generating simple projects list: {e}")
        return {
            'success': False,
            'response': "Sorry, I encountered an error while getting the project list. Please try again.",
            'error': str(e)
        }
    finally:
        if connection:
            connection.close()

def generate_projects_list_response(projects, intent, employee_name="Employee"):
    """Generate a clean projects list response"""
    active_projects = [p for p in projects if p.get('status') != 'Completed']
    completed_projects = [p for p in projects if p.get('status') == 'Completed']
    
    response = f"Here are all of {employee_name}'s projects! 📋✨\n\n"
    
    if active_projects:
        response += f"🔄 **Currently Working On ({len(active_projects)} projects):**\n"
        for i, project in enumerate(active_projects, 1):
            progress = project.get('progress', 0)
            if progress >= 80:
                status_emoji = "🚀"
                status_text = "Almost done!"
            elif progress >= 50:
                status_emoji = "💪"
                status_text = "Making good progress"
            elif progress >= 20:
                status_emoji = "📝"
                status_text = "Getting started"
            else:
                status_emoji = "🆕"
                status_text = "Just beginning"
                
            response += f"{i}. **{project.get('project_name', 'Unknown Project')}** {status_emoji}\n"
            response += f"   📊 {progress}% complete - {status_text}\n"
            response += f"   👤 Client: {project.get('client_name', 'Internal Project')}\n\n"
    
    if completed_projects:
        response += f"✅ **Already Finished ({len(completed_projects)} projects):**\n"
        for i, project in enumerate(completed_projects, 1):
            response += f"{i}. **{project.get('project_name', 'Unknown Project')}** 🎉\n"
            response += f"   � Client: {project.get('client_name', 'Internal Project')}\n\n"
    
    if not active_projects and not completed_projects:
        response += "Hmm, looks like there aren't any projects showing up right now. Maybe check the database connection? 🤔"
    
    return {
        'success': True,
        'response': response,
        'projects_data': projects,
        'data_source': 'real_database'
    }

def generate_project_tasks_response(projects, intent, query_text, employee_name="Employee"):
    """Generate project tasks response based on intent"""
    # Find the target project with improved matching
    target_project = None
    
    # First try to get from intent
    if intent.get('target'):
        target_lower = intent['target'].lower()
        # Fix: use 'name' field instead of 'project_name'
        target_project = next((p for p in projects if p.get('name') and target_lower in p['name'].lower()), None)
    
    # If not found, try to extract project name from the query
    if not target_project:
        query_lower = query_text.lower()
        print(f"🔍 Searching for project in query: '{query_text}'")
        print(f"📋 Available projects: {[p.get('name', 'Unknown') for p in projects[:5]]}")  # Show first 5
        
        # Try to find project name in the query text
        for project in projects:
            project_name = project.get('name', '').lower()
            
            # Check for exact matches or partial matches
            if project_name in query_lower or any(word in project_name for word in query_lower.split() if len(word) > 2):
                # Special matching for common abbreviations and variations
                if 'dds focus pro' in query_lower and 'dds focus pro' in project_name:
                    target_project = project
                    print(f"✅ Found DDS Focus Pro match: {project.get('name')}")
                    break
                elif 'ai coordination' in query_lower and 'ai coordination' in project_name:
                    target_project = project
                    print(f"✅ Found AI Coordination match: {project.get('name')}")
                    break
                elif len([word for word in query_lower.split() if word in project_name]) >= 2:
                    target_project = project
                    print(f"✅ Found partial match: {project.get('name')}")
                    break
    
    # If no specific project found but user asked for tasks, show tasks from multiple projects
    if not target_project and 'task' in query_text.lower():
        print("💡 No specific project found, showing general task overview")
        return generate_general_task_overview(projects, query_text)
    
    if not target_project:
        return {
            'success': False,
            'response': f'Sorry, I could not find a project matching "{query_text}" in the database. 🤔\n\nTry asking:\n• "Show me project list" to see all projects\n• Use a specific project name for task lists',
            'data_source': 'real_database'
        }
    
    tasks = get_project_tasks_from_db(target_project['id'])
    
    if intent.get('wants_list', True):
        # Simple task list format
        response = f"📋 **{target_project.get('name', 'Project')} - Task List**\n\n"
        
        if tasks:
            for i, task in enumerate(tasks, 1):
                status_emoji = "✅" if task['status'] == 'Completed' else "🔄" if task['status'] == 'In Progress' else "⭕"
                response += f"{i}. {status_emoji} **{task['name']}**\n"
        else:
            response += "✨ No tasks found for this project."
    else:
        # Detailed task view
        response = f"📋 **{target_project.get('name', 'Project')} - Detailed Tasks**\n\n"
        response += f"🏢 **Client**: {target_project.get('client_name', 'N/A')}\n"
        response += f"📊 **Project Progress**: {target_project.get('progress', 0)}%\n\n"
        
        if tasks:
            for i, task in enumerate(tasks, 1):
                response += f"{i}. **{task['name']}**\n"
                response += f"   📊 Status: {task.get('status', 'Unknown')} | Priority: {task.get('priority', 'Normal')}\n"
                if task.get('due_date'):
                    response += f"   📅 Due: {task['due_date']}\n"
                response += "\n"
        else:
            response += "✨ No tasks found for this project."
    
    return {
        'success': True,
        'response': response,
        'project_data': target_project,
        'tasks_data': tasks,
        'data_source': 'real_database'
    }

def generate_general_task_overview(projects, query_text):
    """Generate a general task overview when no specific project is found"""
    print("📋 Generating general task overview from available projects")
    
    all_tasks = []
    projects_with_tasks = 0
    
    # Collect tasks from the first few projects
    for project in projects[:10]:  # Check first 10 projects
        tasks = get_project_tasks_from_db(project['id'])
        if tasks:
            projects_with_tasks += 1
            for task in tasks[:3]:  # Max 3 tasks per project
                task['project_name'] = project.get('name', 'Unknown Project')
                all_tasks.append(task)
    
    if not all_tasks:
        return {
            'success': False,
            'response': '📋 No active tasks found in the current projects. All work might be completed! 🎉',
            'data_source': 'real_database'
        }
    
    # Sort by priority and status
    priority_order = {'Urgent': 4, 'High': 3, 'Normal': 2, 'Low': 1}
    all_tasks.sort(key=lambda t: priority_order.get(t.get('priority', 'Normal'), 2), reverse=True)
    
    response = f"📋 **Task Overview** (from {projects_with_tasks} active projects)\n\n"
    
    # Group by status
    active_tasks = [t for t in all_tasks if t.get('status') in ['In Progress', 'Not Started']]
    completed_tasks = [t for t in all_tasks if t.get('status') == 'Completed']
    
    if active_tasks:
        response += "🔄 **Active Tasks:**\n"
        for i, task in enumerate(active_tasks[:10], 1):  # Show max 10 active tasks
            priority_emoji = "🔴" if task.get('priority') == 'High' else "🟡" if task.get('priority') == 'Medium' else "🟢"
            response += f"{i}. {priority_emoji} **{task['name']}**\n"
            response += f"   📊 Project: {task.get('project_name', 'Unknown')}\n"
            if task.get('due_date'):
                response += f"   📅 Due: {task['due_date']}\n"
            response += "\n"
    
    if completed_tasks and len(completed_tasks) > 0:
        response += f"\n✅ **Recently Completed:** {len(completed_tasks)} tasks\n"
        for task in completed_tasks[:3]:  # Show 3 recent completions
            response += f"• {task['name']} (from {task.get('project_name', 'Unknown')})\n"
    
    response += f"\n💡 **Tip:** Ask for a specific project name to see all its tasks!"
    
    return {
        'success': True,
        'response': response,
        'tasks_data': all_tasks,
        'data_source': 'real_database'
    }

def generate_task_detail_response(projects, intent, query_text, employee_name="Employee"):
    """Generate detailed response for a specific task"""
    target_task = None
    task_name = intent.get('target', '')
    
    # Search for the task across all projects
    for project in projects:
        tasks = get_project_tasks_from_db(project['id'])
        for task in tasks:
            if task_name.lower() in task['name'].lower():
                target_task = task
                task_project = project
                break
        if target_task:
            break
    
    if not target_task:
        return {
            'success': False,
            'response': f'Sorry, I could not find a task matching "{task_name}" in Hamza\'s projects.',
            'data_source': 'real_database'
        }
    
    response = f"📋 **Task Details: {target_task['name']}**\n\n"
    response += f"🏢 **Project**: {task_project.get('project_name', 'Unknown')}\n"
    response += f"📝 **Description**: {target_task.get('description', 'No description available')}\n"
    response += f"📊 **Status**: {target_task.get('status', 'Unknown')}\n"
    response += f"⚡ **Priority**: {target_task.get('priority', 'Normal')}\n"
    response += f"📈 **Progress**: {target_task.get('progress', 0)}%\n"
    
    if target_task.get('start_date'):
        response += f"📅 **Start Date**: {target_task['start_date']}\n"
    if target_task.get('due_date'):
        response += f"⏰ **Due Date**: {target_task['due_date']}\n"
    if target_task.get('completed_date'):
        response += f"✅ **Completed**: {target_task['completed_date']}\n"
    
    if target_task.get('billable'):
        response += f"💰 **Billable**: Yes\n"
    if target_task.get('milestone'):
        response += f"🎯 **Milestone**: Yes\n"
    
    return {
        'success': True,
        'response': response,
        'task_data': target_task,
        'project_data': task_project,
        'data_source': 'real_database'
    }

def add_overdue_warning_comments():
    """Add warning comments to overdue projects automatically"""
    from datetime import datetime, date
    
    try:
        # Get database connection
        connection = get_database_connection()
        if not connection:
            return {'success': False, 'error': 'Database connection failed'}
        
        # Get overdue projects
        cursor = connection.cursor(dictionary=True)
        
        # Find overdue projects
        query = """
        SELECT p.id, p.name, p.deadline, p.status 
        FROM tblprojects p
        WHERE p.deadline < CURDATE() 
        AND p.status != 'Finished'
        AND p.status != 'Cancelled'
        """
        
        cursor.execute(query)
        overdue_projects = cursor.fetchall()
        
        warning_count = 0
        
        for project in overdue_projects:
            project_id = project['id']
            project_name = project['name']
            deadline = project['deadline']
            
            # Calculate days overdue
            if isinstance(deadline, date):
                days_overdue = (date.today() - deadline).days
            else:
                continue
                
            # Check if we already have a recent warning comment for this project
            check_query = """
            SELECT COUNT(*) as count FROM tblproject_notes 
            WHERE project_id = %s 
            AND description LIKE '%OVERDUE WARNING%'
            AND dateadded >= DATE_SUB(NOW(), INTERVAL 7 DAY)
            """
            
            cursor.execute(check_query, (project_id,))
            recent_warnings = cursor.fetchone()
            
            # Only add warning if no recent warning exists
            if recent_warnings['count'] == 0:
                warning_message = f"⚠️ OVERDUE WARNING: This project '{project_name}' is {days_overdue} days overdue (deadline was {deadline}). Immediate attention required!"
                
                # Add warning comment to tblproject_notes
                insert_query = """
                INSERT INTO tblproject_notes (project_id, description, staff_id, dateadded)
                VALUES (%s, %s, 1, NOW())
                """
                
                cursor.execute(insert_query, (project_id, warning_message))
                connection.commit()
                warning_count += 1
                
        cursor.close()
        connection.close()
        
        return {
            'success': True,
            'warnings_added': warning_count,
            'overdue_projects': len(overdue_projects)
        }
        
    except Exception as e:
        print(f"Error adding warning comments: {e}")
        return {
            'success': False,
            'error': str(e)
        }

def generate_performance_analysis_response(projects, intent, query_text, employee_name="Employee"):
    """Generate intelligent performance analysis for Hamza's work"""
    from datetime import datetime
    
    # Automatically add warning comments to overdue projects
    warning_result = add_overdue_warning_comments()
    
    performance = analyze_employee_performance(projects, employee_name)
    
    # More human-like, conversational response
    response = f"Hey! Let me give you the scoop on {employee_name}'s performance! 😊\n\n"
    
    # Add warning comment status if any were added
    if warning_result['success'] and warning_result['warnings_added'] > 0:
        response += f"🚨 **Just Added**: I've automatically flagged {warning_result['warnings_added']} overdue projects with warning comments!\n\n"
    
    # Work ethic assessment - more conversational
    if performance['performance_score'] >= 80:
        response += f"� **Work Ethic**: Hamza is doing fantastic! Really impressed with his dedication.\n"
        response += f"📈 **Performance Score**: {performance['performance_score']}/100 - Excellent work! 🎉\n\n"
    elif performance['performance_score'] >= 60:
        response += f"👍 **Work Ethic**: Hamza is doing pretty well, but there's room for improvement.\n"
        response += f"📈 **Performance Score**: {performance['performance_score']}/100 - Good, but can be better! 💪\n\n"
    else:
        response += f"� **Work Ethic**: {performance['work_ethic']}\n"
        response += f"�📈 **Performance Score**: {performance['performance_score']}/100 - Let's work together to improve this! 🤝\n\n"
    
    # Project statistics - more conversational
    response += f"� **Here's what I found:**\n"
    response += f"• **Total Projects**: {performance['total_projects']} (quite a workload!)\n"
    response += f"• **Completed**: {performance['completed_projects']} ✅\n"
    response += f"• **Still Active**: {performance['active_projects']} 🔄\n"
    if performance['overdue_projects'] > 0:
        response += f"• **⚠️ Overdue**: {performance['overdue_projects']} (needs attention!)\n"
    response += "\n"
    
    # Performance details with personality
    if performance['completed_projects'] > 0:
        response += f"⏰ **Delivery Track Record:**\n"
        if performance['early_projects'] > 0:
            response += f"• **🚀 Early Bird**: {performance['early_projects']} projects finished ahead of schedule! Impressive! 👏\n"
        if performance['on_time_projects'] > 0:
            response += f"• **✅ Right on Time**: {performance['on_time_projects']} projects - punctuality is great! ⌚\n"
        if performance['late_projects'] > 0:
            response += f"• **⏰ Running Late**: {performance['late_projects']} projects - let's work on this! 📅\n"
        response += "\n"
    
    # Insights and recommendations - more personal
    response += f"💡 **My Take:**\n"
    for insight in performance['insights']:
        response += f"• {insight}\n"
    
    # More encouraging and supportive conclusions
    if performance['performance_score'] >= 80:
        response += f"\n🎉 **Bottom Line**: {employee_name} is absolutely crushing it! Keep up the amazing work! They're definitely a star performer on the team. ⭐"
    elif performance['performance_score'] >= 60:
        response += f"\n👍 **Bottom Line**: {employee_name} is doing solid work! With a bit more focus on deadlines, they'll be unstoppable! I believe in them! 💪"
    else:
        response += f"\n🤗 **Bottom Line**: Hey, everyone has rough patches! {employee_name} just needs some support and maybe better time management tools. We've got their back! Let's help them succeed! 🚀"
    
    # Specific query handling
    query_lower = query_text.lower()
    if 'overdue' in query_lower or 'late' in query_lower:
        overdue_projects = [p for p in projects if p.get('status') != 'Completed' and p.get('deadline')]
        if overdue_projects:
            response += f"\n\n🚨 **Overdue Projects Details:**\n"
            for project in overdue_projects:
                try:
                    deadline = datetime.strptime(project['deadline'], '%Y-%m-%d').date()
                    if datetime.now().date() > deadline:
                        days_overdue = (datetime.now().date() - deadline).days
                        response += f"- **{project.get('project_name', 'Unknown')}**: {days_overdue} days overdue\n"
                except:
                    response += f"- **{project.get('project_name', 'Unknown')}**: Deadline passed\n"
    
    return {
        'success': True,
        'response': response,
        'performance_data': performance,
        'projects_data': projects,
        'data_source': 'real_database'
    }

def generate_general_response(projects, query_text, intent, employee_name="Employee"):
    """Generate friendly, conversational response for unclear queries"""
    # Default to project overview
    active_projects = [p for p in projects if p.get('status') != 'Completed']
    completed_projects = [p for p in projects if p.get('status') == 'Completed']
    
    response = f"Hey! I'm not quite sure what you're looking for, but let me share what I know! 😊\n\n"
    response += f"📊 **Here's {employee_name}'s current situation:**\n"
    response += f"• **Active Projects**: {len(active_projects)} (keeping busy!)\n"
    response += f"• **Completed Projects**: {len(completed_projects)} (nice work!)\n"
    response += f"• **Total Projects**: {len(projects)} (that's a lot!)\n\n"
    
    response += f"� **Try asking me things like:**\n"
    response += f"• \"Show me {employee_name}'s projects\" - I'll list them all!\n"
    response += f"• \"How is {employee_name} doing?\" - I'll analyze their performance\n"
    response += f"• \"What tasks are in the AI project?\" - I'll break it down\n"
    response += f"• \"Show overdue projects\" - I'll find any late ones\n\n"
    
    response += f"I'm here to help with project management, team insights, and performance tracking! Just ask me naturally - I understand human language! 🤖✨"
    
    return {
        'success': True,
        'response': response,
        'projects_data': projects,
        'data_source': 'real_database'
    }

# OLD CODE TO BE REMOVED - keeping for now to avoid breaking changes
    
    # Check for specific task detail queries first
    if any(word in query_lower for word in ['task', 'phase']) and any(word in query_lower for word in ['detail', 'details', 'information', 'info']):
        # Extract task name from query
        task_keywords = ['phase 1.1', 'phase 1.2', 'phase 1.3', 'create front-end', 'database integration', 'structure', 'environment']
        
        found_task = None
        for keyword in task_keywords:
            if keyword in query_lower:
                found_task = get_task_by_name(keyword)
                break
        
        if found_task:
            # Get project info
            project = next((p for p in projects if p.get('id') == found_task.get('project_id')), None)
            
            response = f"📋 **Task Details: {found_task['name']}**\n\n"
            if project:
                response += f"🏢 **Project**: {project.get('project_name', 'Unknown')}\n"
            response += f"📝 **Description**: {found_task.get('description', 'No description available')}\n"
            response += f"📊 **Status**: {found_task.get('status', 'Unknown')}\n"
            response += f"⚡ **Priority**: {found_task.get('priority', 'Normal')}\n"
            response += f"📈 **Progress**: {found_task.get('progress', 0)}%\n"
            
            if found_task.get('start_date'):
                response += f"📅 **Start Date**: {found_task['start_date']}\n"
            if found_task.get('due_date'):
                response += f"⏰ **Due Date**: {found_task['due_date']}\n"
            if found_task.get('completed_date'):
                response += f"✅ **Completed**: {found_task['completed_date']}\n"
            
            if found_task.get('billable'):
                response += f"💰 **Billable**: Yes\n"
            if found_task.get('milestone'):
                response += f"🎯 **Milestone**: Yes\n"
                
            return {
                'success': True,
                'response': response,
                'task_data': found_task,
                'data_source': 'real_database'
            }
    
    # Smart project detection - much more intelligent
    def detect_project_from_query(query_lower, projects):
        """Intelligently detect which project the user is asking about"""
        
        # AI/Coordination project patterns
        ai_patterns = [
            'ai coordination', 'ai project', 'coordination agent', 'ai agent',
            'ai coordination agent', 'coordination project', 'agent project',
            'this project', 'current project', 'main project'
        ]
        
        # Check for AI project
        for pattern in ai_patterns:
            if pattern in query_lower:
                ai_project = next((p for p in projects if p.get('project_name') and 'ai coordination' in p['project_name'].lower()), None)
                if ai_project:
                    return ai_project
        
        # Tourism/Health project patterns  
        tourism_patterns = ['tourism', 'health', 'medical', 'healthcare']
        for pattern in tourism_patterns:
            if pattern in query_lower:
                tourism_project = next((p for p in projects if p.get('project_name') and 'tourism' in p['project_name'].lower()), None)
                if tourism_project:
                    return tourism_project
        
        # If query mentions tasks but no specific project, assume AI project (most common)
        task_indicators = ['task', 'tasks', 'phase', 'phases', 'work', 'todo', 'assignment']
        if any(indicator in query_lower for indicator in task_indicators):
            ai_project = next((p for p in projects if p.get('project_name') and 'ai coordination' in p['project_name'].lower()), None)
            if ai_project:
                return ai_project
                
        return None
    
    # Smart query intent detection
    def detect_query_intent(query_lower):
        """Detect what the user wants to know"""
        
        # Task-related intents
        task_indicators = ['task', 'tasks', 'phase', 'phases', 'work', 'todo', 'assignment', 'activities']
        project_indicators = ['project', 'projects']
        
        # Detail vs List intent
        detail_keywords = ['detail', 'details', 'information', 'info', 'describe', 'explain', 'about']
        list_keywords = ['list', 'show', 'display', 'all', 'give me', 'tell me']
        
        is_task_query = any(indicator in query_lower for indicator in task_indicators)
        is_project_query = any(indicator in query_lower for indicator in project_indicators)
        wants_details = any(keyword in query_lower for keyword in detail_keywords)
        wants_list = any(keyword in query_lower for keyword in list_keywords)
        
        return {
            'is_task_query': is_task_query,
            'is_project_query': is_project_query,
            'wants_details': wants_details,
            'wants_list': wants_list,
            'is_asking_for_tasks': is_task_query or (is_project_query and wants_list)
        }
    
    # Apply intelligent detection
    specific_project = detect_project_from_query(query_lower, projects)
    intent = detect_query_intent(query_lower)
    
    # Handle task queries with intelligent project detection
    if intent['is_asking_for_tasks'] and specific_project:
        tasks = get_project_tasks_from_db(specific_project['id'])
        
        # Filter tasks by status if specified
        if 'overdue' in query_lower:
            # Filter overdue tasks
            today = datetime.now().date()
            overdue_tasks = []
            for task in tasks:
                if task['due_date'] and task['status'] != 'Completed':
                    try:
                        due_date = datetime.strptime(task['due_date'], '%Y-%m-%d').date()
                        if due_date < today:
                            overdue_tasks.append(task)
                    except:
                        pass
            tasks = overdue_tasks
            status_filter = 'Overdue'
        elif 'progress' in query_lower or 'current' in query_lower:
            tasks = [t for t in tasks if t['status'] in ['In Progress', 'Active']]
            status_filter = 'In Progress'
        elif 'finished' in query_lower or 'completed' in query_lower:
            tasks = [t for t in tasks if t['status'] == 'Completed']
            status_filter = 'Completed'
        else:
            status_filter = 'All'
        
        # Determine response format based on query intent
        show_details = any(word in query_lower for word in ['detail', 'details', 'information', 'info', 'full', 'complete', 'describe'])
        show_list = any(word in query_lower for word in ['list', 'show', 'tasks', 'all']) and not show_details
        
        # Generate smart response based on query intent
        if show_details and len(tasks) == 1:
            # Single task details
            task = tasks[0]
            response = f"📋 **Task Details: {task['name']}**\n\n"
            response += f"🏢 **Project**: {specific_project.get('project_name', 'Unknown')}\n"
            response += f"📝 **Description**: {task.get('description', 'No description available')}\n"
            response += f"📊 **Status**: {task.get('status', 'Unknown')}\n"
            response += f"⚡ **Priority**: {task.get('priority', 'Normal')}\n"
            response += f"� **Progress**: {task.get('progress', 0)}%\n"
            
            if task.get('start_date'):
                response += f"📅 **Start Date**: {task['start_date']}\n"
            if task.get('due_date'):
                response += f"⏰ **Due Date**: {task['due_date']}\n"
            if task.get('completed_date'):
                response += f"✅ **Completed**: {task['completed_date']}\n"
            
            if task.get('billable'):
                response += f"� **Billable**: Yes\n"
            if task.get('milestone'):
                response += f"🎯 **Milestone**: Yes\n"
                
        elif show_list or 'list' in query_lower:
            # Simple task list format
            response = f"📋 **{specific_project.get('project_name', 'Unknown Project')} - Task List**\n\n"
            
            if tasks:
                for i, task in enumerate(tasks, 1):
                    status_emoji = "✅" if task['status'] == 'Completed' else "🔄" if task['status'] == 'In Progress' else "⭕"
                    response += f"{i}. {status_emoji} **{task['name']}**\n"
            else:
                response += f"✨ No {status_filter.lower()} tasks found for this project."
                
        else:
            # Default detailed view for task queries
            response = f"📋 **{specific_project.get('project_name', 'Unknown Project')} - {status_filter} Tasks**\n\n"
            response += f"🏢 **Client**: {specific_project.get('client_name', 'N/A')}\n"
            response += f"📊 **Project Progress**: {specific_project.get('progress', 0)}%\n"
            response += f"📅 **Project Status**: {specific_project.get('status', 'Unknown')}\n\n"
            
            if tasks:
                response += f"📝 **Tasks Found**: {len(tasks)}\n\n"
                for i, task in enumerate(tasks, 1):
                    response += f"{i}. **{task['name']}**\n"
                    response += f"   📝 {task.get('description', 'No description')}\n"
                    response += f"   📊 Status: {task.get('status', 'Unknown')} | Progress: {task.get('progress', 0)}%\n"
                    response += f"   ⚡ Priority: {task.get('priority', 'Normal')}\n"
                    
                    if task.get('due_date'):
                        response += f"   📅 Due: {task['due_date']}\n"
                    if task.get('completed_date'):
                        response += f"   ✅ Completed: {task['completed_date']}\n"
                    response += "\n"
            else:
                response += f"✨ No {status_filter.lower()} tasks found for this project."
        
        return {
            'success': True,
            'response': response,
            'project_data': specific_project,
            'tasks_data': tasks,
            'data_source': 'real_database'
        }
    
    # Fallback: If no specific project detected but user is clearly asking for tasks/projects
    if intent['is_asking_for_tasks'] or intent['is_task_query']:
        # Default to AI Coordination project (most common query)
        ai_project = next((p for p in projects if p.get('project_name') and 'ai coordination' in p['project_name'].lower()), None)
        
        if ai_project:
            tasks = get_project_tasks_from_db(ai_project['id'])
            
            # Simple task list format for fallback queries
            response = f"📋 **{ai_project.get('project_name', 'AI Coordination Agent')} - Task List**\n\n"
            
            if tasks:
                for i, task in enumerate(tasks, 1):
                    status_emoji = "✅" if task['status'] == 'Completed' else "🔄" if task['status'] == 'In Progress' else "⭕"
                    response += f"{i}. {status_emoji} **{task['name']}**\n"
            else:
                response += "✨ No tasks found for this project."
                
            return {
                'success': True,
                'response': response,
                'project_data': ai_project,
                'tasks_data': tasks,
                'data_source': 'real_database'
            }
    
    # General project overview
    active_projects = [p for p in projects if p.get('status') != 'Completed']
    completed_projects = [p for p in projects if p.get('status') == 'Completed']
    
    response = f"🎯 **Hamza's Real Project Portfolio**\n\n"
    response += f"📊 **Project Status Overview:**\n"
    response += f"- **Active/In Progress**: {len(active_projects)} projects\n"
    response += f"- **Completed**: {len(completed_projects)} projects\n"
    response += f"- **Total Assigned**: {len(projects)} projects\n\n"
    
    response += f"📋 **Recent Projects:**\n"
    for i, project in enumerate(projects[:10], 1):
        status_emoji = "✅" if project.get('status') == 'Completed' else "🔄"
        response += f"{i}. **{project.get('project_name', 'Unknown Project')}** {status_emoji}\n"
        response += f"   📊 Progress: {project.get('progress', 0)}% | Client: {project.get('client_name', 'N/A')}\n"
        if project.get('deadline'):
            response += f"   📅 Deadline: {project['deadline']}\n"
        response += "\n"
    
    if len(projects) > 10:
        response += f"... and {len(projects) - 10} more projects\n\n"
    
    response += "🔍 **Try These Specific Queries:**\n"
    response += "- \"Hamza AI project tasks list\"\n"
    response += "- \"Show me Hamza overdue tasks\"\n"
    response += "- \"Hamza in progress tasks\"\n"
    response += "- \"Hamza finished tasks details\"\n\n"
    
    response += "📊 **Data Source**: Real CRM Database ✅"
    
    return {
        'success': True,
        'response': response,
        'hamza_projects_data': {
            'total': len(projects),
            'active': len(active_projects),
            'completed': len(completed_projects),
            'projects': projects
        },
        'data_source': 'real_database'
    }

@app.route('/ai/analyze', methods=['POST', 'OPTIONS'])
def analyze_query():
    """AI analyze endpoint for ChatGPT frontend"""
    if request.method == 'OPTIONS':
        # Handle CORS preflight request
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response
    
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
        
        query = data['query'].strip()
        session_id = data.get('session_id', 'default')  # Get session ID from request
        print(f"🎯 ChatGPT Analyze Query: {query} [Session: {session_id}]")
        
        # Use OpenAI to analyze the query with conversation context
        try:
            result = analyze_employee_query(query, session_id)
            
            # Save conversation to history
            add_to_history(session_id, "user", query)
            add_to_history(session_id, "assistant", result['response'])
            
            response_data = {
                'success': result['success'],
                'response': result['response'],
                'employee_data': result.get('projects_data', {}),
                'project_data': result.get('project_data'),
                'task_data': result.get('task_data'),
                'data': result.get('tasks_data'),
                'data_source': result.get('data_source', 'real_database'),
                'timestamp': datetime.now().isoformat(),
                'session_id': session_id  # Return session ID to frontend
            }
            
            # Add CORS headers
            response = make_response(jsonify(response_data))
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response
            
        except Exception as e:
            print(f"❌ Query analysis error: {e}")
            error_response = {
                'success': False,
                'response': f"Sorry, I encountered an error processing your query: {str(e)}",
                'error': str(e)
            }
            
            response = make_response(jsonify(error_response), 500)
            response.headers.add("Access-Control-Allow-Origin", "*")
            return response
            
    except Exception as e:
        print(f"❌ Analyze endpoint error: {str(e)}")
        error_response = {
            'success': False,
            'error': str(e),
            'response': 'Sorry, I encountered a server error. Please try again.'
        }
        response = make_response(jsonify(error_response), 500)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

@app.route('/ai/enhanced_query', methods=['POST', 'OPTIONS'])
def enhanced_query():
    """
    Enhanced AI query endpoint that:
    1. Sends prompts to OpenAI for analysis
    2. Generates SQL queries based on analysis
    3. Stores prompts for future use
    4. Searches database and returns formatted results
    """
    try:
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers.add("Access-Control-Allow-Origin", "*")
            response.headers.add("Access-Control-Allow-Headers", "Content-Type")
            response.headers.add("Access-Control-Allow-Methods", "POST, OPTIONS")
            return response
            
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({'error': 'Query is required'}), 400
            
        user_prompt = data['query'].strip()
        session_id = data.get('session', 'default_session')
        
        print(f"🚀 Enhanced Query Processing: {user_prompt} [Session: {session_id}]")
        
        # Step 1: Analyze intent using existing logic
        session = get_or_create_session(session_id)
        context = session.get('context', {})
        
        enhanced_query = enhance_query_with_context(user_prompt, context)
        print(f"📝 Enhanced Query: '{enhanced_query}'")
        
        # Get intent analysis
        intent_analysis = analyze_with_openai_and_fallback(enhanced_query, context)
        print(f"🤖 Intent Analysis: {intent_analysis}")
        
        # Step 2: Use enhanced AI service for complete processing
        enhanced_result = enhanced_ai_service.process_user_prompt(
            session_id, user_prompt, intent_analysis
        )
        
        print(f"✅ Enhanced Result: {enhanced_result.get('success', False)}")
        
        if not enhanced_result.get('success', False):
            error_msg = enhanced_result.get('results', 'Query execution failed')
            return jsonify({
                'success': False,
                'error': error_msg,
                'prompt_id': enhanced_result.get('prompt_id'),
                'sql_query': enhanced_result.get('sql_query'),
                'processing_time_ms': enhanced_result.get('processing_time_ms', 0)
            })
        
        # Step 3: Format and return results
        results = enhanced_result.get('results', [])
        query_metadata = enhanced_result.get('query_metadata', {})
        
        # Generate user-friendly response
        if isinstance(results, list) and len(results) > 0:
            response_text = format_enhanced_results(results, intent_analysis, query_metadata)
        else:
            response_text = "No results found for your query. Try rephrasing your question or being more specific."
        
        # Update conversation context
        update_conversation_context(context, intent_analysis, results)
        
        response_data = {
            'success': True,
            'response': response_text,
            'prompt_id': enhanced_result.get('prompt_id'),
            'sql_query': enhanced_result.get('sql_query'),
            'query_metadata': query_metadata,
            'result_count': len(results) if isinstance(results, list) else 0,
            'processing_time_ms': enhanced_result.get('processing_time_ms', 0),
            'intent_type': intent_analysis.get('intent_type'),
            'confidence': intent_analysis.get('confidence', 0.0)
        }
        
        response = make_response(jsonify(response_data))
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
        
    except Exception as e:
        print(f"❌ Enhanced Query Error: {str(e)}")
        error_response = {
            'success': False,
            'error': str(e),
            'response': 'Sorry, I encountered an error processing your enhanced query. Please try again.'
        }
        response = make_response(jsonify(error_response), 500)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

def format_enhanced_results(results, intent_analysis, metadata):
    """Format query results into user-friendly response"""
    intent_type = intent_analysis.get('intent_type', 'general')
    result_count = len(results)
    
    if intent_type == 'employee_list':
        response = f"📋 Found {result_count} employees:\n\n"
        for emp in results[:10]:  # Show first 10
            response += f"• **{emp.get('name', 'Unknown')}** - {emp.get('position', 'N/A')} ({emp.get('department', 'N/A')})\n"
            if emp.get('email'):
                response += f"  📧 {emp['email']}\n"
        if result_count > 10:
            response += f"\n... and {result_count - 10} more employees"
            
    elif intent_type == 'employee_projects_list':
        target = intent_analysis.get('target', 'employee')
        response = f"📊 Found {result_count} projects for {target}:\n\n"
        for proj in results[:10]:
            status_emoji = "✅" if proj.get('status') == 'completed' else "🔄" if proj.get('status') == 'active' else "⏸️"
            response += f"{status_emoji} **{proj.get('name', 'Unnamed Project')}**\n"
            if proj.get('description'):
                response += f"   {proj['description'][:100]}{'...' if len(proj.get('description', '')) > 100 else ''}\n"
            if proj.get('role'):
                response += f"   Role: {proj['role']}\n"
        if result_count > 10:
            response += f"\n... and {result_count - 10} more projects"
            
    elif intent_type == 'project_tasks':
        target = intent_analysis.get('target', 'project')
        response = f"📝 Found {result_count} tasks for {target}:\n\n"
        for task in results[:10]:
            priority_emoji = "🔴" if task.get('priority') == 'high' else "🟡" if task.get('priority') == 'medium' else "🟢"
            status_emoji = "✅" if task.get('status') == 'completed' else "🔄" if task.get('status') == 'in_progress' else "📋"
            response += f"{priority_emoji} {status_emoji} **{task.get('title', 'Untitled Task')}**\n"
            if task.get('assigned_to_name'):
                response += f"   👤 Assigned to: {task['assigned_to_name']}\n"
            if task.get('due_date'):
                response += f"   📅 Due: {task['due_date']}\n"
        if result_count > 10:
            response += f"\n... and {result_count - 10} more tasks"
            
    else:
        # General results formatting
        response = f"🔍 Found {result_count} results:\n\n"
        for item in results[:10]:
            if 'type' in item:
                type_emoji = "👤" if item['type'] == 'employee' else "📊" if item['type'] == 'project' else "📋"
                response += f"{type_emoji} **{item.get('name', 'Unknown')}** ({item['type']})\n"
                if item.get('info'):
                    response += f"   {item['info'][:100]}{'...' if len(str(item.get('info', ''))) > 100 else ''}\n"
            else:
                # Generic formatting
                name = item.get('name') or item.get('title') or 'Unknown'
                response += f"• **{name}**\n"
                if item.get('description'):
                    response += f"   {item['description'][:100]}{'...' if len(item.get('description', '')) > 100 else ''}\n"
        
        if result_count > 10:
            response += f"\n... and {result_count - 10} more results"
    
    # Add metadata information
    processing_time = metadata.get('processing_time_ms', 0)
    if processing_time > 0:
        response += f"\n\n⚡ Processing time: {processing_time}ms"
        
    return response

@app.route('/ai/smart_chat', methods=['POST'])
def smart_chat():
    """Ultra-smart chat endpoint with comprehensive database search"""
    try:
        data = request.get_json()
        if not data or 'message' not in data:
            return jsonify({'error': 'Message is required'}), 400
        
        message = data['message'].strip()
        session_id = data.get('session_id', 'default')
        
        print(f"🎯 Received query: {message} (Session: {session_id})")
        
        # Add message to conversation history
        add_to_conversation_history(session_id, message, 'user')
        
        try:
            # First, try OpenAI ultra-comprehensive analysis
            openai_result = analyze_user_intent_with_openai(message, session_id)
            print(f"🤖 OpenAI Analysis Result: {openai_result}")
            
            if openai_result['success'] and openai_result.get('response'):
                # Add response to conversation history
                add_to_conversation_history(session_id, openai_result['response'], 'assistant')
                
                return jsonify({
                    'success': True,
                    'response': openai_result['response'],
                    'data_source': 'openai_enhanced_database',
                    'intent_type': openai_result.get('intent_type', 'comprehensive'),
                    'employee_data': openai_result.get('employee_data'),
                    'projects_data': openai_result.get('projects_data'),
                    'tasks_data': openai_result.get('tasks_data'),
                    'search_terms': openai_result.get('search_terms', []),
                    'timestamp': datetime.now().isoformat()
                })
            
            # If OpenAI doesn't find specific matches, use comprehensive search
            print("🔍 OpenAI didn't find specific matches, using comprehensive search...")
            comprehensive_results = comprehensive_crm_search(message)
            
            if comprehensive_results['found_matches']:
                response = format_comprehensive_response(comprehensive_results, message)
                
                # Add response to conversation history
                add_to_conversation_history(session_id, response, 'assistant')
                
                return jsonify({
                    'success': True,
                    'response': response,
                    'data_source': 'comprehensive_search',
                    'search_results': {
                        'employees': comprehensive_results['employees'],
                        'projects': comprehensive_results['projects'],
                        'tasks': comprehensive_results['tasks']
                    },
                    'search_terms': comprehensive_results['search_terms'],
                    'match_strategies': comprehensive_results['match_strategies'],
                    'timestamp': datetime.now().isoformat()
                })
            
            # Final fallback - intelligent no-match response
            fallback_response = f"""I searched through all our CRM data but couldn't find specific matches for "{message}".

🔍 **What I can help you with:**
• **Employee Info:** "Show me John Doe details" or "Who is working on project X?"
• **Projects:** "List all projects" or "What projects are in progress?"  
• **Tasks:** "Show pending tasks" or "What tasks are due this week?"
• **Performance:** "How is Sarah performing?" or "Team productivity report"
• **General Queries:** Try more specific terms or ask about specific people/projects

💡 **Tips for better results:**
- Use full names: "Hamza Haseeb projects" instead of just "Hamza"
- Be specific: "AI project status" instead of just "projects"  
- Try variations: "team members", "staff list", "employee roster"

Would you like me to show you all employees, projects, or tasks to help you get started?"""
            
            # Add fallback response to conversation history
            add_to_conversation_history(session_id, fallback_response, 'assistant')
            
            return jsonify({
                'success': True,
                'response': fallback_response,
                'data_source': 'fallback_help',
                'suggestions': ['List all employees', 'Show all projects', 'Display all tasks'],
                'timestamp': datetime.now().isoformat()
            })
            
        except Exception as e:
            print(f"❌ Query processing error: {e}")
            error_response = "Sorry, I encountered an error processing your query. Please try again or rephrase your question."
            
            # Add error response to conversation history
            add_to_conversation_history(session_id, error_response, 'assistant')
            
            return jsonify({
                'success': False,
                'response': error_response,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            })
        
    except Exception as e:
        print(f"❌ Smart chat critical error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'response': 'Sorry, I encountered a critical error. Please try again.'
        }), 500

@app.route('/test', methods=['GET'])
def test():
    """Test endpoint to verify server is running"""
    return jsonify({
        'message': 'Real CRM integration server is running!',
        'status': 'ok',
        'database_connection': get_database_connection() is not None
    })

@app.route('/api/hamza/projects', methods=['GET'])
def get_hamza_projects():
    """Direct API endpoint to get Hamza's projects"""
    projects = get_hamza_projects_from_db()
    if projects is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    return jsonify({
        'success': True,
        'projects': projects,
        'total': len(projects),
        'data_source': 'real_database'
    })

@app.route('/api/employees', methods=['GET'])
def get_employees():
    """API endpoint to get all employees"""
    employees = get_all_employees()
    if employees is None:
        return jsonify({'error': 'Database connection failed'}), 500
    
    return jsonify({
        'success': True,
        'employees': employees,
        'total': len(employees),
        'data_source': 'real_database'
    })

@app.route('/api/employee/<employee_name>/projects', methods=['GET'])
def get_employee_projects_api(employee_name):
    """API endpoint to get projects for a specific employee"""
    projects = get_employee_projects(employee_name=employee_name)
    
    if projects is None:
        # Try to find employee info for better error message
        employee = find_employee_by_name(employee_name)
        if employee:
            return jsonify({
                'success': True,
                'message': f"Found {employee['full_name']}, but no projects assigned yet",
                'projects': [],
                'employee': employee,
                'data_source': 'real_database'
            })
        else:
            return jsonify({'error': f'Employee "{employee_name}" not found'}), 404
    
    return jsonify({
        'success': True,
        'projects': projects,
        'total': len(projects),
        'employee_name': employee_name,
        'data_source': 'real_database'
    })

@app.route('/api/add-warnings', methods=['POST'])
def add_warnings():
    """API endpoint to manually add warning comments to overdue projects"""
    result = add_overdue_warning_comments()
    
    if result['success']:
        return jsonify({
            'success': True,
            'message': f"Added {result['warnings_added']} warning comments",
            'warnings_added': result['warnings_added'],
            'overdue_projects': result['overdue_projects']
        })
    else:
        return jsonify({
            'success': False,
            'error': result['error']
        }), 500

def format_comprehensive_response(comprehensive_results, original_query):
    """Format comprehensive search results into a helpful response"""
    try:
        if not comprehensive_results['found_matches']:
            return "I searched through all our CRM data but couldn't find specific matches for your query. Please try rephrasing your question or be more specific about what you're looking for."
        
        response_parts = []
        query_lower = original_query.lower()
        
        # Smart response introduction based on query type
        intro_phrases = []
        if any(word in query_lower for word in ['who', 'employee', 'staff', 'person', 'people']):
            intro_phrases.append("team members")
        if any(word in query_lower for word in ['project', 'work', 'development', 'initiative']):
            intro_phrases.append("projects")
        if any(word in query_lower for word in ['task', 'todo', 'assignment', 'activity']):
            intro_phrases.append("tasks")
        
        if intro_phrases:
            response_parts.append(f"Here's what I found regarding {' and '.join(intro_phrases)}:")
        else:
            response_parts.append("Here's what I found in our CRM system:")
        
        # EMPLOYEES SECTION
        if comprehensive_results['employees']:
            response_parts.append(f"\n👥 **TEAM MEMBERS ({len(comprehensive_results['employees'])} found):**")
            
            for i, emp in enumerate(comprehensive_results['employees'][:10], 1):
                name = f"{emp['firstname']} {emp['lastname']}"
                role = emp.get('role', 'No role specified')
                email = emp.get('email', 'No email')
                phone = emp.get('phonenumber', 'No phone')
                
                response_parts.append(f"{i}. **{name}** - {role}")
                response_parts.append(f"   📧 {email}")
                if phone and phone != 'No phone':
                    response_parts.append(f"   📱 {phone}")
                response_parts.append("")  # Empty line
        
        # PROJECTS SECTION
        if comprehensive_results['projects']:
            response_parts.append(f"\n🚀 **PROJECTS ({len(comprehensive_results['projects'])} found):**")
            
            for i, proj in enumerate(comprehensive_results['projects'][:10], 1):
                name = proj.get('name', 'Unnamed Project')
                status = proj.get('status', 'Unknown')
                progress = proj.get('progress', 0)
                client = proj.get('client_name', 'No client specified')
                deadline = proj.get('deadline', 'No deadline')
                
                # Status emoji mapping
                status_emojis = {
                    '1': '🆕', '2': '⏳', '3': '🔄', '4': '✅', '5': '❌',
                    'not_started': '🆕', 'in_progress': '🔄', 'completed': '✅', 'on_hold': '⏸️'
                }
                status_emoji = status_emojis.get(str(status).lower(), '📋')
                
                response_parts.append(f"{i}. {status_emoji} **{name}** ({progress}% complete)")
                response_parts.append(f"   🏢 Client: {client}")
                response_parts.append(f"   📅 Status: {status}")
                if deadline and deadline != 'No deadline':
                    response_parts.append(f"   ⏰ Deadline: {deadline}")
                
                # Add description if available and short
                if proj.get('description') and len(proj['description']) < 100:
                    response_parts.append(f"   📝 {proj['description']}")
                response_parts.append("")  # Empty line
        
        # TASKS SECTION
        if comprehensive_results['tasks']:
            response_parts.append(f"\n✅ **TASKS ({len(comprehensive_results['tasks'])} found):**")
            
            for i, task in enumerate(comprehensive_results['tasks'][:10], 1):
                name = task.get('name', 'Unnamed Task')
                status = task.get('status_name', task.get('status', 'Unknown'))
                priority = task.get('priority_name', task.get('priority', 'Normal'))
                project_name = task.get('project_name', 'No project')
                due_date = task.get('duedate', 'No due date')
                
                # Priority emoji mapping
                priority_emojis = {'High': '🔴', 'Urgent': '🚨', 'Normal': '🟡', 'Low': '🟢'}
                priority_emoji = priority_emojis.get(priority, '🟡')
                
                # Status emoji mapping
                status_emojis = {
                    'Not Started': '⭕', 'In Progress': '🔄', 'Completed': '✅',
                    'Testing': '🧪', 'On Hold': '⏸️'
                }
                status_emoji = status_emojis.get(status, '📋')
                
                response_parts.append(f"{i}. {status_emoji} **{name}** {priority_emoji} {priority}")
                if project_name and project_name != 'No project':
                    response_parts.append(f"   🚀 Project: {project_name}")
                response_parts.append(f"   📊 Status: {status}")
                if due_date and due_date != 'No due date':
                    response_parts.append(f"   ⏰ Due: {due_date}")
                response_parts.append("")  # Empty line
        
        # SUMMARY SECTION
        total_results = len(comprehensive_results['employees']) + len(comprehensive_results['projects']) + len(comprehensive_results['tasks'])
        
        if total_results > 0:
            summary_parts = []
            if comprehensive_results['employees']:
                summary_parts.append(f"{len(comprehensive_results['employees'])} team members")
            if comprehensive_results['projects']:
                summary_parts.append(f"{len(comprehensive_results['projects'])} projects")
            if comprehensive_results['tasks']:
                summary_parts.append(f"{len(comprehensive_results['tasks'])} tasks")
            
            response_parts.append(f"\n📊 **SUMMARY:** Found {', '.join(summary_parts)} matching your query.")
            
            # Add helpful suggestions
            suggestions = []
            if comprehensive_results['employees'] and len(comprehensive_results['employees']) > 1:
                suggestions.append("💡 **Tip:** For specific employee details, try asking about them by full name")
            if comprehensive_results['projects']:
                suggestions.append("💡 **Tip:** Ask about a specific project for detailed information and team members")
            if comprehensive_results['tasks']:
                suggestions.append("💡 **Tip:** Ask about task status or deadlines for more focused results")
            
            if suggestions:
                response_parts.extend([""] + suggestions)
        
        # Add search strategy info for debugging
        if comprehensive_results.get('match_strategies'):
            response_parts.append(f"\n🔍 Search strategies used: {', '.join(comprehensive_results['match_strategies'])}")
        
        return '\n'.join(response_parts)
    
    except Exception as e:
        print(f"Error formatting comprehensive response: {e}")
        return "I found some results but encountered an error formatting them. Please try your query again."

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint for the Enhanced Chatbot frontend"""
    try:
        # Test database connection
        connection = get_database_connection()
        db_status = 'ok' if connection else 'failed'
        if connection:
            connection.close()
            
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.now().isoformat(),
            'database_connection': db_status,
            'server': 'Real CRM Integration Server'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }), 500

def extract_person_name_from_query(user_message):
    """Extract person names from user query for targeted filtering"""
    import re
    
    # Common patterns for person-related queries
    patterns = [
        r"show me (.+?)(?:'s|projects|tasks|work|assignments)",
        r"(.+?)(?:'s|projects|tasks|work|assignments)",
        r"find (.+?)(?:'s|projects|tasks)",
        r"get (.+?)(?:'s|information|data|projects|tasks)",
        r"list (.+?)(?:'s|projects|tasks)",
        r"(?:show|find|get|list)\s+(.+?)\s+(?:projects|tasks|work)",
    ]
    
    for pattern in patterns:
        match = re.search(pattern, user_message, re.IGNORECASE)
        if match:
            name_part = match.group(1).strip()
            # Filter out common words
            if name_part.lower() not in ['all', 'the', 'some', 'any', 'employee', 'staff', 'person', 'user']:
                print(f"🔍 Extracted person name from query: '{name_part}'")
                return name_part
    
    return None

def get_comprehensive_database_results(user_message):
    """Get comprehensive results using intelligent table mapping with person-based filtering"""
    try:
        connection = get_database_connection()
        if not connection:
            return {'total_records': 0, 'results': {}}
        
        cursor = connection.cursor(dictionary=True)
        results = {}
        
        # Extract person name from query for targeted filtering
        person_name = extract_person_name_from_query(user_message)
        
        # Use intelligent table mapping if available
        if INTELLIGENT_MAPPING_ENABLED and table_mapper:
            print(f"🧠 Using intelligent table mapping for: {user_message}")
            if person_name:
                print(f"🎯 Person-specific query detected for: {person_name}")
            
            # Get query strategy from intelligent mapper
            strategy = get_query_strategy(user_message)
            relevant_tables = strategy['primary_tables'] + strategy['secondary_tables']
            
            print(f"📊 Intelligent analysis selected {len(relevant_tables)} tables: {relevant_tables[:5]}...")
            
            # Query each relevant table intelligently
            for table_name in relevant_tables[:20]:  # Increased limit to 20 tables max
                try:
                    print(f"🔍 Querying table: {table_name}")
                    
                    # Get table structure first
                    cursor.execute(f"DESCRIBE {table_name}")
                    describe_results = cursor.fetchall()
                    # Since we're using dictionary=True, access by key name instead of index
                    all_columns = [col['Field'] for col in describe_results]
                    select_columns = all_columns[:10]  # Show more columns for better results
                    
                    print(f"📋 Table {table_name} columns: {all_columns[:10]}")
                    
                    # Build query with person-specific filtering if applicable
                    query = f"SELECT {', '.join(select_columns)} FROM {table_name}"
                    params = []
                    
                    if person_name:
                        # Add person-specific WHERE clauses based on table type
                        where_conditions = []
                        
                        # For staff-related tables
                        if table_name == 'tblstaff':
                            where_conditions.append("(firstname LIKE %s OR lastname LIKE %s OR CONCAT(firstname, ' ', lastname) LIKE %s)")
                            params.extend([f"%{person_name}%", f"%{person_name}%", f"%{person_name}%"])
                        
                        # For projects table - find projects where the person is involved
                        elif table_name == 'tblprojects':
                            where_conditions.append("""
                                (id IN (
                                    SELECT DISTINCT pm.project_id FROM tblproject_members pm
                                    JOIN tblstaff s ON pm.staff_id = s.staffid
                                    WHERE s.firstname LIKE %s OR s.lastname LIKE %s OR CONCAT(s.firstname, ' ', s.lastname) LIKE %s
                                ) OR 
                                id IN (
                                    SELECT DISTINCT po.project_id FROM tblproject_owners po
                                    JOIN tblstaff s ON po.staff_id = s.staffid
                                    WHERE s.firstname LIKE %s OR s.lastname LIKE %s OR CONCAT(s.firstname, ' ', s.lastname) LIKE %s
                                ) OR
                                name LIKE %s)
                            """)
                            params.extend([f"%{person_name}%", f"%{person_name}%", f"%{person_name}%", 
                                         f"%{person_name}%", f"%{person_name}%", f"%{person_name}%", 
                                         f"%{person_name}%"])
                        
                        # For tasks table - find tasks assigned to the person
                        elif table_name == 'tbltasks':
                            where_conditions.append("""
                                id IN (
                                    SELECT DISTINCT ta.taskid FROM tbltask_assigned ta
                                    JOIN tblstaff s ON ta.staffid = s.staffid
                                    WHERE s.firstname LIKE %s OR s.lastname LIKE %s OR CONCAT(s.firstname, ' ', s.lastname) LIKE %s
                                )
                            """)
                            params.extend([f"%{person_name}%", f"%{person_name}%", f"%{person_name}%"])
                        
                        # For project members table - direct staff filtering
                        elif table_name == 'tblproject_members':
                            where_conditions.append("""
                                staff_id IN (
                                    SELECT staffid FROM tblstaff
                                    WHERE firstname LIKE %s OR lastname LIKE %s OR CONCAT(firstname, ' ', lastname) LIKE %s
                                )
                            """)
                            params.extend([f"%{person_name}%", f"%{person_name}%", f"%{person_name}%"])
                        
                        # For other tables, try to find name-like columns
                        else:
                            name_columns = [col for col in all_columns if any(keyword in col.lower() for keyword in ['name', 'firstname', 'lastname'])]
                            if name_columns:
                                for col in name_columns:
                                    where_conditions.append(f"{col} LIKE %s")
                                    params.append(f"%{person_name}%")
                        
                        if where_conditions:
                            query += " WHERE " + " OR ".join(where_conditions)
                    
                    query += " LIMIT 10000"
                    print(f"🔍 Executing query: {query[:200]}..." if len(query) > 200 else query)
                    
                    if params:
                        cursor.execute(query, params)
                    else:
                        cursor.execute(query)
                    table_results = cursor.fetchall()
                    
                    if table_results:
                        results[table_name] = table_results
                        print(f"✅ Found {len(table_results)} records in {table_name}")
                    else:
                        print(f"⚠️ No records found in {table_name}")
                    
                except Exception as e:
                    print(f"❌ Database error querying {table_name}: {str(e)}")
                    print(f"❌ Exception type: {type(e).__name__}")
                    import traceback
                    print(f"❌ Full traceback: {traceback.format_exc()}")
                    continue
        
        else:
            # Fallback: query core tables with original method
            print("📊 Using fallback core table queries")
            core_tables = ['tblstaff', 'tblprojects', 'tbltasks']
            
            for table_name in core_tables:
                try:
                    # Simple name-based search for core tables
                    if table_name == 'tblstaff':
                        query = """
                        SELECT staffid, firstname, lastname, email, phonenumber, role, active
                        FROM tblstaff 
                        WHERE firstname LIKE %s OR lastname LIKE %s OR email LIKE %s OR role LIKE %s
                        LIMIT 10000
                        """
                        search_term = f"%{user_message}%"
                        cursor.execute(query, (search_term, search_term, search_term, search_term))
                    
                    elif table_name == 'tblprojects':
                        query = """
                        SELECT id, name, description, status, progress, deadline, clientid
                        FROM tblprojects 
                        WHERE name LIKE %s OR description LIKE %s
                        LIMIT 10000
                        """
                        search_term = f"%{user_message}%"
                        cursor.execute(query, (search_term, search_term))
                    
                    elif table_name == 'tbltasks':
                        query = """
                        SELECT id, name, description, status, priority, rel_id, duedate
                        FROM tbltasks 
                        WHERE name LIKE %s OR description LIKE %s
                        LIMIT 10000
                        """
                        search_term = f"%{user_message}%"
                        cursor.execute(query, (search_term, search_term))
                    
                    table_results = cursor.fetchall()
                    if table_results:
                        results[table_name] = table_results
                        print(f"✅ Fallback found {len(table_results)} records in {table_name}")
                        
                except Exception as e:
                    print(f"⚠️ Fallback error querying {table_name}: {e}")
                    continue
        
        total_records = sum(len(records) for records in results.values())
        print(f"🎯 Total comprehensive search results: {total_records} records from {len(results)} tables")
        
        return {
            'total_records': total_records,
            'results': results,
            'intelligent_mapping_used': INTELLIGENT_MAPPING_ENABLED,
            'tables_queried': list(results.keys())
        }
        
    except Exception as e:
        print(f"❌ Error in comprehensive database search: {e}")
        return {'total_records': 0, 'results': {}, 'error': str(e)}
    finally:
        if connection:
            connection.close()

def format_comprehensive_response(comprehensive_results, user_message):
    """Format comprehensive results into readable response with person-specific formatting"""
    try:
        results = comprehensive_results.get('results', {})
        total_records = comprehensive_results.get('total_records', 0)
        
        if total_records == 0:
            return "I couldn't find any matching records for your query. Please try being more specific."
        
        # Check if this is a person-specific query
        person_name = extract_person_name_from_query(user_message)
        
        if person_name:
            response = f"🔍 **Search Results for '{person_name}'** (found {total_records} records)\n\n"
        else:
            response = f"🔍 **Search Results** (found {total_records} records)\n\n"
        
        # Format results from each table
        for table, records in results.items():
            if not records:
                continue
                
            table_name = table.replace('tbl', '').replace('_', ' ').title()
            response += f"**{table_name}** ({len(records)} records):\n"
            
            # Format based on table type with person-specific context
            if table == 'tblstaff':
                for i, record in enumerate(records, 1):
                    name = f"{record.get('firstname', '')} {record.get('lastname', '')}".strip()
                    email = record.get('email', '')
                    role = record.get('role', 'No role')
                    response += f"{i}. **{name}** - {role}\n"
                    if email:
                        response += f"   📧 {email}\n"
                    if record.get('phonenumber'):
                        response += f"   📱 {record['phonenumber']}\n"
                        
            elif table == 'tblprojects':
                for i, record in enumerate(records, 1):
                    name = record.get('name', 'Unnamed Project')
                    status = record.get('status', 'Unknown')
                    progress = record.get('progress', 0)
                    response += f"{i}. **{name}**\n"
                    response += f"   Status: {status} | Progress: {progress}%\n"
                    if record.get('deadline'):
                        response += f"   Deadline: {record['deadline']}\n"
                    if record.get('clientid'):
                        response += f"   Client ID: {record['clientid']}\n"
                        
            elif table == 'tbltasks':
                for i, record in enumerate(records, 1):
                    name = record.get('name', 'Unnamed Task')
                    status = record.get('status', 'Unknown')
                    priority = record.get('priority', 'Normal')
                    response += f"{i}. **{name}**\n"
                    response += f"   Status: {status} | Priority: {priority}\n"
                    if record.get('duedate'):
                        response += f"   Due: {record['duedate']}\n"
                    if record.get('rel_id'):
                        response += f"   Related to: {record['rel_id']}\n"
            
            elif table == 'tblproject_members':
                # Group by project for better readability
                project_groups = {}
                for record in records:
                    proj_id = record.get('project_id', 'Unknown')
                    if proj_id not in project_groups:
                        project_groups[proj_id] = []
                    project_groups[proj_id].append(record)
                
                for proj_id, members in project_groups.items():
                    response += f"   Project {proj_id}: {len(members)} member(s)\n"
            
            else:
                # Generic formatting for other tables
                for i, record in enumerate(records, 1):
                    # Try to find the most relevant field to display
                    display_field = None
                    for field in ['name', 'title', 'subject', 'description']:
                        if field in record and record[field]:
                            display_field = field
                            break
                    
                    if display_field:
                        response += f"{i}. **{record[display_field]}**\n"
                        # Show a few other relevant fields
                        for key, value in list(record.items())[:3]:
                            if key != display_field and value:
                                response += f"   {key.title()}: {value}\n"
                    else:
                        # Show first few non-null fields
                        non_null_fields = {k: v for k, v in record.items() if v is not None and str(v).strip()}
                        for key, value in list(non_null_fields.items())[:3]:
                            response += f"   {key.title()}: {value}\n"
                        response += "\n"
            
            response += "\n"
        
        # Add helpful context for person-specific queries
        if person_name and 'tblprojects' in results and len(results['tblprojects']) > 0:
            response += f"💡 **Found {len(results['tblprojects'])} projects related to {person_name}**\n"
        elif person_name and 'tblprojects' in results and len(results['tblprojects']) == 0:
            response += f"ℹ️ **No projects found specifically assigned to {person_name}**\n"
        
        return response
        
    except Exception as e:
        print(f"❌ Error formatting response: {e}")
        return f"Found {total_records} records but couldn't format them properly."

@app.route('/ai/enhanced_chat', methods=['POST', 'OPTIONS'])
def enhanced_chat():
    """Enhanced chat endpoint compatible with the Enhanced Chatbot frontend"""
    
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
        session_id = data.get('session_id', 'default')
        
        print(f"🚀 Enhanced Chat Query: {user_message} [Session: {session_id}]")
        
        start_time = datetime.now()
        
        # Use the existing smart_chat functionality
        session = get_or_create_session(session_id)
        
        # Get comprehensive database results
        comprehensive_results = get_comprehensive_database_results(user_message)
        
        # Format response
        if comprehensive_results and comprehensive_results.get('total_records', 0) > 0:
            response_text = format_comprehensive_response(comprehensive_results, user_message)
        else:
            response_text = "I couldn't find any specific results for your query. Could you please be more specific or try asking about employees, projects, or tasks?"
        
        # Add to conversation history
        add_to_history(session_id, user_message, response_text, {
            'total_records': comprehensive_results.get('total_records', 0),
            'tables_searched': list(comprehensive_results.get('results', {}).keys())
        })
        
        # Calculate processing time
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Return response in Enhanced Chatbot format
        response_data = {
            'success': True,
            'response': response_text,
            'session_id': session_id,
            'prompt_id': len(session['messages']),
            'analysis': {
                'intent': 'general_query',
                'confidence': 0.8,
                'entities': [],
                'search_terms': user_message.split()
            },
            'processing_time_ms': processing_time,
            'records_found': comprehensive_results.get('total_records', 0),
            'tables_scanned': list(comprehensive_results.get('results', {}).keys()),
            'conversation_length': len(session['messages'])
        }
        
        response = make_response(jsonify(response_data))
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
        
    except Exception as e:
        print(f"❌ Enhanced Chat Error: {str(e)}")
        error_response = {
            'success': False,
            'error': str(e),
            'response': 'I encountered an error processing your request. Please try again.'
        }
        response = make_response(jsonify(error_response), 500)
        response.headers.add("Access-Control-Allow-Origin", "*")
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
        session_id = data.get('session_id', 'default')
        message_id = data.get('message_id', 0)
        feedback = data.get('feedback', 'neutral')  # 'positive', 'negative', 'neutral'
        rating = data.get('rating', 3)  # 1-5 scale
        
        print(f"👍 Feedback recorded: {feedback} ({rating}/5) for session {session_id}")
        
        # In a real implementation, you would store this in a database
        # For now, we'll just log it
        
        response_data = {
            'success': True,
            'message': 'Feedback recorded successfully',
            'feedback_id': datetime.now().isoformat()
        }
        
        response = make_response(jsonify(response_data))
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
        
    except Exception as e:
        print(f"❌ Feedback Error: {str(e)}")
        error_response = {
            'success': False,
            'error': str(e)
        }
        response = make_response(jsonify(error_response), 500)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

@app.route('/ai/conversation_history/<session_id>', methods=['GET'])
def get_conversation_history_endpoint(session_id):
    """Get conversation history for a session"""
    try:
        session = get_or_create_session(session_id)
        
        response_data = {
            'success': True,
            'session_id': session_id,
            'conversation_history': session['messages'],
            'total_interactions': len(session['messages'])
        }
        
        response = make_response(jsonify(response_data))
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response
        
    except Exception as e:
        print(f"❌ History Error: {str(e)}")
        error_response = {
            'success': False,
            'error': str(e)
        }
        response = make_response(jsonify(error_response), 500)
        response.headers.add("Access-Control-Allow-Origin", "*")
        return response

if __name__ == '__main__':
    print("🚀 Starting Real CRM Integration Server...")
    print(f"📊 Database Host: {os.getenv('DB_HOST')}")
    print(f"📊 Database Name: {os.getenv('DB_NAME')}")
    
    # Test database connection
    if get_database_connection():
        print("✅ Database connection successful!")
    else:
        print("❌ Database connection failed!")
    
    app.run(debug=True, host='127.0.0.1', port=5001)