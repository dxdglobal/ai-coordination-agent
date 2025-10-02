#!/usr/bin/env python3
"""
Database Table Discovery and Categorization System
This script will scan all tables in the database and organize them by categories
"""

import mysql.connector
import os
from dotenv import load_dotenv
import json

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
    """Discover all tables in the database with their columns"""
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
                # Get column information
                cursor.execute(f"DESCRIBE {table}")
                columns = cursor.fetchall()
                
                # Get sample data to understand content
                cursor.execute(f"SELECT * FROM {table} LIMIT 3")
                sample_data = cursor.fetchall()
                
                # Get row count
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                table_info[table] = {
                    'columns': [col[0] for col in columns],
                    'column_details': {col[0]: {'type': col[1], 'null': col[2], 'key': col[3], 'default': col[4]} for col in columns},
                    'sample_data': sample_data,
                    'row_count': row_count
                }
                
                print(f"✅ Analyzed {table}: {len(columns)} columns, {row_count} rows")
                
            except Exception as e:
                print(f"❌ Error analyzing table {table}: {e}")
                continue
        
        return table_info
        
    except Exception as e:
        print(f"Error discovering tables: {e}")
        return {}
    finally:
        if connection:
            connection.close()

def categorize_tables(table_info):
    """Categorize tables based on their names and content"""
    
    categories = {
        'projects': {
            'description': 'Project management and project-related data',
            'keywords': ['project', 'proj'],
            'tables': []
        },
        'tasks': {
            'description': 'Task management and assignments',
            'keywords': ['task', 'assignment', 'todo'],
            'tables': []
        },
        'staff': {
            'description': 'Employee and staff management',
            'keywords': ['staff', 'employee', 'user', 'member', 'person'],
            'tables': []
        },
        'clients': {
            'description': 'Client and customer management',
            'keywords': ['client', 'customer', 'contact', 'lead'],
            'tables': []
        },
        'invoices': {
            'description': 'Billing and invoice management',
            'keywords': ['invoice', 'bill', 'payment', 'estimate', 'proposal'],
            'tables': []
        },
        'timesheets': {
            'description': 'Time tracking and timesheets',
            'keywords': ['time', 'timesheet', 'hour', 'tracking'],
            'tables': []
        },
        'files': {
            'description': 'File and document management',
            'keywords': ['file', 'document', 'attachment', 'media'],
            'tables': []
        },
        'communication': {
            'description': 'Communication and messaging',
            'keywords': ['message', 'email', 'notification', 'comment', 'discussion'],
            'tables': []
        },
        'system': {
            'description': 'System configuration and settings',
            'keywords': ['setting', 'config', 'option', 'permission', 'role'],
            'tables': []
        },
        'reports': {
            'description': 'Reports and analytics',
            'keywords': ['report', 'analytic', 'stat', 'summary'],
            'tables': []
        },
        'misc': {
            'description': 'Miscellaneous and uncategorized tables',
            'keywords': [],
            'tables': []
        }
    }
    
    # Categorize each table
    for table_name, info in table_info.items():
        categorized = False
        
        # Check each category
        for category, cat_info in categories.items():
            if category == 'misc':
                continue
                
            # Check if table name contains category keywords
            table_lower = table_name.lower()
            for keyword in cat_info['keywords']:
                if keyword in table_lower:
                    categories[category]['tables'].append({
                        'name': table_name,
                        'columns': info['columns'],
                        'row_count': info['row_count'],
                        'key_columns': [col for col in info['columns'] if 'id' in col.lower() or 'name' in col.lower()]
                    })
                    categorized = True
                    break
            
            if categorized:
                break
        
        # If not categorized, put in misc
        if not categorized:
            categories['misc']['tables'].append({
                'name': table_name,
                'columns': info['columns'],
                'row_count': info['row_count'],
                'key_columns': [col for col in info['columns'] if 'id' in col.lower() or 'name' in col.lower()]
            })
    
    return categories

