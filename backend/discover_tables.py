#!/usr/bin/env python3
"""
Database Table Discovery and Categorization System
This script will discover all tables in the database and organize them by categories
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

def get_database_connection():
    """Get MySQL database connection"""
    try:
        connection = mysql.connector.connect(**DB_CONFIG)
        return connection
    except Exception as e:
        print(f"Database connection error: {e}")
        return None

def discover_all_tables():
    """Discover all tables in the database with their column information"""
    connection = get_database_connection()
    if not connection:
        return {}
    
    try:
        cursor = connection.cursor()
        
        # Get all table names
        cursor.execute("SHOW TABLES")
        tables = [table[0] for table in cursor.fetchall()]
        
        table_info = {}
        
        for table in tables:
            try:
                # Get column information for each table
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                
                # Get sample data count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                table_info[table] = {
                    'columns': [col[0] for col in columns],
                    'column_details': {col[0]: col[1] for col in columns},
                    'row_count': row_count
                }
                
                print(f"✅ {table}: {len(columns)} columns, {row_count} rows")
                
            except Exception as e:
                print(f"❌ Error analyzing table {table}: {e}")
                continue
                
        return table_info
        
    except Exception as e:
        print(f"Error discovering tables: {e}")
        return {}
    finally:
        connection.close()

def categorize_tables(table_info):
    """Categorize tables based on their names and columns"""
    categories = {
        'STAFF_TABLES': {
            'description': 'Employee and staff related tables',
            'keywords': ['staff', 'employee', 'user', 'member', 'person', 'department', 'role'],
            'tables': []
        },
        'PROJECT_TABLES': {
            'description': 'Project management related tables',
            'keywords': ['project', 'client', 'proposal', 'milestone', 'phase'],
            'tables': []
        },
        'TASK_TABLES': {
            'description': 'Task and assignment related tables',
            'keywords': ['task', 'assignment', 'todo', 'work', 'activity'],
            'tables': []
        },
        'FINANCIAL_TABLES': {
            'description': 'Financial and billing related tables',
            'keywords': ['invoice', 'payment', 'expense', 'estimate', 'credit', 'item', 'tax', 'currency'],
            'tables': []
        },
        'TIME_TRACKING_TABLES': {
            'description': 'Time tracking and timesheets',
            'keywords': ['time', 'timesheet', 'timer', 'hour', 'log'],
            'tables': []
        },
        'COMMUNICATION_TABLES': {
            'description': 'Communication and messaging',
            'keywords': ['message', 'notification', 'email', 'reminder', 'announcement', 'discussion', 'comment'],
            'tables': []
        },
        'CLIENT_TABLES': {
            'description': 'Client and customer management',
            'keywords': ['client', 'customer', 'contact', 'company', 'lead'],
            'tables': []
        },
        'SYSTEM_TABLES': {
            'description': 'System configuration and settings',
            'keywords': ['setting', 'config', 'option', 'template', 'custom', 'field'],
            'tables': []
        },
        'DOCUMENT_TABLES': {
            'description': 'Document and file management',
            'keywords': ['file', 'document', 'attachment', 'upload', 'media'],
            'tables': []
        },
        'WORKFLOW_TABLES': {
            'description': 'Workflow and process management',
            'keywords': ['workflow', 'approval', 'status', 'pipeline', 'process'],
            'tables': []
        },
        'ANALYTICS_TABLES': {
            'description': 'Analytics and reporting',
            'keywords': ['report', 'analytics', 'stat', 'metric', 'dashboard'],
            'tables': []
        }
    }
    
    # Categorize each table
    for table_name, table_data in table_info.items():
        table_lower = table_name.lower()
        categorized = False
        
        # Check each category
        for category_key, category_data in categories.items():
            # Check if table name contains any of the category keywords
            for keyword in category_data['keywords']:
                if keyword in table_lower:
                    category_data['tables'].append({
                        'name': table_name,
                        'columns': table_data['columns'],
                        'row_count': table_data['row_count']
                    })
                    categorized = True
                    break
            
            if categorized:
                break
        
        # If not categorized, check columns for hints
        if not categorized:
            column_text = ' '.join(table_data['columns']).lower()
            for category_key, category_data in categories.items():
                for keyword in category_data['keywords']:
                    if keyword in column_text:
                        category_data['tables'].append({
                            'name': table_name,
                            'columns': table_data['columns'],
                            'row_count': table_data['row_count']
                        })
                        categorized = True
                        break
                
                if categorized:
                    break
        
        # If still not categorized, add to system tables
        if not categorized:
            categories['SYSTEM_TABLES']['tables'].append({
                'name': table_name,
                'columns': table_data['columns'],
                'row_count': table_data['row_count']
            })
    
    return categories

def generate_table_mapping_code(categories):
    """Generate Python code for the table mapping system"""
    
    code = '''
# DATABASE TABLE CATEGORIZATION SYSTEM
# Auto-generated table categories for intelligent query routing

TABLE_CATEGORIES = {
'''
    
    for category_key, category_data in categories.items():
        if category_data['tables']:  # Only include categories that have tables
            code += f"    '{category_key}': {{\n"
            code += f"        'description': '{category_data['description']}',\n"
            code += f"        'keywords': {category_data['keywords']},\n"
            code += f"        'tables': [\n"
            
            for table in category_data['tables']:
                code += f"            {{\n"
                code += f"                'name': '{table['name']}',\n"
                code += f"                'columns': {table['columns']},\n"
                code += f"                'row_count': {table['row_count']}\n"
                code += f"            }},\n"
            
            code += f"        ]\n"
            code += f"    }},\n"
    
    code += '''
}

def get_relevant_tables_for_query(user_query):
    """Determine which tables are relevant for a user query"""
    query_lower = user_query.lower()
    relevant_tables = []
    matched_categories = []
    
    # Check each category
    for category_key, category_data in TABLE_CATEGORIES.items():
        category_matched = False
        
        # Check if query contains category keywords
        for keyword in category_data['keywords']:
            if keyword in query_lower:
                category_matched = True
                break
        
        if category_matched:
            matched_categories.append(category_key)
            for table in category_data['tables']:
                relevant_tables.append(table['name'])
    
    # If no specific category matched, include core tables
    if not relevant_tables:
        core_categories = ['STAFF_TABLES', 'PROJECT_TABLES', 'TASK_TABLES', 'CLIENT_TABLES']
        for category_key in core_categories:
            if category_key in TABLE_CATEGORIES:
                for table in TABLE_CATEGORIES[category_key]['tables']:
                    relevant_tables.append(table['name'])
    
    return {
        'tables': list(set(relevant_tables)),  # Remove duplicates
        'categories': matched_categories,
        'total_tables': len(set(relevant_tables))
    }

def get_table_columns(table_name):
    """Get column names for a specific table"""
    for category_data in TABLE_CATEGORIES.values():
        for table in category_data['tables']:
            if table['name'] == table_name:
                return table['columns']
    return []

def get_table_info(table_name):
    """Get complete information about a table"""
    for category_data in TABLE_CATEGORIES.values():
        for table in category_data['tables']:
            if table['name'] == table_name:
                return table
    return None
'''
    
    return code

if __name__ == '__main__':
    print("🔍 Discovering all database tables...")
    print("=" * 50)
    
    # Discover all tables
    table_info = discover_all_tables()
    
    if not table_info:
        print("❌ No tables found or connection failed!")
        exit(1)
    
    print(f"\n✅ Found {len(table_info)} tables in database")
    print("=" * 50)
    
    # Categorize tables
    print("📊 Categorizing tables...")
    categories = categorize_tables(table_info)
    
    # Print categorization results
    print("\n🗂️ TABLE CATEGORIZATION RESULTS:")
    print("=" * 50)
    
    total_categorized = 0
    for category_key, category_data in categories.items():
        if category_data['tables']:
            print(f"\n{category_key} ({len(category_data['tables'])} tables):")
            print(f"   Description: {category_data['description']}")
            for table in category_data['tables']:
                print(f"   ✅ {table['name']} ({table['row_count']} rows)")
            total_categorized += len(category_data['tables'])
    
    print(f"\n📊 SUMMARY: {total_categorized} tables categorized into {len([c for c in categories.values() if c['tables']])} categories")
    
    # Generate code
    print("\n⚙️ Generating table mapping code...")
    code = generate_table_mapping_code(categories)
    
    # Save to file
    with open('table_categories.py', 'w', encoding='utf-8') as f:
        f.write(code)
    
    print("✅ Table categorization code saved to 'table_categories.py'")
    print("\n🚀 You can now import this in your main server!")
    print("Usage:")
    print("from table_categories import get_relevant_tables_for_query")
    print("relevant = get_relevant_tables_for_query('show me all employees')")
    print("print(relevant['tables'])")