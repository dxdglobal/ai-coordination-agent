from twilio.rest import Client
from config import Config

class WhatsAppService:
    def __init__(self):
        self.account_sid = Config.TWILIO_ACCOUNT_SID
        self.auth_token = Config.TWILIO_AUTH_TOKEN
        self.whatsapp_number = Config.TWILIO_WHATSAPP_NUMBER
        self.client = Client(self.account_sid, self.auth_token) if self.account_sid and self.auth_token else None
    
    def send_message(self, to_number, message):
        """Send WhatsApp message via Twilio"""
        if not self.client:
            return {'error': 'Twilio credentials not configured'}
        
        try:
            # Ensure the to_number is in WhatsApp format
            if not to_number.startswith('whatsapp:'):
                to_number = f'whatsapp:{to_number}'
            
            message = self.client.messages.create(
                body=message,
                from_=self.whatsapp_number,
                to=to_number
            )
            
            return {
                'success': True,
                'sid': message.sid,
                'status': message.status,
                'to': to_number,
                'message': message.body
            }
        
        except Exception as e:
            return {'error': f'Failed to send WhatsApp message: {str(e)}'}
    
    def handle_incoming_message(self, webhook_data):
        """Handle incoming WhatsApp message from webhook"""
        try:
            from_number = webhook_data.get('From', '')
            body = webhook_data.get('Body', '')
            message_sid = webhook_data.get('MessageSid', '')
            
            # Process the incoming message
            # You can add AI processing here to auto-respond or create tasks
            
            result = {
                'success': True,
                'from': from_number,
                'body': body,
                'message_sid': message_sid,
                'processed': True
            }
            
            # Auto-respond with acknowledgment
            if body.lower() in ['help', 'status', 'tasks']:
                self._handle_command(from_number, body.lower())
            
            return result
        
        except Exception as e:
            return {'error': f'Failed to process incoming message: {str(e)}'}
    
    def _handle_command(self, from_number, command):
        """Handle specific commands from WhatsApp"""
        try:
            if command == 'help':
                response = """
Available commands:
- help: Show this help message
- status: Get project status overview
- tasks: Get your assigned tasks
- create task [title]: Create a new task
                """
                self.send_message(from_number, response)
            
            elif command == 'status':
                # Get project status and send it
                from models.models import Project, Task, TaskStatus
                projects = Project.query.count()
                total_tasks = Task.query.count()
                completed_tasks = Task.query.filter_by(status=TaskStatus.DONE).count()
                
                response = f"""
Project Status Overview:
📊 Projects: {projects}
📋 Total Tasks: {total_tasks}
✅ Completed: {completed_tasks}
🔄 In Progress: {Task.query.filter_by(status=TaskStatus.IN_PROGRESS).count()}
                """
                self.send_message(from_number, response)
            
            elif command == 'tasks':
                # Get user's assigned tasks (you'd need to map WhatsApp number to user)
                response = "Feature coming soon: Get your assigned tasks"
                self.send_message(from_number, response)
        
        except Exception as e:
            error_response = f"Sorry, I couldn't process that command: {str(e)}"
            self.send_message(from_number, error_response)
    
    def send_task_notification(self, to_number, task_data):
        """Send task notification via WhatsApp"""
        if not self.client:
            return {'error': 'Twilio credentials not configured'}
        
        message = f"""
🔔 Task Update
Title: {task_data.get('title')}
Status: {task_data.get('status')}
Priority: {task_data.get('priority')}
{f"Assigned to: {task_data.get('assignee')}" if task_data.get('assignee') else ""}
{f"Due: {task_data.get('due_date')}" if task_data.get('due_date') else ""}
        """
        
        return self.send_message(to_number, message.strip())
    
    def send_project_update(self, to_number, project_data):
        """Send project update via WhatsApp"""
        if not self.client:
            return {'error': 'Twilio credentials not configured'}
        
        message = f"""
📈 Project Update
Project: {project_data.get('name')}
Status: {project_data.get('status')}
Progress: {project_data.get('completion_rate', 0):.1f}%
Tasks: {project_data.get('total_tasks')} total, {project_data.get('completed_tasks')} completed
        """
        
        return self.send_message(to_number, message.strip())
    
    def get_message_history(self, limit=50):
        """Get WhatsApp message history"""
        if not self.client:
            return {'error': 'Twilio credentials not configured'}
        
        try:
            messages = self.client.messages.list(
                from_=self.whatsapp_number,
                limit=limit
            )
            
            history = []
            for message in messages:
                history.append({
                    'sid': message.sid,
                    'from': message.from_,
                    'to': message.to,
                    'body': message.body,
                    'status': message.status,
                    'date_created': message.date_created.isoformat() if message.date_created else None,
                    'direction': 'outbound' if message.from_ == self.whatsapp_number else 'inbound'
                })
            
            return {
                'success': True,
                'messages': history,
                'count': len(history)
            }
        
        except Exception as e:
            return {'error': f'Failed to get message history: {str(e)}'}