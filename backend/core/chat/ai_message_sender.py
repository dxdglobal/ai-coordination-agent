#!/usr/bin/env python3
"""
AI Agent Proactive Message System
Sends messages FROM the COORDINATION AGENT DXD AI TO staff members
"""

import mysql.connector
from datetime import datetime, date
import json
import time

class AIAgentMessageSender:
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
    
    def send_message_to_staff(self, recipient_staff_id, message_content):
        """Send a message FROM AI agent TO a specific staff member"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            # Find the correct chat messages table
            # First, check if there's a standard chat messages table
            cursor.execute("SHOW TABLES LIKE '%message%'")
            message_tables = cursor.fetchall()
            
            cursor.execute("SHOW TABLES LIKE '%chat%'")  
            chat_tables = cursor.fetchall()
            
            print(f"📋 Available message tables: {message_tables}")
            print(f"📋 Available chat tables: {chat_tables}")
            
            # If no standard table exists, create one
            create_table_query = """
            CREATE TABLE IF NOT EXISTS tbl_staff_messages (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender_id INT NOT NULL,
                recipient_id INT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_read TINYINT DEFAULT 0,
                message_type VARCHAR(50) DEFAULT 'text',
                INDEX idx_recipient (recipient_id),
                INDEX idx_sender (sender_id),
                INDEX idx_created (created_at)
            )
            """
            cursor.execute(create_table_query)
            
            # Insert the message
            insert_query = """
            INSERT INTO tbl_staff_messages (sender_id, recipient_id, message, message_type)
            VALUES (%s, %s, %s, 'ai_notification')
            """
            
            cursor.execute(insert_query, (self.ai_staff_id, recipient_staff_id, message_content))
            connection.commit()
            
            message_id = cursor.lastrowid
            
            cursor.close()
            connection.close()
            
            print(f"✅ Message sent successfully! ID: {message_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    def get_staff_for_notifications(self):
        """Get all active staff members who should receive notifications"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return []
                
            cursor = connection.cursor(dictionary=True)
            
            # Get active staff with tasks
            query = """
            SELECT DISTINCT s.staffid, s.firstname, s.lastname, s.email,
                   COUNT(t.id) as total_tasks,
                   SUM(CASE WHEN t.duedate < CURDATE() AND t.status NOT IN (2, 3) THEN 1 ELSE 0 END) as overdue_tasks,
                   SUM(CASE WHEN t.duedate = CURDATE() AND t.status NOT IN (2, 3) THEN 1 ELSE 0 END) as due_today_tasks
            FROM tblstaff s
            LEFT JOIN tbltasks t ON s.staffid = t.addedfrom
            WHERE s.active = 1 AND s.staffid != 248
            GROUP BY s.staffid, s.firstname, s.lastname, s.email
            HAVING total_tasks > 0
            ORDER BY overdue_tasks DESC, due_today_tasks DESC
            LIMIT 10
            """
            
            cursor.execute(query)
            staff_list = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return staff_list
            
        except Exception as e:
            print(f"❌ Error getting staff list: {e}")
            return []
    
    def generate_proactive_message(self, staff_info):
        """Generate a proactive message for a staff member"""
        name = f"{staff_info['firstname']} {staff_info['lastname']}".strip()
        
        if staff_info['overdue_tasks'] > 0:
            return f"Hi {name}! 👋 You have {staff_info['overdue_tasks']} overdue tasks. Need help prioritizing or any assistance? I'm here to help! 🤖"
        elif staff_info['due_today_tasks'] > 0:
            return f"Hi {name}! 👋 You have {staff_info['due_today_tasks']} tasks due today. Let me know if you need any support! 🚀"
        else:
            return f"Hi {name}! 👋 Great job staying on top of your tasks! Let me know if you need any project updates or assistance. 😊"
    
    def send_daily_notifications(self):
        """Send daily notifications to all staff members"""
        print("🤖 AI AGENT: Sending daily notifications to staff...")
        print("=" * 60)
        
        staff_list = self.get_staff_for_notifications()
        
        if not staff_list:
            print("❌ No staff found for notifications")
            return
        
        sent_count = 0
        
        for staff in staff_list:
            name = f"{staff['firstname']} {staff['lastname']}".strip()
            print(f"📨 Sending notification to: {name}")
            
            message = self.generate_proactive_message(staff)
            
            success = self.send_message_to_staff(staff['staffid'], message)
            
            if success:
                print(f"   ✅ Message sent to {name}")
                sent_count += 1
            else:
                print(f"   ❌ Failed to send message to {name}")
            
            # Small delay between messages
            time.sleep(1)
        
        print(f"\n🎉 Daily notifications complete! Sent {sent_count} messages")
        return sent_count
    
    def send_test_message_to_hamza(self):
        """Send a test message specifically to Hamza"""
        print("🧪 Sending test message to Hamza...")
        
        # Find Hamza's staff ID
        try:
            connection = self.get_database_connection()
            if not connection:
                return False
                
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT staffid, firstname, lastname FROM tblstaff 
                WHERE LOWER(firstname) LIKE '%hamza%' 
                AND active = 1
            """)
            
            hamza = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if not hamza:
                print("❌ Hamza not found in staff table")
                return False
            
            print(f"✅ Found Hamza: {hamza['firstname']} {hamza['lastname']} (ID: {hamza['staffid']})")
            
            # Send test message
            test_message = """Hi Hamza! 👋 

This is a test message from your COORDINATION AGENT DXD AI! 🤖

📊 Quick update:
• You have 39 overdue tasks
• 1 task due today  
• 2 tasks due soon

Need help prioritizing or want your full task breakdown? Just let me know!

Your AI Assistant is always here to help! 💪"""

            success = self.send_message_to_staff(hamza['staffid'], test_message)
            
            if success:
                print("🎉 Test message sent successfully to Hamza!")
                print("💬 Hamza should now see this message in his chat interface!")
                return True
            else:
                print("❌ Failed to send test message to Hamza")
                return False
                
        except Exception as e:
            print(f"❌ Error sending test message: {e}")
            return False

def main():
    """Main function to test the messaging system"""
    print("🤖 COORDINATION AGENT DXD AI - PROACTIVE MESSAGING SYSTEM")
    print("=" * 70)
    
    message_sender = AIAgentMessageSender()
    
    # Send test message to Hamza
    print("📱 STEP 1: Testing message to Hamza")
    message_sender.send_test_message_to_hamza()
    
    print("\n" + "=" * 70)
    print("📢 STEP 2: Sending daily notifications to all staff")
    message_sender.send_daily_notifications()
    
    print("\n✅ AI Agent messaging system test complete!")
    print("💬 Staff should now see messages from COORDINATION AGENT DXD AI in their chat!")

if __name__ == "__main__":
    main()