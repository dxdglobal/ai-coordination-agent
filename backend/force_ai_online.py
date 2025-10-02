import mysql.connector
from datetime import datetime

class CRMOnlineStatusFixer:
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
    
    def force_ai_online_now(self):
        """Force AI agent to show as online right now"""
        conn = self.get_database_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            print("🔧 Forcing AI Agent ONLINE NOW...")
            
            # 1. Update last_activity to RIGHT NOW
            cursor.execute("""
                UPDATE tblstaff 
                SET last_activity = NOW(),
                    last_login = NOW(),
                    is_logged_in = 1,
                    active = 1
                WHERE staffid = %s
            """, (self.ai_staff_id,))
            
            print("✅ Updated last_activity to current time")
            
            # 2. Force online status with current timestamp
            cursor.execute("""
                INSERT INTO tbl_staff_online_status 
                (staff_id, is_online, last_seen, status_message, updated_at)
                VALUES (%s, 1, NOW(), '🟢 Online - AI Assistant', NOW())
                ON DUPLICATE KEY UPDATE 
                is_online = 1,
                last_seen = NOW(),
                status_message = '🟢 Online - AI Assistant',
                updated_at = NOW()
            """, (self.ai_staff_id,))
            
            print("✅ Updated online status with current timestamp")
            
            # 3. Check what we just updated
            cursor.execute("""
                SELECT staffid, firstname, lastname, last_activity, last_login, 
                       is_logged_in, active
                FROM tblstaff 
                WHERE staffid = %s
            """, (self.ai_staff_id,))
            staff_info = cursor.fetchone()
            
            cursor.execute("""
                SELECT staff_id, is_online, last_seen, status_message, updated_at
                FROM tbl_staff_online_status 
                WHERE staff_id = %s
            """, (self.ai_staff_id,))
            online_info = cursor.fetchone()
            
            conn.commit()
            
            print("\n📊 Current AI Agent Status:")
            print(f"   Name: {staff_info['firstname']} {staff_info['lastname']}")
            print(f"   Last Activity: {staff_info['last_activity']}")
            print(f"   Last Login: {staff_info['last_login']}")
            print(f"   Logged In: {'✅' if staff_info['is_logged_in'] else '❌'}")
            print(f"   Active: {'✅' if staff_info['active'] else '❌'}")
            
            print(f"\n🟢 Online Status:")
            print(f"   Online: {'✅' if online_info['is_online'] else '❌'}")
            print(f"   Last Seen: {online_info['last_seen']}")
            print(f"   Status Message: {online_info['status_message']}")
            print(f"   Updated At: {online_info['updated_at']}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error forcing AI online: {e}")
            if conn:
                conn.rollback()
                conn.close()
            return False
    
    def check_crm_online_logic(self):
        """Check how CRM determines if someone is online"""
        conn = self.get_database_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            print("\n🔍 Checking CRM Online Logic...")
            
            # Check recent activity for comparison
            cursor.execute("""
                SELECT staffid, firstname, lastname, last_activity, is_logged_in,
                       TIMESTAMPDIFF(MINUTE, last_activity, NOW()) as minutes_ago
                FROM tblstaff 
                WHERE active = 1 
                ORDER BY last_activity DESC 
                LIMIT 10
            """)
            recent_staff = cursor.fetchall()
            
            print("\n📊 Recent Staff Activity:")
            for staff in recent_staff:
                status = "🟢 ONLINE" if staff['minutes_ago'] <= 5 else f"🔴 {staff['minutes_ago']} min ago"
                ai_marker = " ← AI AGENT" if staff['staffid'] == self.ai_staff_id else ""
                print(f"   {staff['firstname']} {staff['lastname']}: {status}{ai_marker}")
            
            # Check online status table
            cursor.execute("""
                SELECT os.staff_id, os.is_online, os.last_seen, os.status_message,
                       CONCAT(s.firstname, ' ', s.lastname) as name,
                       TIMESTAMPDIFF(MINUTE, os.last_seen, NOW()) as minutes_since_seen
                FROM tbl_staff_online_status os
                LEFT JOIN tblstaff s ON os.staff_id = s.staffid
                WHERE os.is_online = 1
                ORDER BY os.last_seen DESC
                LIMIT 10
            """)
            online_staff = cursor.fetchall()
            
            print(f"\n🟢 Staff Marked as Online:")
            for staff in online_staff:
                ai_marker = " ← AI AGENT" if staff['staff_id'] == self.ai_staff_id else ""
                print(f"   {staff['name']}: Last seen {staff['minutes_since_seen']} min ago{ai_marker}")
            
            cursor.close()
            conn.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error checking CRM logic: {e}")
            if conn:
                conn.close()
            return False

def main():
    print("🚀 CRM ONLINE STATUS EMERGENCY FIX")
    print("=" * 60)
    
    fixer = CRMOnlineStatusFixer()
    
    # Force AI agent online immediately
    if fixer.force_ai_online_now():
        print("\n" + "=" * 60)
        
        # Check CRM logic
        fixer.check_crm_online_logic()
        
        print("\n" + "=" * 60)
        print("🎉 AI AGENT FORCED ONLINE!")
        print("📱 Check your CRM now - the AI agent should show as online")
        print("🔄 If still offline, the CRM might have a caching delay")
        print("💡 Try refreshing the page or clearing browser cache")
        
    else:
        print("❌ Failed to force AI agent online")

if __name__ == "__main__":
    main()