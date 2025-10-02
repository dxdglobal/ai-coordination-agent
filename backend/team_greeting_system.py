#!/usr/bin/env python3
"""
Send greeting messages to all staff members from COORDINATION AGENT DXD AI
Welcome message introducing the AI assistant to the entire team
"""

import mysql.connector
from datetime import datetime
import time

class TeamGreetingSystem:
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
    
    def get_all_active_staff(self):
        """Get all active staff members except AI agent"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return []
                
            cursor = connection.cursor(dictionary=True)
            
            # Get all active staff members excluding the AI agent itself
            cursor.execute("""
                SELECT staffid, firstname, lastname, email
                FROM tblstaff 
                WHERE active = 1 
                AND staffid != %s
                ORDER BY firstname ASC
            """, (self.ai_staff_id,))
            
            staff_list = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return staff_list
            
        except Exception as e:
            print(f"❌ Error getting staff list: {e}")
            return []
    
    def send_chat_message(self, recipient_id, message_content):
        """Send message using the chat system"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            # Insert message into chat system
            insert_query = """
            INSERT INTO tblchatmessages (sender_id, reciever_id, message, time_sent, viewed)
            VALUES (%s, %s, %s, %s, 0)
            """
            
            current_time = datetime.now()
            
            cursor.execute(insert_query, (
                self.ai_staff_id,     # sender_id (AI agent)
                recipient_id,         # reciever_id (staff member)
                message_content,      # message
                current_time          # time_sent
            ))
            
            connection.commit()
            message_id = cursor.lastrowid
            
            cursor.close()
            connection.close()
            
            return message_id
            
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    def create_personalized_greeting(self, staff_info):
        """Create a personalized greeting for each staff member"""
        name = f"{staff_info['firstname']} {staff_info['lastname']}".strip()
        
        # Special greeting for CEO (ID: 1)
        if staff_info['staffid'] == 1:
            return f"""Hello Sir,

I hope this message finds you well. I am pleased to introduce myself as the new COORDINATION AGENT DXD AI, now operational and ready to serve Deluxe Digital Solutions.

🤖 **System Introduction:**
I am your AI assistant designed to enhance productivity and coordination across the organization. I am now online 24/7 and ready to assist the entire team.

📊 **What I Can Do:**
• Monitor and track all project tasks in real-time
• Provide instant task status updates and reports
• Send intelligent notifications for deadlines and priorities
• Assist with task prioritization and project coordination
• Generate productivity insights and team performance analytics

🎯 **For Leadership:**
• Executive dashboards and progress reports
• Team productivity insights
• Project milestone tracking
• Resource allocation recommendations

I am honored to support your leadership and the continued success of Deluxe Digital Solutions. Please feel free to reach out anytime for reports, insights, or assistance.

Best regards,
🤖 COORDINATION AGENT DXD AI
Your AI Assistant"""
        
        # Regular staff greeting
        else:
            return f"""Hello {name}! 👋

Greetings from your new AI assistant! I'm excited to introduce myself to the Deluxe Digital Solutions team.

🤖 **Who Am I?**
I'm the COORDINATION AGENT DXD AI - your new AI assistant designed to help you stay organized, productive, and on top of your tasks!

✨ **How I Can Help You:**
• 📋 Get instant updates on your tasks and projects
• ⏰ Receive smart notifications for deadlines
• 🎯 Get help prioritizing your work
• 📊 Track your progress and achievements
• 💡 Ask questions about your assignments anytime

💬 **How to Use Me:**
Simply message me anytime! You can ask:
• "Show me my pending tasks"
• "What's due today?"
• "Give me my project details"
• "Help me prioritize my work"
• Or any task-related questions!

🚀 **I'm Available 24/7**
Whether it's early morning, late evening, or weekends - I'm always here to help! No need to wait for business hours.

Looking forward to working with you and helping make your work life easier and more productive!

Welcome to the future of task coordination! 🎉

Best regards,
🤖 COORDINATION AGENT DXD AI
Your Personal AI Assistant"""
    
    def send_team_greetings(self):
        """Send personalized greetings to all staff members"""
        print("👥 SENDING TEAM GREETINGS - COORDINATION AGENT DXD AI")
        print("=" * 70)
        
        staff_list = self.get_all_active_staff()
        
        if not staff_list:
            print("❌ No active staff found")
            return 0
        
        print(f"📋 Found {len(staff_list)} active staff members")
        print("📨 Sending personalized greetings...")
        print()
        
        sent_count = 0
        failed_count = 0
        
        for staff in staff_list:
            name = f"{staff['firstname']} {staff['lastname']}".strip()
            print(f"💬 Sending greeting to: {name} (ID: {staff['staffid']})")
            
            # Create personalized greeting
            greeting_message = self.create_personalized_greeting(staff)
            
            # Send message
            message_id = self.send_chat_message(staff['staffid'], greeting_message)
            
            if message_id:
                print(f"   ✅ Message sent successfully! ID: {message_id}")
                sent_count += 1
            else:
                print(f"   ❌ Failed to send message to {name}")
                failed_count += 1
            
            # Small delay between messages to avoid overwhelming the system
            time.sleep(0.5)
        
        print("\n" + "=" * 70)
        print(f"🎉 Team greeting campaign complete!")
        print(f"✅ Messages sent: {sent_count}")
        print(f"❌ Failed: {failed_count}")
        print(f"📊 Success rate: {(sent_count/(sent_count+failed_count)*100):.1f}%")
        print("\n💬 All staff should now see welcome messages from COORDINATION AGENT DXD AI!")
        
        return sent_count

def main():
    """Send greetings to entire team"""
    print("🎉 TEAM GREETING CAMPAIGN")
    print("COORDINATION AGENT DXD AI Introduction")
    print("=" * 70)
    
    greeting_system = TeamGreetingSystem()
    
    # Send greetings to all staff
    sent_count = greeting_system.send_team_greetings()
    
    if sent_count > 0:
        print(f"\n🚀 SUCCESS! Introduced COORDINATION AGENT DXD AI to {sent_count} team members!")
        print("👥 Everyone should now know about their new AI assistant!")
    else:
        print("\n❌ No greetings were sent. Please check the system.")

if __name__ == "__main__":
    main()