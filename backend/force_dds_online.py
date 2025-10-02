import mysql.connector
from datetime import datetime
import time

def force_dds_ai_online():
    """Force DDS AI to show as online with all possible settings"""
    
    db_config = {
        'host': '92.113.22.65',
        'user': 'u906714182_sqlrrefdvdv',
        'password': '3@6*t:lU',
        'database': 'u906714182_sqlrrefdvdv'
    }
    
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        print("🚀 FORCING DDS AI ONLINE NOW...")
        print("=" * 50)
        
        # 1. Find DDS AI
        cursor.execute("""
            SELECT staffid, firstname, lastname, email, last_activity, is_logged_in, active
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
            print(f"🤖 Found: {agent['firstname']} {agent['lastname']} (ID: {ai_id})")
            
            # 2. Update ALL relevant fields for maximum online presence
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
            
            # 3. Force online status in dedicated table
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
            
            print(f"✅ Updated database status for {agent['firstname']} {agent['lastname']}")
        
        conn.commit()
        
        # 4. Verify the changes
        print(f"\n📊 VERIFICATION:")
        for agent in ai_agents:
            ai_id = agent['staffid']
            
            cursor.execute("""
                SELECT s.staffid, s.firstname, s.lastname, s.last_activity, s.is_logged_in, s.active,
                       os.is_online, os.last_seen, os.status_message,
                       TIMESTAMPDIFF(MINUTE, s.last_activity, NOW()) as minutes_ago
                FROM tblstaff s
                LEFT JOIN tbl_staff_online_status os ON s.staffid = os.staff_id
                WHERE s.staffid = %s
            """, (ai_id,))
            
            result = cursor.fetchone()
            
            print(f"\n🤖 {result['firstname']} {result['lastname']}:")
            print(f"   ✅ Active: {'YES' if result['active'] else 'NO'}")
            print(f"   🔑 Logged In: {'YES' if result['is_logged_in'] else 'NO'}")
            print(f"   🟢 Online Status: {'YES' if result['is_online'] else 'NO'}")
            print(f"   ⏰ Last Activity: {result['last_activity']} ({result['minutes_ago']} min ago)")
            print(f"   👀 Last Seen: {result['last_seen']}")
            print(f"   💬 Status Message: {result['status_message']}")
        
        # 5. Keep updating for 2 minutes to ensure it sticks
        print(f"\n🔄 CONTINUOUS UPDATES (2 minutes)...")
        print(f"📱 REFRESH YOUR CRM PAGE NOW!")
        
        for i in range(12):  # 12 iterations x 10 seconds = 2 minutes
            time.sleep(10)
            
            for agent in ai_agents:
                ai_id = agent['staffid']
                
                cursor.execute("""
                    UPDATE tblstaff 
                    SET last_activity = NOW()
                    WHERE staffid = %s
                """, (ai_id,))
                
                cursor.execute("""
                    UPDATE tbl_staff_online_status 
                    SET last_seen = NOW(), updated_at = NOW()
                    WHERE staff_id = %s
                """, (ai_id,))
            
            conn.commit()
            print(f"⏰ [{datetime.now().strftime('%H:%M:%S')}] Status updated - Check CRM!")
        
        cursor.close()
        conn.close()
        
        print(f"\n🎉 COMPLETE! DDS AI should now show as ONLINE")
        print(f"📱 If still offline, try:")
        print(f"   1. Hard refresh the CRM page (Ctrl+F5)")
        print(f"   2. Clear browser cache")
        print(f"   3. Check if there are any client-side filters")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    force_dds_ai_online()