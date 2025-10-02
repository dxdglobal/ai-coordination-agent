"""
Personal Chat System for COORDINATION AGENT DXD AI
Handles direct messages from staff members requesting their task/project details
"""

import mysql.connector
from datetime import datetime, date
import json

class PersonalChatSystem:
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
    
    def find_staff_by_name(self, staff_name):
        """Find staff member by name"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return []
            cursor = connection.cursor(dictionary=True)
            
            # Search for staff member by name (case insensitive)
            query = """
            SELECT * FROM tblstaff 
            WHERE LOWER(firstname) LIKE LOWER(%s) 
            OR LOWER(lastname) LIKE LOWER(%s)
            OR LOWER(CONCAT(firstname, ' ', lastname)) LIKE LOWER(%s)
            """
            cursor.execute(query, (f'%{staff_name}%', f'%{staff_name}%', f'%{staff_name}%'))
            
            staff_members = cursor.fetchall()
            cursor.close()
            connection.close()
            
            return staff_members
            
        except Exception as e:
            print(f"❌ Error finding staff: {e}")
            return []
    
    def get_staff_tasks(self, staff_id, task_type="all"):
        """Get all tasks assigned to a specific staff member"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return []
            cursor = connection.cursor(dictionary=True)
            
            # Base query for staff tasks
            base_query = """
            SELECT 
                t.id,
                t.name as task_name,
                t.description,
                t.startdate,
                t.duedate,
                t.status,
                t.priority,
                p.name as project_name,
                s.firstname,
                s.lastname,
                CASE 
                    WHEN t.duedate < CURDATE() AND t.status NOT IN (2, 3) THEN 'overdue'
                    WHEN t.duedate = CURDATE() AND t.status NOT IN (2, 3) THEN 'due_today'
                    WHEN DATEDIFF(t.duedate, CURDATE()) BETWEEN 1 AND 3 AND t.status NOT IN (2, 3) THEN 'due_soon'
                    WHEN t.status = 2 THEN 'completed'
                    WHEN t.status = 3 THEN 'completed'
                    ELSE 'normal'
                END as urgency_status
            FROM tbltasks t
            LEFT JOIN tblprojects p ON t.rel_id = p.id
            LEFT JOIN tblstaff s ON t.addedfrom = s.staffid
            WHERE t.addedfrom = %s
            """
            
            # Add conditions based on task type
            if task_type == "pending":
                base_query += " AND t.status NOT IN (2, 3)"
            elif task_type == "overdue":
                base_query += " AND t.duedate < CURDATE() AND t.status NOT IN (2, 3)"
            elif task_type == "completed":
                base_query += " AND t.status IN (2, 3)"
            
            base_query += " ORDER BY t.duedate ASC, t.priority DESC"
            
            cursor.execute(base_query, (staff_id,))
            tasks = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return tasks
            
        except Exception as e:
            print(f"❌ Error getting staff tasks: {e}")
            return []
    
    def get_staff_projects(self, staff_id):
        """Get all projects associated with a staff member"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return []
            cursor = connection.cursor(dictionary=True)
            
            query = """
            SELECT DISTINCT
                p.id,
                p.name as project_name,
                p.description,
                p.start_date,
                p.deadline,
                p.status,
                COUNT(t.id) as total_tasks,
                SUM(CASE WHEN t.status IN (2, 3) THEN 1 ELSE 0 END) as completed_tasks,
                SUM(CASE WHEN t.duedate < CURDATE() AND t.status NOT IN (2, 3) THEN 1 ELSE 0 END) as overdue_tasks
            FROM tblprojects p
            LEFT JOIN tbltasks t ON p.id = t.rel_id
            WHERE t.addedfrom = %s
            GROUP BY p.id, p.name, p.description, p.start_date, p.deadline, p.status
            ORDER BY p.deadline ASC
            """
            
            cursor.execute(query, (staff_id,))
            projects = cursor.fetchall()
            
            cursor.close()
            connection.close()
            
            return projects
            
        except Exception as e:
            print(f"❌ Error getting staff projects: {e}")
            return []
    
    def generate_personal_response(self, staff_name, request_type, tasks, projects=None):
        """Generate a friendly, personal response with task/project details"""
        
        response = f"Hi {staff_name}! 👋\n\n"
        
        if request_type.lower() in ['tasks', 'pending', 'all']:
            if not tasks:
                response += "🎉 Great news! You don't have any pending tasks right now. Well done!"
            else:
                # Categorize tasks
                overdue = [t for t in tasks if t['urgency_status'] == 'overdue']
                due_today = [t for t in tasks if t['urgency_status'] == 'due_today']
                due_soon = [t for t in tasks if t['urgency_status'] == 'due_soon']
                completed = [t for t in tasks if t['urgency_status'] == 'completed']
                normal = [t for t in tasks if t['urgency_status'] == 'normal']
                
                response += f"📋 **Your Task Summary:**\n"
                response += f"• Total Tasks: {len(tasks)}\n"
                
                if overdue:
                    response += f"• 🚨 Overdue: {len(overdue)} tasks\n"
                if due_today:
                    response += f"• ⏰ Due Today: {len(due_today)} tasks\n"
                if due_soon:
                    response += f"• 📅 Due Soon: {len(due_soon)} tasks\n"
                if completed:
                    response += f"• ✅ Completed: {len(completed)} tasks\n"
                if normal:
                    response += f"• 📝 In Progress: {len(normal)} tasks\n"
                
                response += "\n"
                
                # Show urgent tasks first
                if overdue:
                    response += "🚨 **URGENT - Overdue Tasks:**\n"
                    for task in overdue[:3]:  # Show top 3
                        response += f"• Task #{task['id']}: {task['task_name'][:50]}{'...' if len(task['task_name']) > 50 else ''}\n"
                        response += f"  📅 Due: {task['duedate']} | Project: {task['project_name'] or 'No Project'}\n"
                    if len(overdue) > 3:
                        response += f"  ... and {len(overdue) - 3} more overdue tasks\n"
                    response += "\n"
                
                if due_today:
                    response += "⏰ **Due Today:**\n"
                    for task in due_today[:3]:
                        response += f"• Task #{task['id']}: {task['task_name'][:50]}{'...' if len(task['task_name']) > 50 else ''}\n"
                        response += f"  Project: {task['project_name'] or 'No Project'}\n"
                    response += "\n"
                
                if due_soon:
                    response += "📅 **Coming Up Soon:**\n"
                    for task in due_soon[:3]:
                        response += f"• Task #{task['id']}: {task['task_name'][:50]}{'...' if len(task['task_name']) > 50 else ''}\n"
                        response += f"  📅 Due: {task['duedate']} | Project: {task['project_name'] or 'No Project'}\n"
                    response += "\n"
        
        if request_type.lower() in ['projects', 'all'] and projects:
            response += "🏗️ **Your Projects:**\n"
            for project in projects[:5]:  # Show top 5 projects
                completion_rate = 0
                if project['total_tasks'] > 0:
                    completion_rate = (project['completed_tasks'] / project['total_tasks']) * 100
                
                response += f"• **{project['project_name']}**\n"
                response += f"  📊 Progress: {project['completed_tasks']}/{project['total_tasks']} tasks ({completion_rate:.1f}%)\n"
                if project['overdue_tasks'] > 0:
                    response += f"  🚨 Overdue: {project['overdue_tasks']} tasks\n"
                response += f"  📅 Deadline: {project['deadline']}\n\n"
        
        response += "Need help with any specific task? Just ask! 😊\n"
        response += f"- Your AI Assistant, **{self.ai_name}**"
        
        return response
    
    def process_chat_message(self, sender_name, message):
        """Process incoming chat message and generate appropriate response"""
        
        # Find the staff member
        staff_members = self.find_staff_by_name(sender_name)
        if not staff_members:
            return f"Hi! I couldn't find your staff profile. Please check if your name is spelled correctly."
        
        if len(staff_members) > 1:
            names = [f"{s['firstname']} {s['lastname']}" for s in staff_members]
            return f"Found multiple matches: {', '.join(names)}. Please be more specific!"
        
        staff = staff_members[0]
        staff_id = staff['staffid']
        full_name = f"{staff['firstname']} {staff['lastname']}"
        
        # Determine request type from message
        message_lower = message.lower()
        request_type = "all"  # default
        
        if any(word in message_lower for word in ['pending', 'pending tasks']):
            request_type = "pending"
        elif any(word in message_lower for word in ['overdue', 'late']):
            request_type = "overdue"
        elif any(word in message_lower for word in ['completed', 'finished', 'done']):
            request_type = "completed"
        elif any(word in message_lower for word in ['project', 'projects']):
            request_type = "projects"
        
        # Get tasks and projects
        tasks = self.get_staff_tasks(staff_id, request_type if request_type != "projects" else "all")
        projects = None
        
        if request_type in ["projects", "all"]:
            projects = self.get_staff_projects(staff_id)
        
        # Generate response
        response = self.generate_personal_response(full_name, request_type, tasks, projects)
        
        return response
    
    def store_chat_message(self, sender_name, message, response):
        """Store chat conversation in database"""
        try:
            connection = self.get_database_connection()
            if not connection:
                return False
            cursor = connection.cursor()
            
            # Create chat log table if it doesn't exist
            create_table_query = """
            CREATE TABLE IF NOT EXISTS ai_chat_log (
                id INT AUTO_INCREMENT PRIMARY KEY,
                sender_name VARCHAR(100) NOT NULL,
                message TEXT NOT NULL,
                ai_response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                ai_staff_id INT DEFAULT 248
            )
            """
            cursor.execute(create_table_query)
            
            # Insert chat message
            insert_query = """
            INSERT INTO ai_chat_log (sender_name, message, ai_response, ai_staff_id)
            VALUES (%s, %s, %s, %s)
            """
            cursor.execute(insert_query, (sender_name, message, response, self.ai_staff_id))
            
            connection.commit()
            cursor.close()
            connection.close()
            
            return True
            
        except Exception as e:
            print(f"❌ Error storing chat message: {e}")
            return False

# Test the system
if __name__ == "__main__":
    chat_system = PersonalChatSystem()
    
    # Test with Hamza
    print("🧪 Testing Personal Chat System...")
    print("=" * 50)
    
    response = chat_system.process_chat_message("Hamza", "Please give me my projects details")
    print("📨 Message: 'Please give me my projects details'")
    print(f"🤖 Response:\n{response}")
    print("=" * 50)
    
    response2 = chat_system.process_chat_message("Hamza", "Show me my pending tasks")
    print("📨 Message: 'Show me my pending tasks'")
    print(f"🤖 Response:\n{response2}")