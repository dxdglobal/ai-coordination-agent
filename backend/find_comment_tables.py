#!/usr/bin/env python3
"""
Script to find comment/note tables in the CRM database
"""
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

connection = mysql.connector.connect(
    host=os.getenv('DB_HOST'),
    user=os.getenv('DB_USER'),
    password=os.getenv('DB_PASSWORD'),
    database=os.getenv('DB_NAME')
)

cursor = connection.cursor()

print('🔍 Looking for comment tables...')
cursor.execute("SHOW TABLES LIKE '%comment%'")
comment_tables = cursor.fetchall()
print('Comment tables found:')
for table in comment_tables:
    print(f'  - {table[0]}')

print('\n🔍 Looking for note tables...')
cursor.execute("SHOW TABLES LIKE '%note%'")
note_tables = cursor.fetchall()
print('Note tables found:')
for table in note_tables:
    print(f'  - {table[0]}')
    
print('\n🔍 Looking for activity tables...')
cursor.execute("SHOW TABLES LIKE '%activity%'")
activity_tables = cursor.fetchall()
print('Activity tables found:')
for table in activity_tables:
    print(f'  - {table[0]}')

# Also check for general project-related tables
print('\n🔍 All tables containing "project"...')
cursor.execute("SHOW TABLES LIKE '%project%'")
project_tables = cursor.fetchall()
print('Project-related tables:')
for table in project_tables:
    print(f'  - {table[0]}')

connection.close()