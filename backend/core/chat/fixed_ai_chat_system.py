#!/usr/bin/env python3
"""
Fixed AI Agent Chat Response System
Uses correct column names: sender_id, reciever_id, message, time_sent
"""

import mysql.connector
from datetime import datetime

class FixedAIChatSystem:
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
    
    def send_chat_message(self, recipient_id, message_content):
        """Send message using correct column names"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            # Correct INSERT query with proper column names
            insert_query = """
            INSERT INTO tblchatmessages (sender_id, reciever_id, message, time_sent, viewed)
            VALUES (%s, %s, %s, %s, 0)
            """
            
            current_time = datetime.now()
            
            cursor.execute(insert_query, (
                self.ai_staff_id,     # sender_id (AI agent)
                recipient_id,         # reciever_id (recipient)
                message_content,      # message
                current_time          # time_sent
            ))
            
            connection.commit()
            message_id = cursor.lastrowid
            
            cursor.close()
            connection.close()
            
            print(f"✅ Message sent successfully! ID: {message_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    def respond_to_hamza_hello(self):
        """Respond to Hamza's "hello" message"""
        print("💬 I see Hamza sent 'hello' to the AI agent!")
        print("🤖 Sending response from COORDINATION AGENT DXD AI...")
        
        response_message = """Hi Hamza! 👋

Great to hear from you! I'm your COORDINATION AGENT DXD AI, ready to help! 🤖

📊 Quick Update on Your Tasks:
• Total Tasks: 52
• 🚨 Overdue: 39 tasks (needs attention!)
• ⏰ Due Today: 1 task
• 📅 Due Soon: 2 tasks

🎯 Top Priority Tasks:
• Task #1915: Resolving Build Issue for windows (DUE TODAY!)
• Task #1882: Fixing s3 issue and migration (DUE TODAY!)
• Task #1640: DDSFocusPro v1.2 (109 days overdue)

Need help with any of these? Want your full task breakdown? Just ask! 

I'm here 24/7 to help you stay organized and productive! 💪

- Your AI Assistant"""

        # Send to Hamza (ID: 188)
        success = self.send_chat_message(188, response_message)
        
        if success:
            print("🎉 Response sent to Hamza!")
            print("💬 Hamza should now see a detailed response in the chat!")
            return True
        else:
            print("❌ Failed to send response")
            return False
    
    def send_proactive_message_to_hamza(self):
        """Send a proactive message to Hamza"""
        print("📨 Sending proactive task update to Hamza...")
        
        proactive_message = """🚨 Daily Task Update - COORDINATION AGENT DXD AI

Hi Hamza! Your AI assistant here with your daily task summary:

⚠️ URGENT - Action Needed Today:
• Task #1915: Resolving Build Issue for windows
  📅 Status: DUE TODAY - High Priority!
  🔧 Suggestion: Start with this to unblock other work

• Task #1882: Fixing s3 issue and migration  
  📅 Status: DUE TODAY - Critical Infrastructure
  💡 Tip: This affects data flow - prioritize after build issue

📈 Weekly Focus Areas:
• DDSFocusPro v1.2 (109 days overdue) - Major milestone
• DDSFocusPro v1.1 (106 days overdue) - Foundation work
• DDSFocusPro v1.3 (96 days overdue) - Feature completion

💪 You've got this! Break tasks into smaller steps if needed.
Need detailed breakdown or want to discuss priorities? Just reply!

🤖 Always here to help - Your COORDINATION AGENT DXD AI"""

        success = self.send_chat_message(188, proactive_message)
        
        if success:
            print("🎉 Proactive message sent to Hamza!")
            return True
        else:
            print("❌ Failed to send proactive message")
            return False
    
    def check_messages_from_staff(self):
        """Check for any messages sent TO the AI agent"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return
                
            cursor = connection.cursor(dictionary=True)
            
            # Get messages sent TO the AI agent (receiver_id = 248)
            cursor.execute("""
                SELECT m.*, s.firstname, s.lastname 
                FROM tblchatmessages m
                LEFT JOIN tblstaff s ON m.sender_id = s.staffid
                WHERE m.reciever_id = 248
                ORDER BY m.time_sent DESC
                LIMIT 10
            """)
            
            messages = cursor.fetchall()
            
            print("📥 Recent messages TO AI agent:")
            for msg in messages:
                sender_name = f"{msg['firstname']} {msg['lastname']}"
                print(f"   • From {sender_name}: '{msg['message']}' at {msg['time_sent']}")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"❌ Error checking messages: {e}")

def main():
    """Main function to handle AI chat responses"""
    print("🤖 FIXED AI CHAT RESPONSE SYSTEM")
    print("=" * 60)
    
    chat_system = FixedAIChatSystem()
    
    # Check incoming messages
    print("📥 Checking messages sent to AI agent...")
    chat_system.check_messages_from_staff()
    
    print("\n" + "=" * 60)
    
    # Respond to Hamza's hello
    print("💬 Responding to Hamza's message...")
    chat_system.respond_to_hamza_hello()
    
    print("\n" + "=" * 60)
    
    # Send proactive message
    print("📨 Sending proactive task update...")
    chat_system.send_proactive_message_to_hamza()
    
    print("\n✅ AI Chat System is now active!")
    print("💬 Hamza should see responses in the chat interface!")

if __name__ == "__main__":
    main()