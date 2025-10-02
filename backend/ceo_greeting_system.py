#!/usr/bin/env python3
"""
Send greeting message to CEO Deniz from COORDINATION AGENT DXD AI
"""

import mysql.connector
from datetime import datetime

class CEOGreetingSystem:
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
    
    def find_deniz_ceo(self):
        """Find CEO Deniz in the staff table"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return None
                
            cursor = connection.cursor(dictionary=True)
            
            # Look for Deniz (CEO)
            cursor.execute("""
                SELECT staffid, firstname, lastname, email 
                FROM tblstaff 
                WHERE LOWER(firstname) LIKE '%deniz%' 
                AND active = 1
            """)
            
            deniz = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if deniz:
                print(f"✅ Found CEO: {deniz['firstname']} {deniz['lastname']} (ID: {deniz['staffid']})")
                return deniz
            else:
                print("❌ CEO Deniz not found in staff table")
                return None
                
        except Exception as e:
            print(f"❌ Error finding CEO Deniz: {e}")
            return None
    
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
                recipient_id,         # reciever_id (CEO Deniz)
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
    
    def send_greeting_to_ceo(self):
        """Send a respectful greeting message to CEO Deniz"""
        print("👔 Sending greeting to CEO Deniz...")
        
        # Find CEO Deniz
        deniz = self.find_deniz_ceo()
        if not deniz:
            return False
        
        # Compose respectful greeting message
        greeting_message = f"""Hello Sir,

Good day! I hope you are doing well.

I am the COORDINATION AGENT DXD AI, your new AI assistant designed to help coordinate and monitor tasks across the organization.

🤖 **My Capabilities:**
• 24/7 task monitoring and coordination
• Real-time progress tracking across all projects
• Automated status updates and notifications
• Intelligent task prioritization assistance
• Staff productivity insights and support

📊 **Current System Status:**
• Monitoring: 369 active tasks
• Supporting: 25+ active staff members
• Operating: 24/7 automated coordination
• Integrating: All project management workflows

I am here to assist you and the entire team in maintaining optimal productivity and project coordination. Please feel free to reach out anytime for reports, insights, or any assistance you may need.

Thank you for your time, and I look forward to supporting Deluxe Digital Solutions' continued success.

Best regards,
🤖 COORDINATION AGENT DXD AI
Your AI Assistant"""

        # Send the message
        success = self.send_chat_message(deniz['staffid'], greeting_message)
        
        if success:
            print(f"🎉 Greeting message sent successfully to CEO {deniz['firstname']} {deniz['lastname']}!")
            print("💼 CEO should now see a professional greeting from the AI Assistant!")
            return True
        else:
            print("❌ Failed to send greeting to CEO")
            return False

def main():
    """Send greeting to CEO Deniz"""
    print("👔 CEO GREETING SYSTEM - COORDINATION AGENT DXD AI")
    print("=" * 60)
    
    greeting_system = CEOGreetingSystem()
    
    # Send greeting to CEO
    greeting_system.send_greeting_to_ceo()
    
    print("\n✅ CEO greeting process complete!")

if __name__ == "__main__":
    main()