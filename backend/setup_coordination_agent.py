#!/usr/bin/env python3
"""
Find or create COORDINATION AGENT DXD AI staff entry
"""

import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

def get_database_connection():
    """Get database connection"""
    try:
        connection = mysql.connector.connect(
            host='92.113.22.65',
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database='u906714182_sqlrrefdvdv'
        )
        return connection
    except mysql.connector.Error as e:
        print(f"❌ Database connection error: {e}")
        return None

def find_coordination_agent():
    """Find if COORDINATION AGENT DXD AI exists in staff table"""
    connection = get_database_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Look for coordination agent or AI related entries
        search_patterns = ['%coordination%', '%agent%', '%AI%', '%DXD%']
        
        for pattern in search_patterns:
            cursor.execute("""
                SELECT staffid, firstname, lastname, email 
                FROM tblstaff 
                WHERE CONCAT(firstname, ' ', lastname) LIKE %s
                OR email LIKE %s
            """, (pattern, pattern))
            
            results = cursor.fetchall()
            if results:
                print(f"🔍 Found staff matching '{pattern}':")
                for staff in results:
                    print(f"  - ID: {staff['staffid']}, Name: {staff['firstname']} {staff['lastname']}, Email: {staff['email']}")
                return results[0]['staffid']
        
        return None
        
    except mysql.connector.Error as e:
        print(f"❌ Error searching: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def create_coordination_agent():
    """Create COORDINATION AGENT DXD AI staff entry if it doesn't exist"""
    connection = get_database_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor()
        
        # Insert coordination agent as staff
        cursor.execute("""
            INSERT INTO tblstaff (
                email, firstname, lastname, datecreated, admin, role, active,
                is_not_staff, password
            ) VALUES (
                'coordination.agent@dxdglobal.com',
                'COORDINATION AGENT',
                'DXD AI',
                NOW(),
                0,
                1,
                1,
                1,
                'system_agent'
            )
        """)
        
        connection.commit()
        agent_id = cursor.lastrowid
        
        print(f"✅ Created COORDINATION AGENT DXD AI with ID: {agent_id}")
        return agent_id
        
    except mysql.connector.Error as e:
        print(f"❌ Error creating agent: {e}")
        return None
    finally:
        cursor.close()
        connection.close()

def add_comments_as_coordination_agent():
    """Add comments as COORDINATION AGENT DXD AI"""
    # First find or create coordination agent
    agent_id = find_coordination_agent()
    
    if not agent_id:
        print("🤖 Creating COORDINATION AGENT DXD AI staff entry...")
        agent_id = create_coordination_agent()
    
    if not agent_id:
        print("❌ Could not find or create coordination agent")
        return
    
    print(f"🤖 Using COORDINATION AGENT DXD AI (Staff ID: {agent_id})")
    
    # Now add comments with the correct staff ID
    connection = get_database_connection()
    if not connection:
        return
    
    try:
        cursor = connection.cursor()
        
        # Update existing comments to be from coordination agent instead of staff 1
        cursor.execute("""
            UPDATE tbltask_comments 
            SET staffid = %s
            WHERE content LIKE '%testing%' 
            AND staffid = 1
            AND DATE(dateadded) = CURDATE()
        """, (agent_id,))
        
        updated_count = cursor.rowcount
        connection.commit()
        
        print(f"✅ Updated {updated_count} comments to be from COORDINATION AGENT DXD AI")
        
        # Verify the update
        cursor.execute("""
            SELECT COUNT(*) as count
            FROM tbltask_comments tc
            JOIN tblstaff s ON tc.staffid = s.staffid
            WHERE tc.content LIKE '%testing%'
            AND s.firstname = 'COORDINATION AGENT'
            AND DATE(tc.dateadded) = CURDATE()
        """)
        
        verification = cursor.fetchone()
        print(f"🔍 Verified: {verification[0]} comments now from COORDINATION AGENT DXD AI")
        
    except mysql.connector.Error as e:
        print(f"❌ Error updating comments: {e}")
    finally:
        cursor.close()
        connection.close()

if __name__ == "__main__":
    print("🤖 SETTING UP COORDINATION AGENT DXD AI...")
    add_comments_as_coordination_agent()