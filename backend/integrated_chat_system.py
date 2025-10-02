#!/usr/bin/env python3
"""
Integrated AI Agent Chat System
Sends messages through the existing tblchatmessages system
"""

import mysql.connector
from datetime import datetime
import time

class IntegratedAIChatSystem:
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
    
    def analyze_chat_table_structure(self):
        """Analyze the existing chat table structure"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return
                
            cursor = connection.cursor(dictionary=True)
            
            # Check structure of tblchatmessages
            print("📋 Analyzing tblchatmessages structure...")
            cursor.execute("DESCRIBE tblchatmessages")
            columns = cursor.fetchall()
            
            print("🔍 tblchatmessages columns:")
            for col in columns:
                print(f"   • {col['Field']} ({col['Type']}) - {col['Null']} - {col['Default']}")
            
            # Sample existing messages
            print("\n📨 Sample existing messages:")
            cursor.execute("SELECT * FROM tblchatmessages ORDER BY id DESC LIMIT 3")
            messages = cursor.fetchall()
            
            for msg in messages:
                print(f"   Message ID {msg['id']}: {str(msg)[:100]}...")
            
            cursor.close()
            connection.close()
            
        except Exception as e:
            print(f"❌ Error analyzing chat structure: {e}")
    
    def send_chat_message_to_staff(self, recipient_staff_id, message_content):
        """Send message through the existing tblchatmessages system"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return False
                
            cursor = connection.cursor()
            
            # Insert message into the existing chat system
            # Note: We'll need to determine the correct column names from the analysis
            insert_query = """
            INSERT INTO tblchatmessages (sender, receiver, message, date_sent, is_read)
            VALUES (%s, %s, %s, %s, 0)
            """
            
            current_time = datetime.now()
            
            cursor.execute(insert_query, (
                self.ai_staff_id,           # sender (AI agent)
                recipient_staff_id,         # receiver (staff member)
                message_content,            # message content
                current_time               # timestamp
            ))
            
            connection.commit()
            message_id = cursor.lastrowid
            
            cursor.close()
            connection.close()
            
            print(f"✅ Chat message sent! ID: {message_id}")
            return True
            
        except Exception as e:
            print(f"❌ Error sending chat message: {e}")
            print("🔧 Let me analyze the table structure first...")
            self.analyze_chat_table_structure()
            return False
    
    def send_integrated_test_message(self):
        """Send test message through the integrated chat system"""
        print("🧪 Testing integrated chat message system...")
        
        # Find Hamza
        try:
            connection = self.get_database_connection()
            if not connection:
                return
                
            cursor = connection.cursor(dictionary=True)
            
            cursor.execute("""
                SELECT staffid, firstname, lastname FROM tblstaff 
                WHERE LOWER(firstname) LIKE '%hamza%' 
                AND active = 1
            """)
            
            hamza = cursor.fetchone()
            cursor.close()
            connection.close()
            
            if hamza:
                test_message = f"Hi Hamza! 👋 This is your COORDINATION AGENT DXD AI sending you a direct chat message! 🤖 You have 39 overdue tasks - need help prioritizing?"
                
                success = self.send_chat_message_to_staff(hamza['staffid'], test_message)
                
                if success:
                    print("🎉 Integrated chat message sent to Hamza!")
                    print("💬 Check your chat interface - you should see a message from COORDINATION AGENT DXD AI!")
                else:
                    print("❌ Failed to send integrated chat message")
            
        except Exception as e:
            print(f"❌ Error in test message: {e}")

def main():
    """Test the integrated chat system"""
    print("🤖 INTEGRATED CHAT SYSTEM TEST")
    print("=" * 50)
    
    chat_system = IntegratedAIChatSystem()
    
    # First analyze the existing chat structure
    chat_system.analyze_chat_table_structure()
    
    print("\n" + "=" * 50)
    
    # Then try to send a test message
    chat_system.send_integrated_test_message()

if __name__ == "__main__":
    main()