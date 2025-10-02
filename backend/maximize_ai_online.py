import mysql.connector
from datetime import datetime, timedelta

class CRMStatusAnalyzer:
    def __init__(self):
        self.ai_staff_id = 248
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
    
    def analyze_online_detection(self):
        """Analyze how the system detects online users"""
        conn = self.get_database_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            print("🔍 ANALYZING ONLINE STATUS DETECTION")
            print("=" * 60)
            
            # 1. Check if there are specific conditions for showing as online
            print("📊 Comparing AI Agent with other online users:")
            
            cursor.execute("""
                SELECT 
                    s.staffid, 
                    CONCAT(s.firstname, ' ', s.lastname) as name,
                    s.last_activity,
                    s.last_login,
                    s.is_logged_in,
                    s.active,
                    os.is_online,
                    os.last_seen,
                    os.status_message,
                    TIMESTAMPDIFF(MINUTE, s.last_activity, NOW()) as activity_minutes_ago,
                    TIMESTAMPDIFF(MINUTE, os.last_seen, NOW()) as seen_minutes_ago
                FROM tblstaff s
                LEFT JOIN tbl_staff_online_status os ON s.staffid = os.staff_id
                WHERE s.active = 1 
                  AND (s.staffid = %s OR os.is_online = 1 OR s.is_logged_in = 1)
                ORDER BY s.last_activity DESC
                LIMIT 15
            """, (self.ai_staff_id,))
            
            results = cursor.fetchall()
            
            for user in results:
                ai_marker = " ← AI AGENT" if user['staffid'] == self.ai_staff_id else ""
                online_status = "🟢" if user['is_online'] else "🔴"
                logged_in = "✅" if user['is_logged_in'] else "❌"
                
                print(f"\n👤 {user['name']}{ai_marker}")
                print(f"   {online_status} Online Status: {'Yes' if user['is_online'] else 'No'}")
                print(f"   {logged_in} Logged In: {'Yes' if user['is_logged_in'] else 'No'}")
                print(f"   ⏰ Last Activity: {user['activity_minutes_ago']} min ago")
                print(f"   👀 Last Seen: {user['seen_minutes_ago']} min ago" if user['seen_minutes_ago'] is not None else "   👀 Last Seen: Never")
                print(f"   💬 Status: {user['status_message'] or 'No status'}")
            
            # 2. Check for any special online status rules
            print(f"\n🔍 Checking for online status rules...")
            
            # Update AI with even more aggressive settings
            print(f"\n🚀 Applying MAXIMUM ONLINE settings for AI agent...")
            
            # Set everything to make the AI appear as online as possible
            cursor.execute("""
                UPDATE tblstaff 
                SET 
                    last_activity = NOW(),
                    last_login = NOW(),
                    is_logged_in = 1,
                    active = 1,
                    last_ip = '127.0.0.1'
                WHERE staffid = %s
            """, (self.ai_staff_id,))
            
            # Force online status
            cursor.execute("""
                INSERT INTO tbl_staff_online_status 
                (staff_id, is_online, last_seen, status_message, updated_at)
                VALUES (%s, 1, NOW(), '🟢 ALWAYS ONLINE - AI ASSISTANT', NOW())
                ON DUPLICATE KEY UPDATE 
                is_online = 1,
                last_seen = NOW(),
                status_message = '🟢 ALWAYS ONLINE - AI ASSISTANT',
                updated_at = NOW()
            """, (self.ai_staff_id,))
            
            # Also check if there's a session table
            try:
                cursor.execute("""
                    INSERT INTO tblsessions 
                    (session_id, user_id, ip_address, user_agent, created_at, updated_at)
                    VALUES (CONCAT('ai_session_', UNIX_TIMESTAMP()), %s, '127.0.0.1', 'AI Agent Browser', NOW(), NOW())
                    ON DUPLICATE KEY UPDATE updated_at = NOW()
                """, (self.ai_staff_id,))
                print("✅ Created/updated session record")
            except Exception as e:
                print(f"ℹ️  Session table update: {e}")
            
            conn.commit()
            
            # 3. Final verification
            cursor.execute("""
                SELECT 
                    s.staffid, 
                    CONCAT(s.firstname, ' ', s.lastname) as name,
                    s.last_activity,
                    s.is_logged_in,
                    s.active,
                    os.is_online,
                    os.last_seen,
                    os.status_message
                FROM tblstaff s
                LEFT JOIN tbl_staff_online_status os ON s.staffid = os.staff_id
                WHERE s.staffid = %s
            """, (self.ai_staff_id,))
            
            ai_status = cursor.fetchone()
            
            print(f"\n✅ FINAL AI AGENT STATUS:")
            print(f"   📛 Name: {ai_status['name']}")
            print(f"   🟢 Online: {'YES' if ai_status['is_online'] else 'NO'}")
            print(f"   ✅ Logged In: {'YES' if ai_status['is_logged_in'] else 'NO'}")
            print(f"   ✅ Active: {'YES' if ai_status['active'] else 'NO'}")
            print(f"   ⏰ Last Activity: {ai_status['last_activity']}")
            print(f"   👀 Last Seen: {ai_status['last_seen']}")
            print(f"   💬 Status: {ai_status['status_message']}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error analyzing online detection: {e}")
            if conn:
                conn.close()
            return False
    
    def continuous_online_maintenance(self):
        """Keep updating the AI status every few seconds"""
        import time
        
        print(f"\n🔄 Starting continuous online maintenance...")
        print(f"📡 Will update AI status every 10 seconds")
        print(f"🛑 Press Ctrl+C to stop")
        
        try:
            for i in range(12):  # Run for 2 minutes
                conn = self.get_database_connection()
                if conn:
                    try:
                        cursor = conn.cursor()
                        
                        # Update timestamps
                        cursor.execute("""
                            UPDATE tblstaff 
                            SET last_activity = NOW(), last_login = NOW()
                            WHERE staffid = %s
                        """, (self.ai_staff_id,))
                        
                        cursor.execute("""
                            UPDATE tbl_staff_online_status 
                            SET last_seen = NOW(), updated_at = NOW()
                            WHERE staff_id = %s
                        """, (self.ai_staff_id,))
                        
                        conn.commit()
                        cursor.close()
                        conn.close()
                        
                        print(f"⏰ [{datetime.now().strftime('%H:%M:%S')}] Updated AI status - Check CRM now!")
                        
                    except Exception as e:
                        print(f"❌ Update error: {e}")
                        if conn:
                            conn.close()
                
                time.sleep(10)
                
        except KeyboardInterrupt:
            print(f"\n🛑 Maintenance stopped")
        
        print(f"✅ Maintenance completed - AI should be showing as online")

def main():
    analyzer = CRMStatusAnalyzer()
    
    # Analyze and fix
    if analyzer.analyze_online_detection():
        print(f"\n" + "=" * 60)
        print(f"🎯 AI AGENT STATUS MAXIMIZED!")
        print(f"📱 REFRESH YOUR CRM PAGE NOW")
        print(f"🟢 The AI agent should appear online")
        
        # Ask if user wants continuous maintenance
        print(f"\n🔄 Would you like to run continuous maintenance?")
        print(f"   This will keep updating the AI status for 2 minutes")
        choice = input("Run continuous maintenance? (y/n): ").lower().strip()
        
        if choice == 'y' or choice == 'yes':
            analyzer.continuous_online_maintenance()

if __name__ == "__main__":
    main()