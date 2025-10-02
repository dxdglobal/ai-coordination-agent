#!/usr/bin/env python3
"""
Test AI Agent Contact Discovery
Shows how staff can find and message the COORDINATION AGENT DXD AI
"""

import mysql.connector
from personal_chat_system import PersonalChatSystem

# Database connection
db_config = {
    'host': '92.113.22.65',
    'user': 'u906714182_sqlrrefdvdv', 
    'password': '3@6*t:lU',
    'database': 'u906714182_sqlrrefdvdv'
}

def show_staff_list():
    """Show the staff list like it would appear in the chat interface"""
    try:
        conn = mysql.connector.connect(**db_config)
        cursor = conn.cursor(dictionary=True)
        
        print("👥 STAFF LIST - DELUXE DIGITAL SOLUTIONS")
        print("=" * 50)
        
        # Get all active staff members (like the interface would show)
        cursor.execute("""
            SELECT staffid, firstname, lastname, email, active
            FROM tblstaff 
            WHERE active = 1 
            ORDER BY firstname ASC
            LIMIT 15
        """)
        
        staff_list = cursor.fetchall()
        
        for staff in staff_list:
            name = f"{staff['firstname']} {staff['lastname']}".strip()
            if staff['staffid'] == 248:
                print(f"🤖 {name} ⭐ (AI Assistant)")
            else:
                status = "🟢" if staff['active'] else "🔴"
                print(f"{status} {name}")
        
        cursor.close()
        conn.close()
        
        print("\n💬 Staff can now click on 'COORDINATION AGENT DXD AI' to start chatting!")
        
    except Exception as e:
        print(f"❌ Error showing staff list: {e}")

def simulate_staff_messaging_ai():
    """Simulate different staff members messaging the AI"""
    print("\n🧪 TESTING: Staff Members Messaging AI Agent")
    print("=" * 60)
    
    chat_system = PersonalChatSystem()
    
    # Test scenarios
    test_scenarios = [
        ("Hamza", "Please give me my projects details"),
        ("Tuğba", "Show me my pending tasks"), 
        ("Prakhar", "What are my overdue tasks?"),
        ("Begüm Damla Şen", "Do I have any tasks due today?")
    ]
    
    for staff_name, message in test_scenarios:
        print(f"\n📱 {staff_name} → COORDINATION AGENT DXD AI")
        print(f"💬 Message: '{message}'")
        print("🤖 AI Response:")
        
        response = chat_system.process_chat_message(staff_name, message)
        
        # Show first few lines of response
        lines = response.split('\n')[:6]
        for line in lines:
            print(f"   {line}")
        
        if len(response.split('\n')) > 6:
            print("   ... (more details)")
        
        print("   " + "─" * 40)

def show_ai_contact_info():
    """Show AI agent contact information"""
    print("\n📋 AI AGENT CONTACT INFO")
    print("=" * 40)
    print("👤 Name: COORDINATION AGENT DXD AI")
    print("🆔 Staff ID: 248")
    print("📧 Email: ai@dxdglobal.com")
    print("🟢 Status: Online 24/7")
    print("⚡ Response Time: Instant")
    print("\n💡 What you can ask:")
    print("   • 'Show me my projects details'")
    print("   • 'What are my pending tasks?'")
    print("   • 'Do I have any overdue tasks?'")
    print("   • 'Show me tasks due today'")
    print("   • Any task-related questions!")

if __name__ == "__main__":
    print("🚀 AI AGENT CONTACT SETUP TEST")
    print("=" * 60)
    
    # Show the staff list with AI agent
    show_staff_list()
    
    # Show AI contact info
    show_ai_contact_info()
    
    # Test messaging scenarios
    simulate_staff_messaging_ai()
    
    print("\n✅ COORDINATION AGENT DXD AI is ready to receive messages!")
    print("📱 Staff can now find and chat with the AI from their contact list!")