#!/usr/bin/env python3
"""
Mark COORDINATION AGENT DXD AI as Online/Green Status
Updates AI agent status to show as active and available
"""

import mysql.connector
from datetime import datetime

class AIStatusManager:
    def __init__(self):
        self.ai_staff_id = 248  # COORDINATION AGENT DXD AI staff ID
        self.ai_name = "COORDINATION AGENT DXD AI"
        
        # Database connection config
        self.db_config = {
            'host': '92.113.22.65',
            'user': 'u906714182_sqlrrefdvdv', 
            'password': '3@6*t:lU',
            'database': 'u906714182_sqlrrefdvdv'
        }
    
    def get_database_connection(self):
        """Get MySQL database connection"""
        try:
            return mysql.connector.connect(**self.db_config)
        except Exception as e:
            print(f"❌ Database connection error: {e}")
            return None
    
    def check_status_tables(self):
        """Check what status-related tables exist"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return
                
            cursor = connection.cursor()
            
            # Look for status-related tables
            status_tables = []
            
            cursor.execute("SHOW TABLES LIKE '%status%'")
            tables = cursor.fetchall()
            status_tables.extend([t[0] for t in tables])
            
            cursor.execute("SHOW TABLES LIKE '%online%'")
            tables = cursor.fetchall()
            status_tables.extend([t[0] for t in tables])
            
            cursor.execute("SHOW TABLES LIKE '%presence%'")
            tables = cursor.fetchall()
            status_tables.extend([t[0] for t in tables])
            
            cursor.execute("SHOW TABLES LIKE '%active%'")
            tables = cursor.fetchall()
            status_tables.extend([t[0] for t in tables])
            
            print(f"📋 Status-related tables found: {status_tables}")
            
            # Check if tblstaff has status columns
            cursor.execute("DESCRIBE tblstaff")
            columns = cursor.fetchall()
            
            print("🔍 tblstaff columns that might control online status:")
            for col in columns:
                col_name = col[0].lower()
                if any(word in col_name for word in ['status', 'online', 'active', 'last', 'login']):
                    print(f"   • {col[0]} ({col[1]}) - Default: {col[4]}")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"❌ Error checking status tables: {e}")
    
    def update_ai_status_to_online(self):
        """Update AI agent status to show as online/green"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            # Update the AI agent's status in tblstaff
            update_query = """
            UPDATE tblstaff 
            SET 
                active = 1,
                last_login = %s,
                last_activity = %s
            WHERE staffid = %s
            """
            
            current_time = datetime.now()
            
            cursor.execute(update_query, (current_time, current_time, self.ai_staff_id))
            
            # Check if there's a separate online status table
            try:
                # Try to create/update online status record
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS tbl_staff_online_status (
                        staff_id INT PRIMARY KEY,
                        is_online TINYINT DEFAULT 1,
                        last_seen DATETIME,
                        status_message VARCHAR(255),
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
                    )
                """)
                
                # Insert or update online status
                cursor.execute("""
                    INSERT INTO tbl_staff_online_status (staff_id, is_online, last_seen, status_message)
                    VALUES (%s, 1, %s, 'Online 24/7 - Ready to assist!')
                    ON DUPLICATE KEY UPDATE
                    is_online = 1,
                    last_seen = %s,
                    status_message = 'Online 24/7 - Ready to assist!',
                    updated_at = CURRENT_TIMESTAMP
                """, (self.ai_staff_id, current_time, current_time))
                
            except Exception as e:
                print(f"⚠️ Note: Could not update separate status table: {e}")
            
            connection.commit()
            
            cursor.close()
            connection.close()
            
            print("✅ AI agent status updated to ONLINE/GREEN!")
            return True
            
        except Exception as e:
            print(f"❌ Error updating AI status: {e}")
            return False
    
    def verify_ai_online_status(self):
        """Verify that AI agent shows as online"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return
                
            cursor = connection.cursor(dictionary=True)
            
            # Check AI agent status in tblstaff
            cursor.execute("""
                SELECT staffid, firstname, lastname, active, last_login, last_activity
                FROM tblstaff 
                WHERE staffid = %s
            """, (self.ai_staff_id,))
            
            ai_info = cursor.fetchone()
            
            if ai_info:
                print("🤖 COORDINATION AGENT DXD AI Status:")
                print(f"   Name: {ai_info['firstname']} {ai_info['lastname']}")
                print(f"   Staff ID: {ai_info['staffid']}")
                print(f"   Active: {'🟢 YES' if ai_info['active'] else '🔴 NO'}")
                print(f"   Last Login: {ai_info.get('last_login', 'N/A')}")
                print(f"   Last Activity: {ai_info.get('last_activity', 'N/A')}")
            
            # Check online status table if exists
            try:
                cursor.execute("""
                    SELECT * FROM tbl_staff_online_status 
                    WHERE staff_id = %s
                """, (self.ai_staff_id,))
                
                online_status = cursor.fetchone()
                if online_status:
                    print("📡 Online Status:")
                    print(f"   Is Online: {'🟢 YES' if online_status['is_online'] else '🔴 NO'}")
                    print(f"   Last Seen: {online_status['last_seen']}")
                    print(f"   Status Message: {online_status['status_message']}")
                    print(f"   Updated: {online_status['updated_at']}")
                
            except Exception:
                print("📡 No separate online status table found")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"❌ Error verifying status: {e}")

def main():
    """Mark AI agent as online/green and verify status"""
    print("🟢 AI AGENT ONLINE STATUS MANAGER")
    print("=" * 50)
    
    status_manager = AIStatusManager()
    
    # Check existing status structure
    print("🔍 Checking status table structure...")
    status_manager.check_status_tables()
    
    print("\n" + "=" * 50)
    
    # Update AI to online status
    print("🟢 Setting AI agent to ONLINE/GREEN status...")
    success = status_manager.update_ai_status_to_online()
    
    if success:
        print("\n" + "=" * 50)
        print("✅ Verifying AI agent online status...")
        status_manager.verify_ai_online_status()
        
        print("\n🎉 COORDINATION AGENT DXD AI is now ONLINE and GREEN!")
        print("💬 Staff should see the AI agent as available in chat!")
    else:
        print("❌ Failed to set AI agent online status")

if __name__ == "__main__":
    main()