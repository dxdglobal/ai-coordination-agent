import asyncio
try:
    from telegram import Bot, Update
    from telegram.ext import Application, CommandHandler, MessageHandler, filters
    TELEGRAM_AVAILABLE = True
except ImportError:
    Bot = None
    Update = None
    Application = None
    CommandHandler = None
    MessageHandler = None
    filters = None
    TELEGRAM_AVAILABLE = False

from config import Config
import json

class TelegramService:
    def __init__(self):
        self.bot_token = Config.TELEGRAM_BOT_TOKEN
        self.bot = Bot(token=self.bot_token) if (self.bot_token and TELEGRAM_AVAILABLE) else None
    
    def send_message(self, chat_id, message, parse_mode='HTML'):
        """Send message to Telegram chat"""
        if not self.bot:
            return {'error': 'Telegram bot token not configured'}
        
        try:
            # Use asyncio to run the async method
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def _send():
                message_obj = await self.bot.send_message(
                    chat_id=chat_id,
                    text=message,
                    parse_mode=parse_mode
                )
                return message_obj
            
            result = loop.run_until_complete(_send())
            loop.close()
            
            return {
                'success': True,
                'message_id': result.message_id,
                'chat_id': chat_id,
                'text': message
            }
        
        except Exception as e:
            return {'error': f'Failed to send Telegram message: {str(e)}'}
    
    def handle_update(self, update_data):
        """Handle incoming Telegram update"""
        try:
            if 'message' in update_data:
                message = update_data['message']
                chat_id = message.get('chat', {}).get('id')
                text = message.get('text', '')
                
                # Handle commands
                if text.startswith('/'):
                    return self._handle_command(chat_id, text)
                else:
                    return self._handle_message(chat_id, text, message)
            
            return {'success': True, 'processed': True}
        
        except Exception as e:
            return {'error': f'Failed to handle Telegram update: {str(e)}'}
    
    def _handle_command(self, chat_id, command):
        """Handle Telegram bot commands"""
        try:
            if command == '/start':
                response = """
🤖 Welcome to Project Management Bot!

Available commands:
/help - Show this help message
/status - Get project status overview
/tasks - Get tasks overview
/projects - List all projects
/create_task [title] - Create a new task
                """
                return self.send_message(chat_id, response)
            
            elif command == '/help':
                response = """
📋 Available Commands:

/status - Project status overview
/tasks - Tasks summary
/projects - List projects
/create_task [title] - Create new task

You can also send messages to interact with the AI coordination agent.
                """
                return self.send_message(chat_id, response)
            
            elif command == '/status':
                return self._send_status_update(chat_id)
            
            elif command == '/tasks':
                return self._send_tasks_overview(chat_id)
            
            elif command == '/projects':
                return self._send_projects_list(chat_id)
            
            elif command.startswith('/create_task'):
                task_title = command.replace('/create_task', '').strip()
                return self._create_task_from_telegram(chat_id, task_title)
            
            else:
                response = "Unknown command. Use /help to see available commands."
                return self.send_message(chat_id, response)
        
        except Exception as e:
            error_response = f"Sorry, I couldn't process that command: {str(e)}"
            return self.send_message(chat_id, error_response)
    
    def _handle_message(self, chat_id, text, message_data):
        """Handle regular messages (can be processed by AI)"""
        try:
            # For now, acknowledge the message
            response = f"Message received: {text}\n\nUse /help to see available commands."
            return self.send_message(chat_id, response)
        
        except Exception as e:
            return {'error': f'Failed to handle message: {str(e)}'}
    
    def _send_status_update(self, chat_id):
        """Send project status to Telegram"""
        try:
            from models.models import Project, Task, TaskStatus
            
            projects = Project.query.count()
            total_tasks = Task.query.count()
            completed_tasks = Task.query.filter_by(status=TaskStatus.DONE).count()
            in_progress_tasks = Task.query.filter_by(status=TaskStatus.IN_PROGRESS).count()
            
            completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
            
            response = f"""
📊 <b>Project Status Overview</b>

🏗️ <b>Projects:</b> {projects}
📋 <b>Total Tasks:</b> {total_tasks}
✅ <b>Completed:</b> {completed_tasks}
🔄 <b>In Progress:</b> {in_progress_tasks}
📈 <b>Completion Rate:</b> {completion_rate:.1f}%
            """
            
            return self.send_message(chat_id, response.strip())
        
        except Exception as e:
            return self.send_message(chat_id, f"Error getting status: {str(e)}")
    
    def _send_tasks_overview(self, chat_id):
        """Send tasks overview to Telegram"""
        try:
            from models.models import Task, TaskStatus, Priority
            
            high_priority_tasks = Task.query.filter_by(priority=Priority.HIGH).count()
            urgent_tasks = Task.query.filter_by(priority=Priority.URGENT).count()
            overdue_tasks = Task.query.filter(
                Task.end_time < Task.query.session.execute('SELECT NOW()').scalar()
            ).filter(Task.status != TaskStatus.DONE).count()
            
            response = f"""
📋 <b>Tasks Overview</b>

🔥 <b>Urgent Tasks:</b> {urgent_tasks}
⚠️ <b>High Priority:</b> {high_priority_tasks}
⏰ <b>Overdue Tasks:</b> {overdue_tasks}

Use /status for complete overview.
            """
            
            return self.send_message(chat_id, response.strip())
        
        except Exception as e:
            return self.send_message(chat_id, f"Error getting tasks: {str(e)}")
    
    def _send_projects_list(self, chat_id):
        """Send projects list to Telegram"""
        try:
            from models.models import Project
            
            projects = Project.query.limit(10).all()
            
            if not projects:
                response = "No projects found."
            else:
                response = "<b>📁 Projects:</b>\n\n"
                for project in projects:
                    task_count = len(project.tasks)
                    response += f"• <b>{project.name}</b>\n"
                    response += f"  Status: {project.status.value}\n"
                    response += f"  Tasks: {task_count}\n\n"
            
            return self.send_message(chat_id, response)
        
        except Exception as e:
            return self.send_message(chat_id, f"Error getting projects: {str(e)}")
    
    def _create_task_from_telegram(self, chat_id, task_title):
        """Create a task from Telegram"""
        try:
            if not task_title:
                return self.send_message(chat_id, "Please provide a task title. Usage: /create_task [title]")
            
            from models.models import db, Task
            
            task = Task(
                title=task_title,
                description=f"Created via Telegram by chat {chat_id}"
            )
            
            db.session.add(task)
            db.session.commit()
            
            response = f"✅ Task created successfully!\n\n<b>Title:</b> {task_title}\n<b>ID:</b> {task.id}"
            return self.send_message(chat_id, response)
        
        except Exception as e:
            return self.send_message(chat_id, f"Error creating task: {str(e)}")
    
    def send_task_notification(self, chat_id, task_data):
        """Send task notification to Telegram"""
        if not self.bot:
            return {'error': 'Telegram bot token not configured'}
        
        message = f"""
🔔 <b>Task Update</b>

<b>Title:</b> {task_data.get('title')}
<b>Status:</b> {task_data.get('status')}
<b>Priority:</b> {task_data.get('priority')}
{f"<b>Assigned to:</b> {task_data.get('assignee')}" if task_data.get('assignee') else ""}
{f"<b>Due:</b> {task_data.get('due_date')}" if task_data.get('due_date') else ""}
        """
        
        return self.send_message(chat_id, message.strip())
    
    def send_project_update(self, chat_id, project_data):
        """Send project update to Telegram"""
        if not self.bot:
            return {'error': 'Telegram bot token not configured'}
        
        message = f"""
📈 <b>Project Update</b>

<b>Project:</b> {project_data.get('name')}
<b>Status:</b> {project_data.get('status')}
<b>Progress:</b> {project_data.get('completion_rate', 0):.1f}%
<b>Tasks:</b> {project_data.get('total_tasks')} total, {project_data.get('completed_tasks')} completed
        """
        
        return self.send_message(chat_id, message.strip())
    
    def set_webhook(self, webhook_url):
        """Set webhook for Telegram bot"""
        if not self.bot:
            return {'error': 'Telegram bot token not configured'}
        
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            async def _set_webhook():
                return await self.bot.set_webhook(url=webhook_url)
            
            result = loop.run_until_complete(_set_webhook())
            loop.close()
            
            return {'success': True, 'webhook_set': result}
        
        except Exception as e:
            return {'error': f'Failed to set webhook: {str(e)}'}