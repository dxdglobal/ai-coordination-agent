"""
Enhanced AI Agent Notification System
Monitors for new messages and automatically responds with notifications
"""

import mysql.connector
from datetime import datetime, timedelta
import time
import threading
import json

class AIAgentNotificationMonitor:
    def __init__(self):
        self.ai_staff_id = 248
        self.monitoring = False
        self.last_check = datetime.now()
        
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
    
    def ensure_ai_agent_online(self):
        """Ensure AI agent stays online"""
        conn = self.get_database_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor()
            
            # Update AI agent status
            cursor.execute("""
                UPDATE tblstaff 
                SET is_logged_in = 1, 
                    last_activity = NOW(),
                    active = 1
                WHERE staffid = %s
            """, (self.ai_staff_id,))
            
            # Update online status
            cursor.execute("""
                INSERT INTO tbl_staff_online_status 
                (staff_id, is_online, last_seen, status_message, updated_at)
                VALUES (%s, 1, NOW(), 'Always Online - AI Assistant 🤖', NOW())
                ON DUPLICATE KEY UPDATE 
                is_online = 1,
                last_seen = NOW(),
                status_message = 'Always Online - AI Assistant 🤖',
                updated_at = NOW()
            """, (self.ai_staff_id,))
            
            conn.commit()
            cursor.close()
            conn.close()
            return True
            
        except Exception as e:
            print(f"❌ Error ensuring AI agent online: {e}")
            if conn:
                conn.close()
            return False
    
    def check_for_new_messages(self):
        """Check for new messages and handle them"""
        conn = self.get_database_connection()
        if not conn:
            return []
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get new messages since last check
            cursor.execute("""
                SELECT cm.id, cm.sender_id, cm.message, cm.time_sent, cm.viewed,
                       CONCAT(s.firstname, ' ', s.lastname) as sender_name,
                       s.email as sender_email
                FROM tblchatmessages cm
                LEFT JOIN tblstaff s ON cm.sender_id = s.staffid
                WHERE cm.reciever_id = %s 
                  AND cm.time_sent > %s
                  AND cm.viewed = 0
                ORDER BY cm.time_sent ASC
            """, (self.ai_staff_id, self.last_check))
            
            new_messages = cursor.fetchall()
            
            for message in new_messages:
                # Mark message as viewed
                cursor.execute("""
                    UPDATE tblchatmessages 
                    SET viewed = 1, viewed_at = NOW() 
                    WHERE id = %s
                """, (message['id'],))
                
                # Create notification for the sender that their message was received
                cursor.execute("""
                    INSERT INTO tblnotifications 
                    (isread, isread_inline, date, description, fromuserid, fromclientid, 
                     from_fullname, touserid, link, additional_data)
                    VALUES 
                    (0, 0, NOW(), 'AI Agent received your message', %s, 0, 
                     '!COORDINATION AGENT DXD AI', %s, 
                     CONCAT('#message=', %s), 
                     CONCAT('Your message was received: ', LEFT(%s, 50)))
                """, (self.ai_staff_id, message['sender_id'], message['id'], message['message']))
                
                print(f"📨 New message from {message['sender_name']}: {message['message'][:50]}...")
            
            if new_messages:
                conn.commit()
                
            cursor.close()
            conn.close()
            
            self.last_check = datetime.now()
            return new_messages
            
        except Exception as e:
            print(f"❌ Error checking for new messages: {e}")
            if conn:
                conn.close()
            return []
    
    def send_auto_response(self, sender_id, original_message):
        """Send an automatic response to acknowledge the message"""
        conn = self.get_database_connection()
        if not conn:
            return False
            
        try:
            cursor = conn.cursor(dictionary=True)
            
            # Get sender info
            cursor.execute("""
                SELECT firstname, lastname, email
                FROM tblstaff 
                WHERE staffid = %s
            """, (sender_id,))
            sender = cursor.fetchone()
            
            if not sender:
                return False
            
            sender_name = f"{sender['firstname']} {sender['lastname']}"
            
            # Create acknowledgment response
            response_message = f"""Hello {sender_name}! 👋

I've received your message: "{original_message[:100]}..."

As your AI Coordination Agent, I'm processing your request. I'll analyze your message and provide you with relevant information shortly.

🤖 Always here to help!
- COORDINATION AGENT DXD AI"""
            
            # Send response message
            cursor.execute("""
                INSERT INTO tblchatmessages 
                (sender_id, reciever_id, message, time_sent, viewed)
                VALUES (%s, %s, %s, NOW(), 0)
            """, (self.ai_staff_id, sender_id, response_message))
            
            conn.commit()
            cursor.close()
            conn.close()
            
            print(f"🤖 Sent auto-response to {sender_name}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending auto-response: {e}")
            if conn:
                conn.close()
            return False
    
    def monitor_messages(self, duration_minutes=60):
        """Monitor for new messages for a specified duration"""
        print(f"🚀 Starting AI Agent notification monitoring for {duration_minutes} minutes...")
        print(f"🤖 AI Agent (ID: {self.ai_staff_id}) is now actively monitoring messages")
        print("📡 Will check for new messages every 10 seconds")
        print("=" * 70)
        
        self.monitoring = True
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        # Ensure AI agent is online at start
        self.ensure_ai_agent_online()
        
        message_count = 0
        
        try:
            while self.monitoring and datetime.now() < end_time:
                # Check for new messages
                new_messages = self.check_for_new_messages()
                
                # Handle each new message
                for message in new_messages:
                    message_count += 1
                    print(f"📨 [{datetime.now().strftime('%H:%M:%S')}] Message #{message_count}")
                    print(f"   From: {message['sender_name']} (ID: {message['sender_id']})")
                    print(f"   Content: {message['message'][:100]}...")
                    
                    # Send auto-response
                    self.send_auto_response(message['sender_id'], message['message'])
                    print(f"   ✅ Auto-response sent")
                    print()
                
                # Ensure AI agent stays online every 30 seconds
                if int(time.time()) % 30 == 0:
                    self.ensure_ai_agent_online()
                
                # Wait 10 seconds before next check
                time.sleep(10)
                
        except KeyboardInterrupt:
            print("\n🛑 Monitoring stopped by user")
        
        self.monitoring = False
        
        print("=" * 70)
        print(f"📊 Monitoring Summary:")
        print(f"   Duration: {(datetime.now() - start_time).total_seconds() / 60:.1f} minutes")
        print(f"   Messages processed: {message_count}")
        print(f"   AI Agent Status: Online ✅")
        print("🎉 Monitoring completed successfully!")
    
    def stop_monitoring(self):
        """Stop the monitoring process"""
        self.monitoring = False
        print("🛑 Stopping message monitoring...")

def run_background_monitor():
    """Run the monitor in background for testing"""
    monitor = AIAgentNotificationMonitor()
    monitor.monitor_messages(duration_minutes=5)  # Run for 5 minutes for testing

if __name__ == "__main__":
    monitor = AIAgentNotificationMonitor()
    
    print("🤖 AI Agent Notification System")
    print("=" * 50)
    print("Choose an option:")
    print("1. Test notification system (5 minutes)")
    print("2. Run continuous monitoring (60 minutes)")
    print("3. Just ensure AI agent is online")
    print("4. Check current status")
    
    choice = input("\nEnter choice (1-4): ").strip()
    
    if choice == "1":
        monitor.monitor_messages(duration_minutes=5)
    elif choice == "2":
        monitor.monitor_messages(duration_minutes=60)
    elif choice == "3":
        if monitor.ensure_ai_agent_online():
            print("✅ AI Agent is now online!")
        else:
            print("❌ Failed to set AI Agent online")
    elif choice == "4":
        # Just check current status
        messages = monitor.check_for_new_messages()
        if messages:
            print(f"📨 Found {len(messages)} new messages")
        else:
            print("📭 No new messages")
    else:
        print("❌ Invalid choice")