def generate_intelligent_query_mapper(categories):
    """Generate intelligent query mapping system"""
    
    query_patterns = {
        'employee_queries': {
            'patterns': ['employee', 'staff', 'worker', 'team member', 'person', 'who is', 'show me staff'],
            'primary_tables': [],
            'related_tables': []
        },
        'project_queries': {
            'patterns': ['project', 'proj', 'assignment', 'work on', 'working on', 'project status'],
            'primary_tables': [],
            'related_tables': []
        },
        'task_queries': {
            'patterns': ['task', 'todo', 'assignment', 'due', 'deadline', 'complete', 'finish'],
            'primary_tables': [],
            'related_tables': []
        },
        'client_queries': {
            'patterns': ['client', 'customer', 'contact', 'company', 'business'],
            'primary_tables': [],
            'related_tables': []
        },
        'invoice_queries': {
            'patterns': ['invoice', 'bill', 'payment', 'cost', 'price', 'estimate', 'proposal'],
            'primary_tables': [],
            'related_tables': []
        },
        'timesheet_queries': {
            'patterns': ['time', 'hour', 'worked', 'timesheet', 'tracking', 'logged'],
            'primary_tables': [],
            'related_tables': []
        },
        'file_queries': {
            'patterns': ['file', 'document', 'attachment', 'download', 'upload'],
            'primary_tables': [],
            'related_tables': []
        }
    }
    
    # Map categories to query types
    for query_type, query_info in query_patterns.items():
        category_name = query_type.replace('_queries', '')
        
        if category_name in ['employee']:
            category_name = 'staff'
        elif category_name in ['invoice']:
            category_name = 'invoices'
        elif category_name in ['timesheet']:
            category_name = 'timesheets'
        elif category_name in ['file']:
            category_name = 'files'
        
        if category_name in categories:
            query_info['primary_tables'] = [table['name'] for table in categories[category_name]['tables']]
            
            # Add related tables
            if category_name == 'staff':
                query_info['related_tables'] = [table['name'] for table in categories['projects']['tables'] + categories['tasks']['tables']]
            elif category_name == 'projects':
                query_info['related_tables'] = [table['name'] for table in categories['staff']['tables'] + categories['tasks']['tables']]
            elif category_name == 'tasks':
                query_info['related_tables'] = [table['name'] for table in categories['staff']['tables'] + categories['projects']['tables']]
    
    return query_patterns

def main():
    print("🔍 Starting Database Table Discovery and Categorization...")
    print("=" * 60)
    
    # Step 1: Discover all tables
    print("\n📊 Step 1: Discovering all database tables...")
    table_info = discover_all_tables()
    
    if not table_info:
        print("❌ Failed to discover tables. Check database connection.")
        return
    
    print(f"✅ Discovered {len(table_info)} tables")
    
    # Step 2: Categorize tables
    print("\n🏷️  Step 2: Categorizing tables...")
    categories = categorize_tables(table_info)
    
    # Step 3: Generate query mapper
    print("\n🧠 Step 3: Generating intelligent query mapper...")
    query_patterns = generate_intelligent_query_mapper(categories)
    
    # Step 4: Display results
    print("\n" + "=" * 60)
    print("📋 DATABASE TABLE CATEGORIZATION RESULTS")
    print("=" * 60)
    
    for category, info in categories.items():
        if info['tables']:
            print(f"\n🔸 {category.upper()} ({len(info['tables'])} tables)")
            print(f"   Description: {info['description']}")
            for table in info['tables']:
                print(f"   • {table['name']} ({table['row_count']} rows, {len(table['columns'])} columns)")
                print(f"     Key columns: {', '.join(table['key_columns'][:5])}")
    
    # Step 5: Save configuration
    print(f"\n💾 Step 5: Saving configuration...")
    
    config = {
        'table_categories': categories,
        'query_patterns': query_patterns,
        'table_schemas': table_info
    }
    
    with open('database_table_config.json', 'w', encoding='utf-8') as f:
        json.dump(config, f, indent=2, default=str)
    
    print("✅ Configuration saved to 'database_table_config.json'")
    
    # Step 6: Generate Python code
    print(f"\n🐍 Step 6: Generating Python implementation...")
    generate_python_implementation(categories, query_patterns)
    
    print("\n🎉 Database analysis complete!")
    print("📁 Files generated:")
    print("   • database_table_config.json - Full configuration")
    print("   • intelligent_table_mapper.py - Python implementation")

