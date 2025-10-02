#!/usr/bin/env python3
"""
Script to examine project comment/note table structures
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

# Check tblproject_notes structure
print('📋 Structure of tblproject_notes:')
cursor.execute('DESCRIBE tblproject_notes')
columns = cursor.fetchall()
for col in columns:
    print(f'  {col[0]} - {col[1]}')

print('\n📋 Structure of tblproject_activity:')
cursor.execute('DESCRIBE tblproject_activity')
columns = cursor.fetchall()
for col in columns:
    print(f'  {col[0]} - {col[1]}')

print('\n📋 Structure of comments:')
cursor.execute('DESCRIBE comments')
columns = cursor.fetchall()
for col in columns:
    print(f'  {col[0]} - {col[1]}')

# Check sample data from tblproject_notes
print('\n📝 Sample data from tblproject_notes:')
cursor.execute('SELECT * FROM tblproject_notes LIMIT 3')
sample_notes = cursor.fetchall()
if sample_notes:
    for note in sample_notes:
        print(f'  Note: {note}')
else:
    print('  No notes found in table')

connection.close()