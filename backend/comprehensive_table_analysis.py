import mysql.connector
from datetime import datetime

class CRMTableAnalyzer:
    def __init__(self):
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
    
    def find_all_chat_and_online_tables(self):
        """Find all tables related to chat and online status"""
        conn = self.get_database_connection()
        if not conn:
            return
            
        try:
            cursor = conn.cursor()
            
            print("🔍 SEARCHING ALL CHAT AND ONLINE RELATED TABLES...")
            print("=" * 70)
            
            # Get all table names
            cursor.execute("SHOW TABLES")
            all_tables = [table[0] for table in cursor.fetchall()]
            
            # Filter for relevant tables
            chat_keywords = ['chat', 'message', 'online', 'status', 'session', 'activity', 'login', 'staff']
            relevant_tables = []
            
            for table in all_tables:
                for keyword in chat_keywords:
                    if keyword.lower() in table.lower():
                        relevant_tables.append(table)
                        break
            
            print(f"📋 Found {len(relevant_tables)} relevant tables:")
            for table in sorted(relevant_tables):
                print(f"   • {table}")
            
            return relevant_tables
            
        except Exception as e:
            print(f"❌ Error finding tables: {e}")
            return []
        finally:
            if conn:
                conn.close()
    
    def analyze_table_structure_and_data(self, table_name):
        """Analyze a specific table's structure and sample data"""
        conn = self.get_database_connection()
        if not conn:
            return
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            print(f"\n📊 ANALYZING TABLE: {table_name}")
            print("-" * 50)
            
            # Get table structure
            cursor.execute(f"DESCRIBE {table_name}")
            structure = cursor.fetchall()
            
            print("🏗️  Table Structure:")
            for field in structure:
                key_info = f" ({field['Key']})" if field['Key'] else ""
                null_info = "NOT NULL" if field['Null'] == 'NO' else "NULL"
                print(f"   {field['Field']}: {field['Type']} {null_info}{key_info}")
            
            # Get sample data (limit to avoid overwhelming output)
            try:
                cursor.execute(f"SELECT * FROM {table_name} LIMIT 5")
                sample_data = cursor.fetchall()
                
                if sample_data:
                    print(f"\n📝 Sample Data (first 5 rows):")
                    for i, row in enumerate(sample_data, 1):
                        print(f"   Row {i}: {dict(row)}")
                else:
                    print(f"\n📝 No data in table")
                    
            except Exception as e:
                print(f"   ⚠️  Could not fetch sample data: {e}")
            
            # If it's a staff-related table, check for DDS AI
            if 'staff' in table_name.lower():
                try:
                    cursor.execute(f"""
                        SELECT * FROM {table_name} 
                        WHERE (firstname LIKE '%DDS%' OR lastname LIKE '%DDS%' OR firstname LIKE '%AI%')
                           OR staffid = 248
                        LIMIT 3
                    """)
                    dds_data = cursor.fetchall()
                    
                    if dds_data:
                        print(f"\n🤖 DDS AI data in {table_name}:")
                        for row in dds_data:
                            print(f"   {dict(row)}")
                except Exception as e:
                    print(f"   ⚠️  Could not search for DDS AI: {e}")
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error analyzing {table_name}: {e}")
            if conn:
                conn.close()
    
    def find_dds_ai_in_all_tables(self):
        """Find DDS AI entries across all relevant tables"""
        conn = self.get_database_connection()
        if not conn:
            return
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            print("\n🔍 SEARCHING FOR DDS AI ACROSS ALL TABLES...")
            print("=" * 70)
            
            # Check main staff table first
            cursor.execute("""
                SELECT staffid, firstname, lastname, email, last_activity, 
                       is_logged_in, active, last_login, last_ip
                FROM tblstaff 
                WHERE (firstname LIKE '%DDS%' OR lastname LIKE '%DDS%' OR firstname LIKE '%AI%')
                   OR staffid = 248
            """)
            staff_data = cursor.fetchall()
            
            if staff_data:
                print("🤖 DDS AI in tblstaff:")
                for staff in staff_data:
                    ai_id = staff['staffid']
                    print(f"   ID: {ai_id}")
                    print(f"   Name: {staff['firstname']} {staff['lastname']}")
                    print(f"   Email: {staff['email']}")
                    print(f"   Last Activity: {staff['last_activity']}")
                    print(f"   Logged In: {staff['is_logged_in']}")
                    print(f"   Active: {staff['active']}")
                    print(f"   Last Login: {staff['last_login']}")
                    print(f"   Last IP: {staff['last_ip']}")
                    
                    # Check online status table
                    cursor.execute("""
                        SELECT * FROM tbl_staff_online_status 
                        WHERE staff_id = %s
                    """, (ai_id,))
                    online_status = cursor.fetchone()
                    
                    if online_status:
                        print(f"   🟢 Online Status: {online_status}")
                    else:
                        print(f"   ❌ No online status record")
                    
                    # Check chat messages
                    cursor.execute("""
                        SELECT COUNT(*) as total_sent, MAX(time_sent) as last_sent
                        FROM tblchatmessages 
                        WHERE sender_id = %s
                    """, (ai_id,))
                    sent_stats = cursor.fetchone()
                    
                    cursor.execute("""
                        SELECT COUNT(*) as total_received, MAX(time_sent) as last_received
                        FROM tblchatmessages 
                        WHERE reciever_id = %s
                    """, (ai_id,))
                    received_stats = cursor.fetchone()
                    
                    print(f"   📤 Messages Sent: {sent_stats['total_sent']} (Last: {sent_stats['last_sent']})")
                    print(f"   📥 Messages Received: {received_stats['total_received']} (Last: {received_stats['last_received']})")
                    print("-" * 50)
            
            cursor.close()
            conn.close()
            
        except Exception as e:
            print(f"❌ Error finding DDS AI: {e}")
            if conn:
                conn.close()
    
    def fix_all_dds_ai_status(self):
        """Fix DDS AI status in ALL relevant tables"""
        conn = self.get_database_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            print("\n🔧 FIXING DDS AI STATUS IN ALL TABLES...")
            print("=" * 70)
            
            # Find DDS AI first
            cursor.execute("""
                SELECT staffid, firstname, lastname
                FROM tblstaff 
                WHERE (firstname LIKE '%DDS%' OR lastname LIKE '%DDS%' OR firstname LIKE '%AI%')
                   OR staffid = 248
            """)
            ai_agents = cursor.fetchall()
            
            if not ai_agents:
                print("❌ DDS AI not found!")
                return False
            
            for agent in ai_agents:
                ai_id = agent['staffid']
                ai_name = f"{agent['firstname']} {agent['lastname']}"
                
                print(f"🤖 Fixing status for: {ai_name} (ID: {ai_id})")
                
                # 1. Update tblstaff
                cursor.execute("""
                    UPDATE tblstaff 
                    SET 
                        last_activity = NOW(),
                        last_login = NOW(),
                        is_logged_in = 1,
                        active = 1,
                        last_ip = '127.0.0.1'
                    WHERE staffid = %s
                """, (ai_id,))
                print("   ✅ Updated tblstaff")
                
                # 2. Update/Insert online status
                cursor.execute("""
                    INSERT INTO tbl_staff_online_status 
                    (staff_id, is_online, last_seen, status_message, updated_at)
                    VALUES (%s, 1, NOW(), '🟢 ONLINE - AI ASSISTANT', NOW())
                    ON DUPLICATE KEY UPDATE 
                    is_online = 1,
                    last_seen = NOW(),
                    status_message = '🟢 ONLINE - AI ASSISTANT',
                    updated_at = NOW()
                """, (ai_id,))
                print("   ✅ Updated tbl_staff_online_status")
                
                # 3. Check if there's a sessions table and create/update session
                try:
                    cursor.execute("""
                        INSERT INTO tblsessions 
                        (session_id, user_id, ip_address, user_agent, created_at, updated_at)
                        VALUES (CONCAT('ai_session_', UNIX_TIMESTAMP(), '_', %s), %s, '127.0.0.1', 'AI Agent Always Online', NOW(), NOW())
                        ON DUPLICATE KEY UPDATE updated_at = NOW()
                    """, (ai_id, ai_id))
                    print("   ✅ Updated/Created session")
                except Exception as e:
                    print(f"   ⚠️  Session update: {e}")
                
                # 4. Send a "heartbeat" message to show activity
                try:
                    cursor.execute("""
                        INSERT INTO tblchatmessages 
                        (sender_id, reciever_id, message, time_sent, viewed)
                        VALUES (%s, 1, '🤖 AI Agent is now ONLINE and ready to assist!', NOW(), 0)
                    """, (ai_id,))
                    print("   ✅ Sent activity message")
                except Exception as e:
                    print(f"   ⚠️  Message send: {e}")
                
                # 5. Update any activity logs
                try:
                    cursor.execute("""
                        INSERT INTO tblactivity_log 
                        (staffid, description, date, additional_data)
                        VALUES (%s, 'AI Agent came online', NOW(), 'Automated status update')
                    """, (ai_id,))
                    print("   ✅ Updated activity log")
                except Exception as e:
                    print(f"   ⚠️  Activity log: {e}")
            
            conn.commit()
            
            # 6. Verify the changes
            print(f"\n📊 VERIFICATION:")
            for agent in ai_agents:
                ai_id = agent['staffid']
                
                cursor.execute("""
                    SELECT s.staffid, s.firstname, s.lastname, s.last_activity, s.is_logged_in, s.active,
                           os.is_online, os.last_seen, os.status_message,
                           TIMESTAMPDIFF(SECOND, s.last_activity, NOW()) as seconds_ago
                    FROM tblstaff s
                    LEFT JOIN tbl_staff_online_status os ON s.staffid = os.staff_id
                    WHERE s.staffid = %s
                """, (ai_id,))
                
                result = cursor.fetchone()
                
                print(f"\n🤖 {result['firstname']} {result['lastname']}:")
                print(f"   ✅ Active: {'YES' if result['active'] else 'NO'}")
                print(f"   🔑 Logged In: {'YES' if result['is_logged_in'] else 'NO'}")
                print(f"   🟢 Online Status: {'YES' if result['is_online'] else 'NO'}")
                print(f"   ⏰ Last Activity: {result['last_activity']} ({result['seconds_ago']} seconds ago)")
                print(f"   💬 Status Message: {result['status_message']}")
            
            cursor.close()
            conn.close()
            
            print(f"\n🎉 ALL STATUS UPDATES COMPLETE!")
            print(f"📱 REFRESH YOUR CRM PAGE NOW!")
            print(f"🔄 If still not showing as online, there might be:")
            print(f"   • Browser cache issues")
            print(f"   • Client-side JavaScript filtering")
            print(f"   • Different online detection logic")
            
            return True
            
        except Exception as e:
            print(f"❌ Error fixing status: {e}")
            if conn:
                conn.close()
            return False

def main():
    analyzer = CRMTableAnalyzer()
    
    print("🚀 COMPREHENSIVE CRM TABLE ANALYSIS AND FIX")
    print("=" * 70)
    
    # 1. Find all relevant tables
    relevant_tables = analyzer.find_all_chat_and_online_tables()
    
    # 2. Analyze key tables
    key_tables = ['tblstaff', 'tbl_staff_online_status', 'tblchatmessages', 'tblsessions', 'tblactivity_log']
    
    for table in key_tables:
        if table in relevant_tables:
            analyzer.analyze_table_structure_and_data(table)
    
    # 3. Find DDS AI across all tables
    analyzer.find_dds_ai_in_all_tables()
    
    # 4. Fix all status issues
    analyzer.fix_all_dds_ai_status()

if __name__ == "__main__":
    main()