from flask import Flask, request, jsonify
from flask_cors import CORS
from config import Config
from personal_chat_system import PersonalChatSystem
import os
import threading
import subprocess
import sys

def start_background_scripts():
    """Start all background monitoring and automation scripts"""
    print("🚀 Starting background monitoring scripts...")
    
    # List of scripts to run in background
    background_scripts = [
        'human_like_task_monitor.py',  # Main 24/7 task monitoring
    ]
    
    for script in background_scripts:
        if os.path.exists(script):
            try:
                print(f"  ▶ Starting {script}...")
                # Start each script in a separate thread
                thread = threading.Thread(
                    target=run_script_in_background,
                    args=(script,),
                    daemon=True  # Dies when main app dies
                )
                thread.start()
                print(f"  ✅ {script} started successfully")
            except Exception as e:
                print(f"  ❌ Failed to start {script}: {e}")
        else:
            print(f"  ⚠️ Script not found: {script}")
    
    print("🎯 All background scripts initialization complete!")

def run_script_in_background(script_name):
    """Run a Python script in background"""
    try:
        # Use the same Python interpreter that's running the main app
        print(f"🔄 Running {script_name} in background...")
        process = subprocess.Popen([sys.executable, script_name], 
                                 stdout=subprocess.PIPE, 
                                 stderr=subprocess.PIPE,
                                 text=True)
        # Don't wait for the process - let it run in background
        print(f"✅ {script_name} is now running in background (PID: {process.pid})")
    except Exception as e:
        print(f"❌ Error starting {script_name}: {e}")

def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    # Initialize extensions
    from models.models import db
    db.init_app(app)
    
    # Configure CORS with specific settings
    CORS(app, resources={
        r"/ai/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        },
        r"/api/*": {
            "origins": ["http://localhost:5173", "http://127.0.0.1:5173", "http://localhost:5174", "http://127.0.0.1:5174"],
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"]
        }
    })
    
    # Register blueprints
    from routes.api import api_bp
    from routes.integrations import integrations_bp
    from routes.ai import ai_bp
    
    app.register_blueprint(api_bp, url_prefix='/api')
    app.register_blueprint(integrations_bp, url_prefix='/integrations')
    app.register_blueprint(ai_bp, url_prefix='/ai')
    
    # Initialize personal chat system
    chat_system = PersonalChatSystem()
    
    # Personal Chat API Endpoint
    @app.route('/api/personal-chat', methods=['POST'])
    def personal_chat():
        """Handle personal chat messages from staff members"""
        try:
            data = request.get_json()
            
            # Validate request
            if not data or 'sender_name' not in data or 'message' not in data:
                return jsonify({
                    'success': False,
                    'error': 'Missing required fields: sender_name and message'
                }), 400
            
            sender_name = data['sender_name']
            message = data['message']
            
            # Process the chat message
            response = chat_system.process_chat_message(sender_name, message)
            
            # Store the conversation
            chat_system.store_chat_message(sender_name, message, response)
            
            return jsonify({
                'success': True,
                'sender': sender_name,
                'user_message': message,
                'ai_response': response,
                'ai_name': 'COORDINATION AGENT DXD AI'
            })
            
        except Exception as e:
            return jsonify({
                'success': False,
                'error': f'Chat processing failed: {str(e)}'
            }), 500
    
    # Test endpoint to simulate chat
    @app.route('/api/test-chat/<staff_name>')
    def test_chat(staff_name):
        """Quick test endpoint for personal chat"""
        test_message = "Please give me my projects details"
        response = chat_system.process_chat_message(staff_name, test_message)
        
        return jsonify({
            'staff_name': staff_name,
            'test_message': test_message,
            'ai_response': response,
            'ai_name': 'COORDINATION AGENT DXD AI'
        })
    
    # Create tables (skip if tables already exist to avoid timeout)
    # Tables already exist based on our database test
    # with app.app_context():
    #     db.create_all()
    
    return app

# Create app instance for imports
app = create_app()

if __name__ == '__main__':
    print("🌟 AI COORDINATION AGENT STARTING UP...")
    print("=" * 50)
    
    # Start all background monitoring scripts
    start_background_scripts()
    
    print("\n🌐 Starting Flask web server...")
    print("📡 Server will be available at: http://127.0.0.1:5001")
    print("🔄 24/7 Task monitoring is now ACTIVE!")
    print("=" * 50)
    
    app.run(debug=False, host='127.0.0.1', port=5001)