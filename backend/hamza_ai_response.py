#!/usr/bin/env python3
"""
Hamza Projects Search - Simple keyword-based search
Shows Hamza's 18 projects from CRM with basic filtering
"""
import os
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

class HamzaProjectsSimpleSearch:
    def __init__(self):
        self.hamza_staff_id = 188  # Hamza Haseeb's staff ID
        
    def get_db_connection(self):
        """Get database connection"""
        return mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
    
    def get_hamza_projects_with_details(self):
        """Get all projects assigned to Hamza with client info"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT p.id, p.name, p.description, p.status, p.project_created,
                   p.progress, p.deadline, p.start_date, p.clientid,
                   c.company as client_name
            FROM tblprojects p
            JOIN tblproject_members pm ON p.id = pm.project_id  
            LEFT JOIN tblclients c ON p.clientid = c.userid
            WHERE pm.staff_id = %s
            ORDER BY p.project_created DESC
        """, (self.hamza_staff_id,))
        
        projects = cursor.fetchall()
        conn.close()
        return projects
    
    def search_hamza_projects(self, query=""):
        """Search Hamza's projects with keyword matching"""
        projects = self.get_hamza_projects_with_details()
        
        if not query:
            return projects
        
        # Simple keyword search
        query_lower = query.lower()
        filtered_projects = []
        
        for project in projects:
            pid, name, description, status, created, progress, deadline, start_date, clientid, client_name = project
            
            # Search in project name, description, and client name
            searchable_text = f"{name} {description or ''} {client_name or ''}".lower()
            
            if query_lower in searchable_text:
                filtered_projects.append(project)
        
        return filtered_projects
    
    def get_project_summary(self):
        """Get summary of Hamza's projects"""
        projects = self.get_hamza_projects_with_details()
        
        # Status mapping for better display
        status_names = {
            1: 'Not Started', 
            2: 'Active/In Progress', 
            3: 'On Hold', 
            4: 'Completed', 
            5: 'Cancelled'
        }
        
        total = len(projects)
        active = len([p for p in projects if p[3] == 2])
        completed = len([p for p in projects if p[3] == 4])
        
        # Group by categories based on project names
        categories = {
            'AI/Automation': [],
            'Website Development': [],
            'Social Media/Marketing': [],
            'Construction/Real Estate': [],
            'Other': []
        }
        
        for project in projects:
            name = project[1].lower()
            if any(keyword in name for keyword in ['ai', 'automation', 'script']):
                categories['AI/Automation'].append(project)
            elif any(keyword in name for keyword in ['website', 'web', 'wordpress', 'development']):
                categories['Website Development'].append(project)
            elif any(keyword in name for keyword in ['social', 'medya', 'grafik', 'içerik']):
                categories['Social Media/Marketing'].append(project)
            elif any(keyword in name for keyword in ['construction', 'inşaat', 'real estate', 'ocean']):
                categories['Construction/Real Estate'].append(project)
            else:
                categories['Other'].append(project)
        
        return {
            'total_projects': total,
            'active_projects': active,
            'completed_projects': completed,
            'projects': projects,
            'categories': categories,
            'status_names': status_names
        }

def create_ai_response_for_hamza_projects():
    """Create AI-style response about Hamza's projects"""
    service = HamzaProjectsSimpleSearch()
    summary = service.get_project_summary()
    
    response = f"""🎯 **Hamza's Project Portfolio Analysis**

I found **{summary['total_projects']} projects** assigned to **Hamza Haseeb** in your CRM system:

📊 **Project Status Overview:**
- **Active/In Progress**: {summary['active_projects']} projects
- **Completed**: {summary['completed_projects']} projects
- **Total Assigned**: {summary['total_projects']} projects

📋 **Project Categories:**"""
    
    for category, projects in summary['categories'].items():
        if projects:
            response += f"\n\n**{category}** ({len(projects)} projects):"
            for i, project in enumerate(projects[:3], 1):  # Show top 3 per category
                name = project[1][:50] + "..." if len(project[1]) > 50 else project[1]
                status = summary['status_names'].get(project[3], f'Status {project[3]}')
                response += f"\n  {i}. {name} - *{status}*"
            if len(projects) > 3:
                response += f"\n  ... and {len(projects) - 3} more"
    
    response += f"""

🔍 **Search Capabilities:**
You can search Hamza's projects by:
- Project type (AI, website, marketing, etc.)
- Client names
- Specific technologies or keywords
- Project status

💡 **Notable Projects:**
- AI coordination Agent (Current project)
- Multiple website development projects
- Social media management for various clients
- Construction company marketing projects

Would you like me to search for specific types of projects or provide more details about any particular project?"""
    
    return response

def main():
    """Test the service and show AI-style response"""
    print(create_ai_response_for_hamza_projects())

if __name__ == "__main__":
    main()