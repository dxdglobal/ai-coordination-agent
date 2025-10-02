#!/usr/bin/env python3
"""
Check and update COORDINATION AGENT DXD AI in staff table
"""

import mysql.connector

# Database connection
db_config = {
    'host': '92.113.22.65',
    'user': 'u906714182_sqlrrefdvdv', 
    'password': '3@6*t:lU',
    'database': 'u906714182_sqlrrefdvdv'
}

def check_ai_agent_in_staff():
    """Check if AI agent exists in staff table"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        print("🤖 Checking COORDINATION AGENT DXD AI in staff table...")
        print("=" * 60)
        
        # Look for the AI agent
        cursor.execute("""
            SELECT * FROM tblstaff 
            WHERE staffid = 248 OR 
            firstname LIKE '%COORDINATION%' OR 
            firstname LIKE '%DXD%' OR
            firstname LIKE '%AI%'
        """)
        
        ai_agents = cursor.fetchall()
        
        if ai_agents:
            print(f"✅ Found {len(ai_agents)} AI agent entries:")
            for agent in ai_agents:
                print(f"   Staff ID: {agent['staffid']}")
                print(f"   Name: {agent['firstname']} {agent.get('lastname', '')}")
                print(f"   Email: {agent.get('email', 'N/A')}")
                print(f"   Active: {agent.get('active', 'N/A')}")
                print(f"   Is Admin: {agent.get('is_admin', 'N/A')}")
                print("   " + "-" * 40)
        else:
            print("❌ AI agent not found in staff table")
            
        # Check if we need to add or update the AI agent
        print("\n🔧 Checking if AI agent needs to be added/updated...")
        
        # Check specifically for staff ID 248
        cursor.execute("SELECT * FROM tblstaff WHERE staffid = 248")
        existing_agent = cursor.fetchone()
        
        if existing_agent:
            print("✅ AI Agent (ID: 248) exists!")
            print(f"   Current name: {existing_agent['firstname']} {existing_agent.get('lastname', '')}")
            
            # Check if name needs updating
            if existing_agent['firstname'] != 'COORDINATION AGENT DXD AI':
                print("🔄 Updating AI agent name...")
                cursor.execute("""
                    UPDATE tblstaff 
                    SET firstname = %s, lastname = %s, active = 1
                    WHERE staffid = 248
                """, ('COORDINATION AGENT DXD AI', ''))
                conn.commit()
                print("✅ AI agent name updated!")
            else:
                print("✅ AI agent name is already correct!")
                
        else:
            print("❌ AI Agent (ID: 248) doesn't exist. Adding it...")
            cursor.execute("""
                INSERT INTO tblstaff (staffid, firstname, lastname, email, active, is_admin)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (248, 'COORDINATION AGENT DXD AI', '', 'ai@dxdglobal.com', 1, 0))
            conn.commit()
            print("✅ AI agent added to staff table!")
            
        cursor.close()
        conn.close()
        
        print("\n🎯 Final verification...")
        return verify_ai_agent()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def verify_ai_agent():
    """Verify AI agent is properly set up"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM tblstaff WHERE staffid = 248")
        agent = cursor.fetchone()
        
        if agent:
            print("✅ COORDINATION AGENT DXD AI is ready!")
            print(f"   Staff ID: {agent['staffid']}")
            print(f"   Name: {agent['firstname']} {agent.get('lastname', '')}")
            print(f"   Email: {agent.get('email', 'N/A')}")
            print(f"   Active: {agent.get('active', 'N/A')}")
            print("   Ready to receive personal messages! 💬")
            return True
        else:
            print("❌ Verification failed - AI agent not found")
            return False
            
    except Exception as e:
        print(f"❌ Verification error: {e}")
        return False

if __name__ == "__main__":
    check_ai_agent_in_staff()