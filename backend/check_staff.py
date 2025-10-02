#!/usr/bin/env python3
import mysql.connector
conn = mysql.connector.connect(host='92.113.22.65', user='u906714182_sqlrrefdvdv', password='3@6*t:lU', database='u906714182_sqlrrefdvdv')
cursor = conn.cursor()
cursor.execute('SHOW TABLES LIKE "%staff%"')
tables = cursor.fetchall()
print('Staff tables:', tables)
if tables:
    cursor.execute(f'DESCRIBE {tables[0][0]}')
    columns = cursor.fetchall()
    print('Staff table columns:')
    for col in columns[:10]:
        print(f'  - {col[0]} ({col[1]})')
conn.close()