import yagmail
from config import Config
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailService:
    def __init__(self):
        self.email_user = Config.EMAIL_USER
        self.email_password = Config.EMAIL_PASSWORD
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
    
    def send_email(self, to_email, subject, body, html_body=None):
        """Send email using SMTP"""
        if not all([self.email_user, self.email_password]):
            return {'error': 'Email credentials not configured'}
        
        try:
            # Use yagmail for simpler sending
            yag = yagmail.SMTP(self.email_user, self.email_password)
            
            contents = [body]
            if html_body:
                contents.append(html_body)
            
            yag.send(
                to=to_email,
                subject=subject,
                contents=contents
            )
            
            return {
                'success': True,
                'to': to_email,
                'subject': subject,
                'message': 'Email sent successfully'
            }
        
        except Exception as e:
            # Fallback to standard SMTP
            return self._send_email_smtp(to_email, subject, body, html_body)
    
    def _send_email_smtp(self, to_email, subject, body, html_body=None):
        """Send email using standard SMTP library"""
        try:
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.email_user
            msg['To'] = to_email
            
            # Add text part
            text_part = MIMEText(body, 'plain')
            msg.attach(text_part)
            
            # Add HTML part if provided
            if html_body:
                html_part = MIMEText(html_body, 'html')
                msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.email_user, self.email_password)
                server.send_message(msg)
            
            return {
                'success': True,
                'to': to_email,
                'subject': subject,
                'message': 'Email sent successfully'
            }
        
        except Exception as e:
            return {'error': f'Failed to send email: {str(e)}'}
    
    def send_task_notification(self, to_email, task_data):
        """Send task notification email"""
        subject = f"Task Update: {task_data.get('title')}"
        
        body = f"""
Task Update Notification

Title: {task_data.get('title')}
Status: {task_data.get('status')}
Priority: {task_data.get('priority')}
{f"Assigned to: {task_data.get('assignee')}" if task_data.get('assignee') else ""}
{f"Due Date: {task_data.get('due_date')}" if task_data.get('due_date') else ""}

Description:
{task_data.get('description', 'No description provided')}

---
This is an automated notification from the Project Management System.
        """
        
        html_body = f"""
        <html>
        <body>
            <h2>Task Update Notification</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><td><b>Title:</b></td><td>{task_data.get('title')}</td></tr>
                <tr><td><b>Status:</b></td><td>{task_data.get('status')}</td></tr>
                <tr><td><b>Priority:</b></td><td>{task_data.get('priority')}</td></tr>
                {f"<tr><td><b>Assigned to:</b></td><td>{task_data.get('assignee')}</td></tr>" if task_data.get('assignee') else ""}
                {f"<tr><td><b>Due Date:</b></td><td>{task_data.get('due_date')}</td></tr>" if task_data.get('due_date') else ""}
            </table>
            
            <h3>Description:</h3>
            <p>{task_data.get('description', 'No description provided')}</p>
            
            <hr>
            <p><i>This is an automated notification from the Project Management System.</i></p>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_project_update(self, to_email, project_data):
        """Send project update email"""
        subject = f"Project Update: {project_data.get('name')}"
        
        completion_rate = project_data.get('completion_rate', 0)
        
        body = f"""
Project Update Notification

Project: {project_data.get('name')}
Status: {project_data.get('status')}
Progress: {completion_rate:.1f}%
Tasks: {project_data.get('total_tasks')} total, {project_data.get('completed_tasks')} completed

Description:
{project_data.get('description', 'No description provided')}

---
This is an automated notification from the Project Management System.
        """
        
        html_body = f"""
        <html>
        <body>
            <h2>Project Update Notification</h2>
            <table border="1" cellpadding="5" cellspacing="0">
                <tr><td><b>Project:</b></td><td>{project_data.get('name')}</td></tr>
                <tr><td><b>Status:</b></td><td>{project_data.get('status')}</td></tr>
                <tr><td><b>Progress:</b></td><td>{completion_rate:.1f}%</td></tr>
                <tr><td><b>Total Tasks:</b></td><td>{project_data.get('total_tasks')}</td></tr>
                <tr><td><b>Completed Tasks:</b></td><td>{project_data.get('completed_tasks')}</td></tr>
            </table>
            
            <h3>Description:</h3>
            <p>{project_data.get('description', 'No description provided')}</p>
            
            <hr>
            <p><i>This is an automated notification from the Project Management System.</i></p>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_body)
    
    def send_daily_summary(self, to_email, summary_data):
        """Send daily project summary email"""
        subject = f"Daily Project Summary - {summary_data.get('date')}"
        
        body = f"""
Daily Project Summary

Date: {summary_data.get('date')}

Overview:
- Total Projects: {summary_data.get('total_projects')}
- Total Tasks: {summary_data.get('total_tasks')}
- Completed Today: {summary_data.get('completed_today')}
- In Progress: {summary_data.get('in_progress')}
- Overdue: {summary_data.get('overdue')}

Top Priority Items:
{chr(10).join(f"- {item}" for item in summary_data.get('priority_items', []))}

Recent Activities:
{chr(10).join(f"- {activity}" for activity in summary_data.get('recent_activities', []))}

---
This is an automated daily summary from the Project Management System.
        """
        
        return self.send_email(to_email, subject, body)
    
    def send_reminder_email(self, to_email, reminder_data):
        """Send reminder email for tasks or deadlines"""
        subject = f"Reminder: {reminder_data.get('title')}"
        
        body = f"""
Reminder Notification

{reminder_data.get('message')}

Item: {reminder_data.get('title')}
Type: {reminder_data.get('type')}
Due: {reminder_data.get('due_date')}
Priority: {reminder_data.get('priority')}

Please take appropriate action.

---
This is an automated reminder from the Project Management System.
        """
        
        return self.send_email(to_email, subject, body)
    
    def send_welcome_email(self, to_email, user_name):
        """Send welcome email to new users"""
        subject = "Welcome to Project Management System"
        
        body = f"""
Welcome to Project Management System!

Hello {user_name},

Your account has been set up and you can now access the project management system.

Features available to you:
- Task management and tracking
- Project collaboration
- AI-powered coordination assistance
- Integration with multiple communication channels
- Real-time notifications and updates

Get started by logging in to the dashboard and exploring your projects.

If you have any questions, feel free to reach out to the support team.

Welcome aboard!

---
Project Management System Team
        """
        
        html_body = f"""
        <html>
        <body>
            <h1>Welcome to Project Management System!</h1>
            <p>Hello <b>{user_name}</b>,</p>
            
            <p>Your account has been set up and you can now access the project management system.</p>
            
            <h3>Features available to you:</h3>
            <ul>
                <li>Task management and tracking</li>
                <li>Project collaboration</li>
                <li>AI-powered coordination assistance</li>
                <li>Integration with multiple communication channels</li>
                <li>Real-time notifications and updates</li>
            </ul>
            
            <p>Get started by logging in to the dashboard and exploring your projects.</p>
            
            <p>If you have any questions, feel free to reach out to the support team.</p>
            
            <h2>Welcome aboard!</h2>
            
            <hr>
            <p><i>Project Management System Team</i></p>
        </body>
        </html>
        """
        
        return self.send_email(to_email, subject, body, html_body)