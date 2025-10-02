#!/usr/bin/env python3
"""Direct database query to show employees list"""

import mysql.connector
import os
from dotenv import load_dotenv

def show_employees_from_db():
    print("👥 EMPLOYEES LIST FROM DATABASE")
    print("================================")
    
    # Load environment variables
    load_dotenv()
    
    try:
        # Connect to database
        conn = mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME'),
            charset='utf8mb4',
            collation='utf8mb4_unicode_ci'
        )
        
        cursor = conn.cursor(dictionary=True)
        print("✅ Database connection successful!")
        
        # Query tblstaff for employees
        print("\n📊 STAFF TABLE (tblstaff):")
        print("-" * 40)
        cursor.execute("SELECT staffid, firstname, lastname, email, active FROM tblstaff WHERE active = 1 LIMIT 10")
        staff_results = cursor.fetchall()
        
        if staff_results:
            for i, employee in enumerate(staff_results, 1):
                name = f"{employee.get('firstname', '')} {employee.get('lastname', '')}".strip()
                email = employee.get('email', 'No email')
                staff_id = employee.get('staffid', 'N/A')
                print(f"{i}. ID: {staff_id} | {name} | {email}")
        else:
            print("No active staff found")
        
        # Query employees table
        print("\n📊 EMPLOYEES TABLE:")
        print("-" * 40)
        try:
            cursor.execute("SELECT id, name, email, department, position FROM employees WHERE is_active = 1 LIMIT 10")
            emp_results = cursor.fetchall()
            
            if emp_results:
                for i, employee in enumerate(emp_results, 1):
                    name = employee.get('name', 'No name')
                    email = employee.get('email', 'No email')
                    dept = employee.get('department', 'No dept')
                    position = employee.get('position', 'No position')
                    emp_id = employee.get('id', 'N/A')
                    print(f"{i}. ID: {emp_id} | {name} | {email} | {dept} ({position})")
            else:
                print("No active employees found in employees table")
        except Exception as e:
            print(f"Employees table error: {e}")
        
        print(f"\n✅ Total Staff Records Found: {len(staff_results)}")
        
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"❌ Database error: {e}")

if __name__ == "__main__":
    show_employees_from_db()