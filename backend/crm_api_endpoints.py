"""
CRM API Endpoints - Task 1.2
============================

Complete implementation of all 5 required CRM API endpoints:
- Projects: Project management and lifecycle
- Tasks: Task creation, assignment, and tracking
- Users: User management and authentication
- Clients: Client relationship management
- Comments: Communication and collaboration

Each endpoint supports full CRUD operations with validation and error handling.

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

from typing import Dict, List, Optional, Any, Union
from datetime import datetime
import logging
from dataclasses import dataclass, asdict
from crm_api_service import CRMAPIClient, CRMConfig

logger = logging.getLogger(__name__)

@dataclass
class Project:
    """Project data model"""
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    status: str = "active"  # active, completed, on_hold, cancelled
    priority: str = "medium"  # low, medium, high, critical
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    budget: Optional[float] = None
    client_id: Optional[int] = None
    manager_id: Optional[int] = None
    team_members: List[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.team_members is None:
            self.team_members = []

@dataclass
class Task:
    """Task data model"""
    id: Optional[int] = None
    title: str = ""
    description: str = ""
    status: str = "todo"  # todo, in_progress, review, done, cancelled
    priority: str = "medium"  # low, medium, high, critical
    project_id: Optional[int] = None
    assignee_id: Optional[int] = None
    reporter_id: Optional[int] = None
    due_date: Optional[str] = None
    estimated_hours: Optional[float] = None
    actual_hours: Optional[float] = None
    tags: List[str] = None
    dependencies: List[int] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    def __post_init__(self):
        if self.tags is None:
            self.tags = []
        if self.dependencies is None:
            self.dependencies = []

@dataclass
class User:
    """User data model"""
    id: Optional[int] = None
    username: str = ""
    email: str = ""
    first_name: str = ""
    last_name: str = ""
    role: str = "user"  # admin, manager, user, client
    department: str = ""
    position: str = ""
    phone: str = ""
    is_active: bool = True
    last_login: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class Client:
    """Client data model"""
    id: Optional[int] = None
    name: str = ""
    company: str = ""
    email: str = ""
    phone: str = ""
    address: str = ""
    industry: str = ""
    status: str = "active"  # active, inactive, prospect, former
    contact_person: str = ""
    notes: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

@dataclass
class Comment:
    """Comment data model"""
    id: Optional[int] = None
    content: str = ""
    author_id: Optional[int] = None
    entity_type: str = ""  # project, task, client, user
    entity_id: Optional[int] = None
    parent_id: Optional[int] = None  # For nested comments
    is_private: bool = False
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ProjectsAPI:
    """Projects API endpoint handler"""
    
    def __init__(self, client: CRMAPIClient):
        self.client = client
        self.endpoint_base = "projects"
    
    def get_all(self, 
                status: Optional[str] = None,
                client_id: Optional[int] = None,
                manager_id: Optional[int] = None,
                page: int = 1,
                per_page: int = 50) -> Dict[str, Any]:
        """Get all projects with optional filtering"""
        params = {"page": page, "per_page": per_page}
        
        if status:
            params["status"] = status
        if client_id:
            params["client_id"] = client_id
        if manager_id:
            params["manager_id"] = manager_id
        
        try:
            response = self.client.get(self.endpoint_base, params=params)
            logger.info(f"Retrieved {len(response.get('data', []))} projects")
            return response
        except Exception as e:
            logger.error(f"Failed to get projects: {e}")
            raise
    
    def get_by_id(self, project_id: int) -> Project:
        """Get project by ID"""
        try:
            response = self.client.get(f"{self.endpoint_base}/{project_id}")
            project_data = response.get("data", response)
            logger.info(f"Retrieved project {project_id}")
            return Project(**project_data)
        except Exception as e:
            logger.error(f"Failed to get project {project_id}: {e}")
            raise
    
    def create(self, project: Project) -> Project:
        """Create new project"""
        project_data = asdict(project)
        # Remove None values and id for creation
        project_data = {k: v for k, v in project_data.items() if v is not None and k != 'id'}
        
        try:
            response = self.client.post(self.endpoint_base, project_data)
            created_project = response.get("data", response)
            logger.info(f"Created project: {created_project.get('name')}")
            return Project(**created_project)
        except Exception as e:
            logger.error(f"Failed to create project: {e}")
            raise
    
    def update(self, project_id: int, project: Project) -> Project:
        """Update existing project"""
        project_data = asdict(project)
        # Remove None values
        project_data = {k: v for k, v in project_data.items() if v is not None}
        
        try:
            response = self.client.put(f"{self.endpoint_base}/{project_id}", project_data)
            updated_project = response.get("data", response)
            logger.info(f"Updated project {project_id}")
            return Project(**updated_project)
        except Exception as e:
            logger.error(f"Failed to update project {project_id}: {e}")
            raise
    
    def delete(self, project_id: int) -> bool:
        """Delete project"""
        try:
            success = self.client.delete(f"{self.endpoint_base}/{project_id}")
            if success:
                logger.info(f"Deleted project {project_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete project {project_id}: {e}")
            raise
    
    def get_project_tasks(self, project_id: int) -> List[Task]:
        """Get all tasks for a project"""
        try:
            response = self.client.get(f"{self.endpoint_base}/{project_id}/tasks")
            tasks_data = response.get("data", [])
            tasks = [Task(**task_data) for task_data in tasks_data]
            logger.info(f"Retrieved {len(tasks)} tasks for project {project_id}")
            return tasks
        except Exception as e:
            logger.error(f"Failed to get tasks for project {project_id}: {e}")
            raise

class TasksAPI:
    """Tasks API endpoint handler"""
    
    def __init__(self, client: CRMAPIClient):
        self.client = client
        self.endpoint_base = "tasks"
    
    def get_all(self,
                status: Optional[str] = None,
                project_id: Optional[int] = None,
                assignee_id: Optional[int] = None,
                priority: Optional[str] = None,
                page: int = 1,
                per_page: int = 50) -> Dict[str, Any]:
        """Get all tasks with optional filtering"""
        params = {"page": page, "per_page": per_page}
        
        if status:
            params["status"] = status
        if project_id:
            params["project_id"] = project_id
        if assignee_id:
            params["assignee_id"] = assignee_id
        if priority:
            params["priority"] = priority
        
        try:
            response = self.client.get(self.endpoint_base, params=params)
            logger.info(f"Retrieved {len(response.get('data', []))} tasks")
            return response
        except Exception as e:
            logger.error(f"Failed to get tasks: {e}")
            raise
    
    def get_by_id(self, task_id: int) -> Task:
        """Get task by ID"""
        try:
            response = self.client.get(f"{self.endpoint_base}/{task_id}")
            task_data = response.get("data", response)
            logger.info(f"Retrieved task {task_id}")
            return Task(**task_data)
        except Exception as e:
            logger.error(f"Failed to get task {task_id}: {e}")
            raise
    
    def create(self, task: Task) -> Task:
        """Create new task"""
        task_data = asdict(task)
        # Remove None values and id for creation
        task_data = {k: v for k, v in task_data.items() if v is not None and k != 'id'}
        
        try:
            response = self.client.post(self.endpoint_base, task_data)
            created_task = response.get("data", response)
            logger.info(f"Created task: {created_task.get('title')}")
            return Task(**created_task)
        except Exception as e:
            logger.error(f"Failed to create task: {e}")
            raise
    
    def update(self, task_id: int, task: Task) -> Task:
        """Update existing task"""
        task_data = asdict(task)
        # Remove None values
        task_data = {k: v for k, v in task_data.items() if v is not None}
        
        try:
            response = self.client.put(f"{self.endpoint_base}/{task_id}", task_data)
            updated_task = response.get("data", response)
            logger.info(f"Updated task {task_id}")
            return Task(**updated_task)
        except Exception as e:
            logger.error(f"Failed to update task {task_id}: {e}")
            raise
    
    def delete(self, task_id: int) -> bool:
        """Delete task"""
        try:
            success = self.client.delete(f"{self.endpoint_base}/{task_id}")
            if success:
                logger.info(f"Deleted task {task_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete task {task_id}: {e}")
            raise
    
    def assign_task(self, task_id: int, assignee_id: int) -> Task:
        """Assign task to user"""
        try:
            response = self.client.patch(f"{self.endpoint_base}/{task_id}/assign", 
                                       {"assignee_id": assignee_id})
            updated_task = response.get("data", response)
            logger.info(f"Assigned task {task_id} to user {assignee_id}")
            return Task(**updated_task)
        except Exception as e:
            logger.error(f"Failed to assign task {task_id}: {e}")
            raise
    
    def update_status(self, task_id: int, status: str) -> Task:
        """Update task status"""
        try:
            response = self.client.patch(f"{self.endpoint_base}/{task_id}/status", 
                                       {"status": status})
            updated_task = response.get("data", response)
            logger.info(f"Updated task {task_id} status to {status}")
            return Task(**updated_task)
        except Exception as e:
            logger.error(f"Failed to update task {task_id} status: {e}")
            raise

class UsersAPI:
    """Users API endpoint handler"""
    
    def __init__(self, client: CRMAPIClient):
        self.client = client
        self.endpoint_base = "users"
    
    def get_all(self,
                role: Optional[str] = None,
                department: Optional[str] = None,
                is_active: Optional[bool] = None,
                page: int = 1,
                per_page: int = 50) -> Dict[str, Any]:
        """Get all users with optional filtering"""
        params = {"page": page, "per_page": per_page}
        
        if role:
            params["role"] = role
        if department:
            params["department"] = department
        if is_active is not None:
            params["is_active"] = is_active
        
        try:
            response = self.client.get(self.endpoint_base, params=params)
            logger.info(f"Retrieved {len(response.get('data', []))} users")
            return response
        except Exception as e:
            logger.error(f"Failed to get users: {e}")
            raise
    
    def get_by_id(self, user_id: int) -> User:
        """Get user by ID"""
        try:
            response = self.client.get(f"{self.endpoint_base}/{user_id}")
            user_data = response.get("data", response)
            logger.info(f"Retrieved user {user_id}")
            return User(**user_data)
        except Exception as e:
            logger.error(f"Failed to get user {user_id}: {e}")
            raise
    
    def create(self, user: User) -> User:
        """Create new user"""
        user_data = asdict(user)
        # Remove None values and id for creation
        user_data = {k: v for k, v in user_data.items() if v is not None and k != 'id'}
        
        try:
            response = self.client.post(self.endpoint_base, user_data)
            created_user = response.get("data", response)
            logger.info(f"Created user: {created_user.get('username')}")
            return User(**created_user)
        except Exception as e:
            logger.error(f"Failed to create user: {e}")
            raise
    
    def update(self, user_id: int, user: User) -> User:
        """Update existing user"""
        user_data = asdict(user)
        # Remove None values
        user_data = {k: v for k, v in user_data.items() if v is not None}
        
        try:
            response = self.client.put(f"{self.endpoint_base}/{user_id}", user_data)
            updated_user = response.get("data", response)
            logger.info(f"Updated user {user_id}")
            return User(**updated_user)
        except Exception as e:
            logger.error(f"Failed to update user {user_id}: {e}")
            raise
    
    def delete(self, user_id: int) -> bool:
        """Delete user"""
        try:
            success = self.client.delete(f"{self.endpoint_base}/{user_id}")
            if success:
                logger.info(f"Deleted user {user_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete user {user_id}: {e}")
            raise
    
    def get_user_tasks(self, user_id: int) -> List[Task]:
        """Get all tasks assigned to user"""
        try:
            response = self.client.get(f"{self.endpoint_base}/{user_id}/tasks")
            tasks_data = response.get("data", [])
            tasks = [Task(**task_data) for task_data in tasks_data]
            logger.info(f"Retrieved {len(tasks)} tasks for user {user_id}")
            return tasks
        except Exception as e:
            logger.error(f"Failed to get tasks for user {user_id}: {e}")
            raise
    
    def get_user_projects(self, user_id: int) -> List[Project]:
        """Get all projects for user"""
        try:
            response = self.client.get(f"{self.endpoint_base}/{user_id}/projects")
            projects_data = response.get("data", [])
            projects = [Project(**project_data) for project_data in projects_data]
            logger.info(f"Retrieved {len(projects)} projects for user {user_id}")
            return projects
        except Exception as e:
            logger.error(f"Failed to get projects for user {user_id}: {e}")
            raise

class ClientsAPI:
    """Clients API endpoint handler"""
    
    def __init__(self, client: CRMAPIClient):
        self.client = client
        self.endpoint_base = "clients"
    
    def get_all(self,
                status: Optional[str] = None,
                industry: Optional[str] = None,
                page: int = 1,
                per_page: int = 50) -> Dict[str, Any]:
        """Get all clients with optional filtering"""
        params = {"page": page, "per_page": per_page}
        
        if status:
            params["status"] = status
        if industry:
            params["industry"] = industry
        
        try:
            response = self.client.get(self.endpoint_base, params=params)
            logger.info(f"Retrieved {len(response.get('data', []))} clients")
            return response
        except Exception as e:
            logger.error(f"Failed to get clients: {e}")
            raise
    
    def get_by_id(self, client_id: int) -> Client:
        """Get client by ID"""
        try:
            response = self.client.get(f"{self.endpoint_base}/{client_id}")
            client_data = response.get("data", response)
            logger.info(f"Retrieved client {client_id}")
            return Client(**client_data)
        except Exception as e:
            logger.error(f"Failed to get client {client_id}: {e}")
            raise
    
    def create(self, client: Client) -> Client:
        """Create new client"""
        client_data = asdict(client)
        # Remove None values and id for creation
        client_data = {k: v for k, v in client_data.items() if v is not None and k != 'id'}
        
        try:
            response = self.client.post(self.endpoint_base, client_data)
            created_client = response.get("data", response)
            logger.info(f"Created client: {created_client.get('name')}")
            return Client(**created_client)
        except Exception as e:
            logger.error(f"Failed to create client: {e}")
            raise
    
    def update(self, client_id: int, client: Client) -> Client:
        """Update existing client"""
        client_data = asdict(client)
        # Remove None values
        client_data = {k: v for k, v in client_data.items() if v is not None}
        
        try:
            response = self.client.put(f"{self.endpoint_base}/{client_id}", client_data)
            updated_client = response.get("data", response)
            logger.info(f"Updated client {client_id}")
            return Client(**updated_client)
        except Exception as e:
            logger.error(f"Failed to update client {client_id}: {e}")
            raise
    
    def delete(self, client_id: int) -> bool:
        """Delete client"""
        try:
            success = self.client.delete(f"{self.endpoint_base}/{client_id}")
            if success:
                logger.info(f"Deleted client {client_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete client {client_id}: {e}")
            raise
    
    def get_client_projects(self, client_id: int) -> List[Project]:
        """Get all projects for client"""
        try:
            response = self.client.get(f"{self.endpoint_base}/{client_id}/projects")
            projects_data = response.get("data", [])
            projects = [Project(**project_data) for project_data in projects_data]
            logger.info(f"Retrieved {len(projects)} projects for client {client_id}")
            return projects
        except Exception as e:
            logger.error(f"Failed to get projects for client {client_id}: {e}")
            raise

class CommentsAPI:
    """Comments API endpoint handler"""
    
    def __init__(self, client: CRMAPIClient):
        self.client = client
        self.endpoint_base = "comments"
    
    def get_all(self,
                entity_type: Optional[str] = None,
                entity_id: Optional[int] = None,
                author_id: Optional[int] = None,
                page: int = 1,
                per_page: int = 50) -> Dict[str, Any]:
        """Get all comments with optional filtering"""
        params = {"page": page, "per_page": per_page}
        
        if entity_type:
            params["entity_type"] = entity_type
        if entity_id:
            params["entity_id"] = entity_id
        if author_id:
            params["author_id"] = author_id
        
        try:
            response = self.client.get(self.endpoint_base, params=params)
            logger.info(f"Retrieved {len(response.get('data', []))} comments")
            return response
        except Exception as e:
            logger.error(f"Failed to get comments: {e}")
            raise
    
    def get_by_id(self, comment_id: int) -> Comment:
        """Get comment by ID"""
        try:
            response = self.client.get(f"{self.endpoint_base}/{comment_id}")
            comment_data = response.get("data", response)
            logger.info(f"Retrieved comment {comment_id}")
            return Comment(**comment_data)
        except Exception as e:
            logger.error(f"Failed to get comment {comment_id}: {e}")
            raise
    
    def create(self, comment: Comment) -> Comment:
        """Create new comment"""
        comment_data = asdict(comment)
        # Remove None values and id for creation
        comment_data = {k: v for k, v in comment_data.items() if v is not None and k != 'id'}
        
        try:
            response = self.client.post(self.endpoint_base, comment_data)
            created_comment = response.get("data", response)
            logger.info(f"Created comment on {comment.entity_type} {comment.entity_id}")
            return Comment(**created_comment)
        except Exception as e:
            logger.error(f"Failed to create comment: {e}")
            raise
    
    def update(self, comment_id: int, comment: Comment) -> Comment:
        """Update existing comment"""
        comment_data = asdict(comment)
        # Remove None values
        comment_data = {k: v for k, v in comment_data.items() if v is not None}
        
        try:
            response = self.client.put(f"{self.endpoint_base}/{comment_id}", comment_data)
            updated_comment = response.get("data", response)
            logger.info(f"Updated comment {comment_id}")
            return Comment(**updated_comment)
        except Exception as e:
            logger.error(f"Failed to update comment {comment_id}: {e}")
            raise
    
    def delete(self, comment_id: int) -> bool:
        """Delete comment"""
        try:
            success = self.client.delete(f"{self.endpoint_base}/{comment_id}")
            if success:
                logger.info(f"Deleted comment {comment_id}")
            return success
        except Exception as e:
            logger.error(f"Failed to delete comment {comment_id}: {e}")
            raise
    
    def get_entity_comments(self, entity_type: str, entity_id: int) -> List[Comment]:
        """Get all comments for a specific entity"""
        try:
            params = {"entity_type": entity_type, "entity_id": entity_id}
            response = self.client.get(self.endpoint_base, params=params)
            comments_data = response.get("data", [])
            comments = [Comment(**comment_data) for comment_data in comments_data]
            logger.info(f"Retrieved {len(comments)} comments for {entity_type} {entity_id}")
            return comments
        except Exception as e:
            logger.error(f"Failed to get comments for {entity_type} {entity_id}: {e}")
            raise

# Main CRM API Manager
class CRMAPIManager:
    """Main CRM API Manager combining all endpoints"""
    
    def __init__(self, config: CRMConfig):
        self.client = CRMAPIClient(config)
        
        # Initialize all API endpoints
        self.projects = ProjectsAPI(self.client)
        self.tasks = TasksAPI(self.client)
        self.users = UsersAPI(self.client)
        self.clients = ClientsAPI(self.client)
        self.comments = CommentsAPI(self.client)
        
        logger.info("CRM API Manager initialized with all endpoints")
    
    def health_check(self) -> Dict[str, Any]:
        """Perform health check on all API endpoints"""
        results = {}
        
        try:
            # Test basic connectivity
            health = self.client.health_check()
            results["api_health"] = health
            
            # Test each endpoint
            endpoints = ["projects", "tasks", "users", "clients", "comments"]
            for endpoint in endpoints:
                try:
                    # Test GET request with minimal parameters
                    test_response = self.client.get(endpoint, params={"page": 1, "per_page": 1})
                    results[f"{endpoint}_status"] = "healthy"
                except Exception as e:
                    results[f"{endpoint}_status"] = f"error: {str(e)}"
            
            logger.info("Health check completed for all endpoints")
            return results
            
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            results["error"] = str(e)
            return results

# Example usage
if __name__ == "__main__":
    # Example configuration
    config = CRMConfig(
        base_url="https://api.crm.example.com",
        api_version="v1",
        authentication_type="jwt",
        username="api_user",
        password="api_password"
    )
    
    # Initialize API manager
    api = CRMAPIManager(config)
    
    try:
        # Health check
        health = api.health_check()
        print(f"Health check results: {health}")
        
        # Example: Create a new project
        new_project = Project(
            name="Sample Project",
            description="A sample project for testing",
            status="active",
            priority="high"
        )
        
        created_project = api.projects.create(new_project)
        print(f"Created project: {created_project.name} (ID: {created_project.id})")
        
        # Example: Create a task for the project
        new_task = Task(
            title="Sample Task",
            description="A sample task for the project",
            project_id=created_project.id,
            status="todo",
            priority="medium"
        )
        
        created_task = api.tasks.create(new_task)
        print(f"Created task: {created_task.title} (ID: {created_task.id})")
        
    except Exception as e:
        print(f"Error: {e}")