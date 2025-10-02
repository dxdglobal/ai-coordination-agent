#!/usr/bin/env python3
"""
Hamza Projects Semantic Search Service
Uses OpenAI embeddings to analyze and search Hamza's 18 projects
"""
import os
import mysql.connector
from openai import OpenAI
import numpy as np
from dotenv import load_dotenv

load_dotenv()

class HamzaProjectsService:
    def __init__(self):
        self.openai_client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.hamza_staff_id = 188  # Hamza Haseeb's staff ID
        
    def get_db_connection(self):
        """Get database connection"""
        return mysql.connector.connect(
            host=os.getenv('DB_HOST'),
            user=os.getenv('DB_USER'),
            password=os.getenv('DB_PASSWORD'),
            database=os.getenv('DB_NAME')
        )
    
    def get_hamza_projects(self):
        """Get all projects assigned to Hamza"""
        conn = self.get_db_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT DISTINCT p.id, p.name, p.description, p.status, p.project_created,
                   p.progress, p.deadline, p.start_date, p.clientid
            FROM tblprojects p
            JOIN tblproject_members pm ON p.id = pm.project_id  
            WHERE pm.staff_id = %s
            ORDER BY p.project_created DESC
        """, (self.hamza_staff_id,))
        
        projects = cursor.fetchall()
        conn.close()
        return projects
    
    def create_project_embedding(self, project_name, project_description):
        """Create OpenAI embedding for project content"""
        # Combine name and description for better context
        content = f"Project: {project_name}\nDescription: {project_description or ''}"
        
        try:
            response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=content
            )
            return response.data[0].embedding
        except Exception as e:
            print(f"Error creating embedding: {e}")
            return None
    
    def semantic_search_hamza_projects(self, query, limit=18):
        """Search Hamza's projects using semantic similarity"""
        print(f"🔍 Searching Hamza's projects for: '{query}'")
        
        # Get query embedding
        try:
            query_response = self.openai_client.embeddings.create(
                model="text-embedding-ada-002",
                input=query
            )
            query_embedding = np.array(query_response.data[0].embedding)
        except Exception as e:
            print(f"Error creating query embedding: {e}")
            return []
        
        # Get all Hamza's projects
        projects = self.get_hamza_projects()
        project_similarities = []
        
        for project in projects:
            pid, name, description, status, created, progress, deadline, start_date, clientid = project
            
            # Create embedding for this project
            project_embedding = self.create_project_embedding(name, description)
            if project_embedding is None:
                continue
                
            # Calculate similarity
            project_embedding = np.array(project_embedding)
            similarity = np.dot(query_embedding, project_embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(project_embedding)
            )
            
            project_similarities.append({
                'id': pid,
                'name': name,
                'description': description,
                'status': status,
                'created': created,
                'progress': progress,
                'similarity': similarity,
                'clientid': clientid
            })
        
        # Sort by similarity (highest first)
        project_similarities.sort(key=lambda x: x['similarity'], reverse=True)
        return project_similarities[:limit]
    
    def analyze_hamza_projects(self):
        """Get comprehensive analysis of Hamza's projects"""
        projects = self.get_hamza_projects()
        
        # Status mapping
        status_names = {1: 'Not Started', 2: 'Active/In Progress', 3: 'On Hold', 4: 'Completed', 5: 'Cancelled'}
        
        analysis = {
            'total_projects': len(projects),
            'active_projects': len([p for p in projects if p[3] == 2]),
            'completed_projects': len([p for p in projects if p[3] == 4]),
            'project_breakdown': [],
            'status_summary': {}
        }
        
        # Count by status
        for project in projects:
            status = project[3]
            if status not in analysis['status_summary']:
                analysis['status_summary'][status] = 0
            analysis['status_summary'][status] += 1
        
        # Format project details
        for project in projects:
            pid, name, description, status, created, progress, deadline, start_date, clientid = project
            analysis['project_breakdown'].append({
                'id': pid,
                'name': name,
                'status': status_names.get(status, f'Status {status}'),
                'progress': progress,
                'created': created.strftime('%Y-%m-%d') if created else None,
                'client_id': clientid
            })
        
        return analysis

def main():
    """Test the Hamza projects service"""
    service = HamzaProjectsService()
    
    print("🎯 Hamza's Projects Analysis")
    print("=" * 50)
    
    # Get comprehensive analysis
    analysis = service.analyze_hamza_projects()
    print(f"📊 Total Projects: {analysis['total_projects']}")
    print(f"📈 Active Projects: {analysis['active_projects']}")
    print(f"✅ Completed Projects: {analysis['completed_projects']}")
    
    print("\n📋 All Hamza's Projects:")
    for i, project in enumerate(analysis['project_breakdown'], 1):
        print(f"  {i:2}. {project['name'][:60]}... | {project['status']} | Progress: {project['progress']}%")
    
    print("\n🔍 Testing Semantic Search:")
    
    # Test different queries
    test_queries = [
        "AI and automation projects",
        "website development work", 
        "social media and marketing",
        "construction and real estate projects"
    ]
    
    for query in test_queries:
        print(f"\n🎯 Query: '{query}'")
        results = service.semantic_search_hamza_projects(query, limit=5)
        for i, result in enumerate(results, 1):
            print(f"  {i}. {result['name'][:50]}... (similarity: {result['similarity']:.3f})")

if __name__ == "__main__":
    main()