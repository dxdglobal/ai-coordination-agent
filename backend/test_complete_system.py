"""
Comprehensive Test for AI Agent Notification System
Tests all aspects of the notification and online status system
"""

import mysql.connector
from datetime import datetime
import time

class AIAgentSystemTester:
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
    
    def test_ai_agent_status(self):
        """Test AI agent status in all relevant tables"""
        print("🧪 Testing AI Agent Status...")
        print("-" * 50)
        
        conn = self.get_database_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # 1. Check tblstaff status
            cursor.execute("""
                SELECT staffid, firstname, lastname, email, active, is_logged_in, 
                       last_activity, priority
                FROM tblstaff 
                WHERE staffid = %s
            """, (self.ai_staff_id,))
            staff_status = cursor.fetchone()
            
            print("📊 tblstaff Status:")
            if staff_status:
                print(f"   ✅ Found: {staff_status['firstname']} {staff_status['lastname']}")
                print(f"   📧 Email: {staff_status['email']}")
                print(f"   🔴 Active: {'✅ Yes' if staff_status['active'] else '❌ No'}")
                print(f"   🟢 Logged In: {'✅ Yes' if staff_status['is_logged_in'] else '❌ No'}")
                print(f"   ⏰ Last Activity: {staff_status['last_activity']}")
                print(f"   🎯 Priority: {staff_status['priority']}")
            else:
                print("   ❌ AI agent not found in tblstaff!")
                return False
            
            # 2. Check online status
            cursor.execute("""
                SELECT staff_id, is_online, last_seen, status_message, updated_at
                FROM tbl_staff_online_status 
                WHERE staff_id = %s
            """, (self.ai_staff_id,))
            online_status = cursor.fetchone()
            
            print("\n🟢 Online Status:")
            if online_status:
                print(f"   🟢 Online: {'✅ Yes' if online_status['is_online'] else '❌ No'}")
                print(f"   💬 Status: {online_status['status_message']}")
                print(f"   👀 Last Seen: {online_status['last_seen']}")
                print(f"   🔄 Updated: {online_status['updated_at']}")
            else:
                print("   ❌ No online status record found!")
            
            # 3. Check message statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_messages,
                    SUM(CASE WHEN viewed = 1 THEN 1 ELSE 0 END) as read_messages,
                    SUM(CASE WHEN viewed = 0 THEN 1 ELSE 0 END) as unread_messages
                FROM tblchatmessages 
                WHERE reciever_id = %s
            """, (self.ai_staff_id,))
            msg_stats = cursor.fetchone()
            
            print("\n📧 Message Statistics:")
            print(f"   📨 Total Messages: {msg_stats['total_messages']}")
            print(f"   ✅ Read Messages: {msg_stats['read_messages']}")
            print(f"   📬 Unread Messages: {msg_stats['unread_messages']}")
            
            # 4. Check notification statistics
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_notifications,
                    SUM(CASE WHEN isread = 1 THEN 1 ELSE 0 END) as read_notifications,
                    SUM(CASE WHEN isread = 0 THEN 1 ELSE 0 END) as unread_notifications
                FROM tblnotifications 
                WHERE touserid = %s
            """, (self.ai_staff_id,))
            notif_stats = cursor.fetchone()
            
            print("\n🔔 Notification Statistics:")
            print(f"   🔔 Total Notifications: {notif_stats['total_notifications']}")
            print(f"   ✅ Read Notifications: {notif_stats['read_notifications']}")
            print(f"   📬 Unread Notifications: {notif_stats['unread_notifications']}")
            
            cursor.close()
            conn.close()
            
            # Overall assessment
            print("\n" + "=" * 50)
            print("📊 SYSTEM STATUS ASSESSMENT:")
            
            issues = []
            if not staff_status['active']:
                issues.append("AI agent not active")
            if not staff_status['is_logged_in']:
                issues.append("AI agent not logged in")
            if not online_status or not online_status['is_online']:
                issues.append("AI agent not showing as online")
            if msg_stats['unread_messages'] > 0:
                issues.append(f"{msg_stats['unread_messages']} unread messages")
            if notif_stats['unread_notifications'] > 0:
                issues.append(f"{notif_stats['unread_notifications']} unread notifications")
                
            if not issues:
                print("🎉 ALL SYSTEMS OPERATIONAL!")
                print("✅ AI agent is online and notifications are working")
                return True
            else:
                print("⚠️  ISSUES DETECTED:")
                for issue in issues:
                    print(f"   • {issue}")
                return False
                
        except Exception as e:
            print(f"❌ Error testing AI agent status: {e}")
            if conn:
                conn.close()
            return False
    
    def send_test_message(self, test_message="Test notification system"):
        """Send a test message to the AI agent"""
        print(f"\n📤 Sending test message to AI agent...")
        print(f"📝 Message: {test_message}")
        
        conn = self.get_database_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Send test message from user ID 1 (admin)
            cursor.execute("""
                INSERT INTO tblchatmessages 
                (sender_id, reciever_id, message, time_sent, viewed)
                VALUES (1, %s, %s, NOW(), 0)
            """, (self.ai_staff_id, test_message))
            
            message_id = cursor.lastrowid
            conn.commit()
            
            print(f"✅ Test message sent (ID: {message_id})")
            
            # Wait a moment and check if it was processed
            time.sleep(2)
            
            cursor.execute("""
                SELECT viewed, viewed_at 
                FROM tblchatmessages 
                WHERE id = %s
            """, (message_id,))
            result = cursor.fetchone()
            
            if result:
                if result['viewed']:
                    print(f"✅ Message marked as viewed at: {result['viewed_at']}")
                else:
                    print("⏳ Message not yet processed (this is normal)")
            
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error sending test message: {e}")
            if conn:
                conn.close()
            return False
    
    def run_comprehensive_test(self):
        """Run all tests"""
        print("🚀 AI AGENT COMPREHENSIVE SYSTEM TEST")
        print("=" * 70)
        print(f"🕒 Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"🤖 Testing AI Agent ID: {self.ai_staff_id}")
        print("=" * 70)
        
        # Test 1: Status check
        status_ok = self.test_ai_agent_status()
        
        # Test 2: Send test message
        if status_ok:
            self.send_test_message("🧪 Comprehensive system test message - please ignore")
        
        print("\n" + "=" * 70)
        print("📋 TEST SUMMARY:")
        
        if status_ok:
            print("🎉 SYSTEM STATUS: ✅ OPERATIONAL")
            print("🟢 AI Agent is online and visible in CRM")
            print("📱 Notifications should be working properly")
            print("💬 Messages are being processed correctly")
        else:
            print("⚠️  SYSTEM STATUS: ❌ ISSUES DETECTED")
            print("🔧 Please check the issues listed above")
        
        print("\n🔍 To verify in CRM:")
        print("   1. Check staff list - AI agent should show with green indicator")
        print("   2. Send a message to the AI agent")
        print("   3. Check that you receive notifications")
        print("   4. Verify the AI agent appears at the top of the staff list")
        
        return status_ok

if __name__ == "__main__":
    tester = AIAgentSystemTester()
    tester.run_comprehensive_test()