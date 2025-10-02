#!/usr/bin/env python3
"""
Staff List Priority System - Move COORDINATION AGENT DXD AI to Top
Ensures AI agent appears at the top of the staff list with online status
"""

import mysql.connector
from datetime import datetime

class StaffListPriorityManager:
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
    
    def check_staff_ordering_system(self):
        """Check how staff list is ordered and what controls priority"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return
                
            cursor = connection.cursor(dictionary=True)
            
            # Check tblstaff structure for ordering fields
            cursor.execute("DESCRIBE tblstaff")
            columns = cursor.fetchall()
            
            print("🔍 Checking staff table columns for priority/ordering:")
            ordering_columns = []
            for col in columns:
                col_name = col['Field'].lower()
                if any(word in col_name for word in ['order', 'priority', 'sort', 'position', 'rank', 'level']):
                    ordering_columns.append(col['Field'])
                    print(f"   • {col['Field']} ({col['Type']}) - {col['Default']}")
            
            if not ordering_columns:
                print("   ⚠️ No specific ordering columns found - using standard approach")
            
            # Check current staff list order
            cursor.execute("""
                SELECT staffid, firstname, lastname, active, last_activity
                FROM tblstaff 
                WHERE active = 1 
                ORDER BY firstname ASC
                LIMIT 10
            """)
            
            current_order = cursor.fetchall()
            print(f"\n📋 Current staff list order (first 10):")
            for i, staff in enumerate(current_order, 1):
                name = f"{staff['firstname']} {staff['lastname']}".strip()
                ai_indicator = "🤖 AI AGENT" if staff['staffid'] == self.ai_staff_id else ""
                print(f"   {i}. {name} (ID: {staff['staffid']}) {ai_indicator}")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"❌ Error checking staff ordering: {e}")
    
    def set_ai_agent_priority(self):
        """Set AI agent to appear at top of staff list"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            # Strategy 1: Use firstname to force alphabetical top position
            print("🔧 Strategy 1: Setting firstname to force top position...")
            
            cursor.execute("""
                UPDATE tblstaff 
                SET firstname = %s,
                    lastname = %s,
                    active = 1,
                    last_activity = %s,
                    last_login = %s
                WHERE staffid = %s
            """, (
                "!COORDINATION AGENT DXD AI",  # ! forces it to top alphabetically
                "",
                datetime.now(),
                datetime.now(),
                self.ai_staff_id
            ))
            
            # Strategy 2: Add priority column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE tblstaff ADD COLUMN priority INT DEFAULT 100")
                print("✅ Added priority column to tblstaff")
            except Exception as e:
                if "Duplicate column name" not in str(e):
                    print(f"⚠️ Could not add priority column: {e}")
            
            # Set highest priority for AI agent
            try:
                cursor.execute("""
                    UPDATE tblstaff 
                    SET priority = 1 
                    WHERE staffid = %s
                """, (self.ai_staff_id,))
                print("✅ Set AI agent priority to 1 (highest)")
            except Exception as e:
                print(f"⚠️ Could not set priority: {e}")
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print("✅ AI agent priority settings updated!")
            return True
            
        except Exception as e:
            print(f"❌ Error setting AI priority: {e}")
            return False
    
    def ensure_online_status(self):
        """Ensure AI agent has strong online presence"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            # Update all online status indicators
            current_time = datetime.now()
            
            # Update main staff record
            cursor.execute("""
                UPDATE tblstaff 
                SET 
                    active = 1,
                    last_login = %s,
                    last_activity = %s,
                    status_work = 'Online 24/7 - AI Assistant Ready'
                WHERE staffid = %s
            """, (current_time, current_time, self.ai_staff_id))
            
            # Update online status table
            cursor.execute("""
                INSERT INTO tbl_staff_online_status (staff_id, is_online, last_seen, status_message)
                VALUES (%s, 1, %s, 'Always Online - AI Assistant')
                ON DUPLICATE KEY UPDATE
                is_online = 1,
                last_seen = %s,
                status_message = 'Always Online - AI Assistant',
                updated_at = CURRENT_TIMESTAMP
            """, (self.ai_staff_id, current_time, current_time))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            print("✅ AI agent online status strengthened!")
            return True
            
        except Exception as e:
            print(f"❌ Error updating online status: {e}")
            return False
    
    def verify_top_position(self):
        """Verify AI agent appears at top of staff list"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return
                
            cursor = connection.cursor(dictionary=True)
            
            # Check multiple ordering scenarios
            ordering_queries = [
                ("Alphabetical by firstname", "ORDER BY firstname ASC"),
                ("By priority (if exists)", "ORDER BY COALESCE(priority, 999), firstname ASC"),
                ("By last_activity desc", "ORDER BY last_activity DESC"),
                ("By active status + name", "ORDER BY active DESC, firstname ASC")
            ]
            
            for name, order_clause in ordering_queries:
                print(f"\n📊 {name}:")
                
                query = f"""
                    SELECT staffid, firstname, lastname, active, last_activity, 
                           COALESCE(priority, 999) as priority
                    FROM tblstaff 
                    WHERE active = 1 
                    {order_clause}
                    LIMIT 5
                """
                
                cursor.execute(query)
                results = cursor.fetchall()
                
                for i, staff in enumerate(results, 1):
                    name_display = f"{staff['firstname']} {staff['lastname']}".strip()
                    ai_indicator = " 🤖⭐ AI AGENT" if staff['staffid'] == self.ai_staff_id else ""
                    online_indicator = "🟢" if staff['active'] else "🔴"
                    priority_info = f" (Priority: {staff['priority']})" if 'priority' in staff else ""
                    
                    print(f"   {i}. {online_indicator} {name_display}{ai_indicator}{priority_info}")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"❌ Error verifying position: {e}")

def main():
    """Set AI agent to appear at top of staff list with online indicator"""
    print("⬆️ STAFF LIST PRIORITY MANAGER")
    print("Moving COORDINATION AGENT DXD AI to Top Position")
    print("=" * 60)
    
    priority_manager = StaffListPriorityManager()
    
    # Check current ordering system
    print("🔍 Analyzing current staff list ordering...")
    priority_manager.check_staff_ordering_system()
    
    print("\n" + "=" * 60)
    
    # Set AI agent priority
    print("⬆️ Setting AI agent to top position...")
    success1 = priority_manager.set_ai_agent_priority()
    
    # Ensure strong online presence
    print("\n🟢 Strengthening online status...")
    success2 = priority_manager.ensure_online_status()
    
    print("\n" + "=" * 60)
    
    # Verify results
    if success1 and success2:
        print("✅ Verifying AI agent position in staff list...")
        priority_manager.verify_top_position()
        
        print(f"\n🎉 SUCCESS! COORDINATION AGENT DXD AI should now appear:")
        print("   ⬆️ At the TOP of the staff list")
        print("   🟢 With GREEN online indicator")
        print("   ⭐ Marked as AI Assistant")
        print("   📱 Always available status")
        
        print("\n💬 Staff should now see AI agent prominently at the top!")
    else:
        print("❌ Some priority settings failed. Please check manually.")

if __name__ == "__main__":
    main()