def generate_python_implementation(categories, query_patterns):
    """Generate Python implementation for the intelligent table mapper"""
    
    python_code = f'''"""
Intelligent Database Table Mapper
Auto-generated from database analysis on {os.getenv('DB_NAME')}
This module provides intelligent table selection based on user queries
"""

import re
from typing import List, Dict, Set

class IntelligentTableMapper:
    def __init__(self):
        self.table_categories = {repr(categories)}
        
        self.query_patterns = {repr(query_patterns)}
    
    def analyze_user_query(self, user_query: str) -> Dict:
        """Analyze user query and determine relevant tables"""
        query_lower = user_query.lower()
        
        # Remove common words
        stop_words = {{"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should", "may", "might", "can", "must"}}
        
        words = [word for word in query_lower.split() if word not in stop_words and len(word) > 2]
        
        relevant_tables = set()
        matched_patterns = []
        confidence_scores = {{}}
        
        # Check each query pattern
        for query_type, pattern_info in self.query_patterns.items():
            score = 0
            pattern_matches = []
            
            for pattern in pattern_info['patterns']:
                if pattern in query_lower:
                    score += 2
                    pattern_matches.append(pattern)
                    relevant_tables.update(pattern_info['primary_tables'])
                    relevant_tables.update(pattern_info['related_tables'][:2])  # Limit related tables
            
            # Check for word matches
            for word in words:
                for pattern in pattern_info['patterns']:
                    if word in pattern or pattern in word:
                        score += 1
                        pattern_matches.append(f"word_match: {{word}}")
                        relevant_tables.update(pattern_info['primary_tables'])
            
            if score > 0:
                confidence_scores[query_type] = score
                matched_patterns.extend(pattern_matches)
        
        # If no specific patterns matched, include core tables
        if not relevant_tables:
            relevant_tables.update(['tblstaff', 'tblprojects', 'tbltasks'])
            matched_patterns.append('fallback_core_tables')
        
        return {{
            'relevant_tables': list(relevant_tables),
            'matched_patterns': matched_patterns,
            'confidence_scores': confidence_scores,
            'query_analysis': {{
                'original_query': user_query,
                'processed_words': words,
                'dominant_intent': max(confidence_scores.items(), key=lambda x: x[1])[0] if confidence_scores else 'general'
            }}
        }}
    
    def get_table_info(self, table_name: str) -> Dict:
        """Get information about a specific table"""
        for category, info in self.table_categories.items():
            for table in info['tables']:
                if table['name'] == table_name:
                    return {{
                        'name': table_name,
                        'category': category,
                        'columns': table['columns'],
                        'key_columns': table['key_columns'],
                        'row_count': table['row_count']
                    }}
        return None
    
    def get_optimized_query_strategy(self, user_query: str) -> Dict:
        """Get optimized querying strategy for user query"""
        analysis = self.analyze_user_query(user_query)
        
        strategy = {{
            'primary_tables': [],
            'secondary_tables': [],
            'search_columns': {{}},
            'join_strategy': [],
            'limit_per_table': 50
        }}
        
        # Prioritize tables based on confidence
        high_confidence_tables = []
        medium_confidence_tables = []
        
        for table in analysis['relevant_tables']:
            table_info = self.get_table_info(table)
            if table_info:
                # High confidence: direct matches with high row count
                if table_info['row_count'] > 10 and any(pattern in user_query.lower() for pattern in [table_info['category']]):
                    high_confidence_tables.append(table)
                else:
                    medium_confidence_tables.append(table)
        
        strategy['primary_tables'] = high_confidence_tables[:3]  # Limit to 3 primary
        strategy['secondary_tables'] = medium_confidence_tables[:2]  # Limit to 2 secondary
        
        # Define search columns for each table
        query_words = user_query.lower().split()
        for table in strategy['primary_tables'] + strategy['secondary_tables']:
            table_info = self.get_table_info(table)
            if table_info:
                # Smart column selection
                search_cols = []
                for col in table_info['columns']:
                    col_lower = col.lower()
                    if any(word in col_lower for word in ['name', 'title', 'description', 'email']):
                        search_cols.append(col)
                
                if not search_cols:  # Fallback to key columns
                    search_cols = table_info['key_columns'][:3]
                
                strategy['search_columns'][table] = search_cols[:5]  # Limit columns
        
        return strategy

# Global instance
table_mapper = IntelligentTableMapper()

def get_relevant_tables_for_query(user_query: str) -> List[str]:
    """Simple function to get relevant tables for a query"""
    analysis = table_mapper.analyze_user_query(user_query)
    return analysis['relevant_tables']

def get_query_strategy(user_query: str) -> Dict:
    """Get complete query strategy for user input"""
    return table_mapper.get_optimized_query_strategy(user_query)

if __name__ == "__main__":
    # Test the mapper
    test_queries = [
        "Show me all employees",
        "Find Hamza's projects", 
        "What tasks are overdue?",
        "Show client invoices",
        "Time tracking for this week",
        "Project files and documents"
    ]
    
    print("🧪 Testing Intelligent Table Mapper")
    print("=" * 50)
    
    for query in test_queries:
        print(f"\\nQuery: '{{query}}'")
        strategy = get_query_strategy(query)
        print(f"Primary tables: {{strategy['primary_tables']}}")
        print(f"Secondary tables: {{strategy['secondary_tables']}}")
        print(f"Dominant intent: {{table_mapper.analyze_user_query(query)['query_analysis']['dominant_intent']}}")
'''
    
    with open('intelligent_table_mapper.py', 'w', encoding='utf-8') as f:
        f.write(python_code)
    
    print("✅ Python implementation saved to 'intelligent_table_mapper.py'")

if __name__ == "__main__":
    main()