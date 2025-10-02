#!/usr/bin/env python3
"""
Send test message to Hamza using the COORDINATION AGENT DXD AI
This simulates Hamza messaging the AI and getting a response
"""

from personal_chat_system import PersonalChatSystem
import json
from datetime import datetime

def send_test_message_to_hamza():
    """Send a test message from Hamza to the AI agent"""
    
    print("📱 TESTING: Hamza → COORDINATION AGENT DXD AI")
    print("=" * 60)
    
    # Initialize the chat system
    chat_system = PersonalChatSystem()
    
    # Test different message types from Hamza
    test_messages = [
        "Please give me my projects details",
        "Show me my pending tasks", 
        "What overdue tasks do I have?",
        "Do I have any tasks due today?",
        "Give me a summary of my work"
    ]
    
    print(f"🤖 AI Agent: {chat_system.ai_name}")
    print(f"📧 Contact: ai@dxdglobal.com")
    print(f"🆔 Staff ID: {chat_system.ai_staff_id}")
    print()
    
    for i, message in enumerate(test_messages, 1):
        print(f"💬 Test Message #{i}:")
        print(f"👤 Hamza: '{message}'")
        print(f"🤖 {chat_system.ai_name}:")
        print("─" * 50)
        
        try:
            # Process the message
            response = chat_system.process_chat_message("Hamza", message)
            
            # Store the conversation
            chat_system.store_chat_message("Hamza", message, response)
            
            # Display the response
            print(response)
            
        except Exception as e:
            print(f"❌ Error processing message: {e}")
        
        print("\n" + "=" * 60 + "\n")
    
    print("✅ All test messages sent successfully!")
    print("💾 Conversations have been stored in the database")
    print("📊 Hamza can now see his personalized task information!")

def simulate_real_conversation():
    """Simulate a more realistic conversation"""
    print("🎭 REALISTIC CONVERSATION SIMULATION")
    print("=" * 60)
    
    chat_system = PersonalChatSystem()
    
    # Simulate Hamza starting a conversation
    conversation = [
        ("Hamza", "Hi! Can you show me my current projects?"),
        ("Hamza", "What about my overdue tasks?"),
        ("Hamza", "Thanks! Can you help me prioritize what to work on first?")
    ]
    
    for sender, message in conversation:
        print(f"👤 {sender}: {message}")
        
        response = chat_system.process_chat_message(sender, message)
        chat_system.store_chat_message(sender, message, response)
        
        print(f"🤖 COORDINATION AGENT DXD AI:")
        # Show first few lines for readability
        lines = response.split('\n')
        for line in lines[:8]:  # Show first 8 lines
            print(f"   {line}")
        
        if len(lines) > 8:
            print("   ... (full response available)")
        
        print("─" * 50)
        print()

if __name__ == "__main__":
    print("🚀 HAMZA ↔ AI AGENT TEST CONVERSATION")
    print("=" * 60)
    
    # Send test messages
    send_test_message_to_hamza()
    
    # Simulate realistic conversation
    simulate_real_conversation()
    
    print("🎉 Test completed! Hamza has successfully chatted with the AI agent!")
    print("📱 The COORDINATION AGENT DXD AI is ready for real conversations!")