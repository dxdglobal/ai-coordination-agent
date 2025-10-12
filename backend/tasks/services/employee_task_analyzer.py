"""
Employee Task Analyzer

Advanced task analysis service for employee performance tracking and insights.
This service provides detailed analysis of employee tasks, performance metrics,
and actionable recommendations.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# Import CRM functions
from core.crm.real_crm_server import find_employee_by_name, get_database_connection
from tasks.utils.task_mapper import TaskStatusMapper, TaskPriorityMapper


@dataclass
class EmployeeTaskMetrics:
    """Data structure for employee task performance metrics"""
    employee_name: str
    employee_id: int
    total_tasks: int
    completed_tasks: int
    in_progress_tasks: int
    not_started_tasks: int
    awaiting_feedback_tasks: int
    overdue_tasks: int
    completion_rate: float
    avg_progress: Optional[float]
    recent_activity: List[Dict]
    performance_trend: str


class EmployeeTaskAnalyzer:
    """Advanced employee task analyzer with deep CRM integration"""
    
    def __init__(self):
        # In-memory cache for performance data
        self.metrics_cache = {}
        self.cache_duration = 300  # 5 minutes
        self.cache_expiry = {}
    
    def get_employee_tasks(self, employee_name: str) -> Dict[str, Any]:
        """Fetch comprehensive task data for an employee from the CRM database"""
        try:
            # Step 1: Find the employee by name to get their user ID
            employee = find_employee_by_name(employee_name)
            if not employee:
                return {
                    'success': False,
                    'error': f'Employee {employee_name} not found in the system',
                    'total_tasks': 0,
                    'tasks': []
                }
            
            employee_id = employee.get('staffid')
            print(f"🔍 Found employee {employee['full_name']} with ID: {employee_id}")
            
            # Step 2: Get database connection and search for all tasks assigned to this user
            connection = get_database_connection()
            if not connection:
                return {
                    'success': False,
                    'error': 'Could not connect to CRM database',
                    'total_tasks': 0,
                    'tasks': []
                }
            
            try:
                cursor = connection.cursor(dictionary=True)
                
                # Search for tasks in tbltasks table using employee ID via task assignment table
                task_query = """
                SELECT 
                    t.id as task_id,
                    t.name as task_name,
                    t.description,
                    t.status,
                    t.priority,
                    t.startdate,
                    t.duedate,
                    t.datefinished,
                    t.addedfrom,
                    t.dateadded,
                    t.rel_id,
                    t.rel_type,
                    p.name as project_name,
                    p.clientid,
                    c.company as client_name,
                    s.firstname,
                    s.lastname,
                    ta.staffid as assigned_staff_id
                FROM tbltasks t
                INNER JOIN tbltask_assigned ta ON t.id = ta.taskid
                LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
                LEFT JOIN tblclients c ON p.clientid = c.userid
                LEFT JOIN tblstaff s ON ta.staffid = s.staffid
                WHERE ta.staffid = %s
                ORDER BY t.dateadded DESC
                """
                
                cursor.execute(task_query, (employee_id,))
                tasks = cursor.fetchall()
                
                print(f"📊 Found {len(tasks)} tasks for employee {employee['full_name']}")
                
                # If no direct task assignments, also check project assignments
                if not tasks:
                    print("🔄 No direct task assignments found, checking project-level assignments...")
                    
                    project_query = """
                    SELECT DISTINCT
                        p.id as project_id,
                        p.name as project_name,
                        p.description,
                        p.status,
                        p.progress,
                        p.start_date,
                        p.deadline,
                        p.project_created as created_date,
                        c.company as client_name,
                        s.firstname,
                        s.lastname,
                        'project' as type
                    FROM tblprojects p
                    INNER JOIN tblproject_members pm ON p.id = pm.project_id
                    LEFT JOIN tblclients c ON p.clientid = c.userid
                    LEFT JOIN tblstaff s ON pm.staff_id = s.staffid
                    WHERE pm.staff_id = %s
                    ORDER BY p.project_created DESC
                    """
                    
                    cursor.execute(project_query, (employee_id,))
                    projects = cursor.fetchall()
                    
                    # Convert projects to task-like format
                    for project in projects:
                        task_dict = {
                            'task_id': f"project_{project['project_id']}",
                            'task_name': project.get('project_name', 'Untitled Project'),
                            'description': project.get('description', ''),
                            'status': project.get('status', 2),  # Project status
                            'priority': 2,  # Default priority
                            'startdate': project.get('start_date'),
                            'duedate': project.get('deadline'),
                            'datefinished': None,
                            'project_name': project.get('project_name'),
                            'client_name': project.get('client_name'),
                            'firstname': project.get('firstname'),
                            'lastname': project.get('lastname'),
                            'progress': project.get('progress', 0),
                            'type': 'project'
                        }
                        tasks.append(task_dict)
                
                cursor.close()
                connection.close()
                
                if not tasks:
                    return {
                        'success': False,
                        'error': f'No tasks or projects found for {employee["full_name"]}',
                        'total_tasks': 0,
                        'tasks': []
                    }
                
                # Convert tasks to standardized format and calculate metrics
                standardized_tasks = self._standardize_tasks(tasks)
                metrics = self._calculate_metrics(employee, standardized_tasks)
                
                return {
                    'employee_name': employee['full_name'],
                    'employee_id': employee_id,
                    'total_tasks': metrics.total_tasks,
                    'completed_tasks': metrics.completed_tasks,
                    'in_progress_tasks': metrics.in_progress_tasks,
                    'not_started_tasks': metrics.not_started_tasks,
                    'awaiting_feedback_tasks': metrics.awaiting_feedback_tasks,
                    'overdue_tasks': metrics.overdue_tasks,
                    'completion_rate': round(metrics.completion_rate, 2),
                    'avg_progress': metrics.avg_progress,
                    'tasks': standardized_tasks,
                    'success': True
                }
                
            except Exception as db_error:
                print(f"❌ Database query error: {db_error}")
                if connection:
                    connection.close()
                return {
                    'error': f'Database query failed: {str(db_error)}',
                    'success': False,
                    'employee_name': employee_name,
                    'total_tasks': 0,
                    'tasks': []
                }
            
        except Exception as e:
            print(f"❌ Error in get_employee_tasks: {e}")
            return {
                'error': f'Task retrieval failed: {str(e)}',
                'success': False,
                'employee_name': employee_name,
                'total_tasks': 0,
                'tasks': []
            }
    
    def _standardize_tasks(self, raw_tasks: List[Dict]) -> List[Dict]:
        """Convert raw CRM tasks to standardized format"""
        standardized = []
        
        for task in raw_tasks:
            standardized_task = {
                'id': task.get('task_id'),
                'title': task.get('task_name', 'Untitled Task'),
                'description': task.get('description', ''),
                'status': TaskStatusMapper.map_status(task.get('status', 1)),
                'priority': TaskPriorityMapper.map_priority(task.get('priority', 2)),
                'start_date': task.get('startdate'),
                'due_date': task.get('duedate'),
                'finished_date': task.get('datefinished'),
                'assignee': f"{task.get('firstname', '')} {task.get('lastname', '')}".strip(),
                'project_name': task.get('project_name', 'No Project'),
                'client_name': task.get('client_name', 'No Client'),
                'progress': task.get('progress', 0) if 'progress' in task else None,
                'type': task.get('type', 'task'),
                'created_date': task.get('dateadded'),
                'raw_status_id': task.get('status', 1),
                'raw_priority_id': task.get('priority', 2)
            }
            standardized.append(standardized_task)
        
        return standardized
    
    def _calculate_metrics(self, employee: Dict, tasks: List[Dict]) -> EmployeeTaskMetrics:
        """Calculate comprehensive performance metrics"""
        total_tasks = len(tasks)
        
        # Count tasks by status
        completed_tasks = len([t for t in tasks if TaskStatusMapper.is_completed(t.get('raw_status_id', 1))])
        in_progress_tasks = len([t for t in tasks if TaskStatusMapper.is_active(t.get('raw_status_id', 1))])
        not_started_tasks = len([t for t in tasks if t.get('status') == 'not_started'])
        awaiting_feedback_tasks = len([t for t in tasks if t.get('status') == 'awaiting_feedback'])
        
        # Calculate overdue tasks
        overdue_tasks = 0
        now = datetime.utcnow()
        for task in tasks:
            if task.get('due_date') and not TaskStatusMapper.is_completed(task.get('raw_status_id', 1)):
                try:
                    due_date = datetime.strptime(task['due_date'], '%Y-%m-%d') if isinstance(task['due_date'], str) else task['due_date']
                    if due_date < now:
                        overdue_tasks += 1
                except:
                    pass
        
        # Calculate completion rate
        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
        
        # Calculate average progress for projects
        project_tasks = [t for t in tasks if t.get('progress') is not None]
        avg_progress = sum(t.get('progress', 0) for t in project_tasks) / len(project_tasks) if project_tasks else 0
        
        # Recent activity (last 30 days)
        recent_activity = self._get_recent_activity(tasks)
        
        # Performance trend
        if completion_rate >= 80:
            trend = "Excellent"
        elif completion_rate >= 60:
            trend = "Good"
        elif completion_rate >= 40:
            trend = "Average"
        else:
            trend = "Needs Improvement"
        
        return EmployeeTaskMetrics(
            employee_name=employee['full_name'],
            employee_id=employee['staffid'],
            total_tasks=total_tasks,
            completed_tasks=completed_tasks,
            in_progress_tasks=in_progress_tasks,
            not_started_tasks=not_started_tasks,
            awaiting_feedback_tasks=awaiting_feedback_tasks,
            overdue_tasks=overdue_tasks,
            completion_rate=completion_rate,
            avg_progress=avg_progress,
            recent_activity=recent_activity,
            performance_trend=trend
        )
    
    def _get_recent_activity(self, tasks: List[Dict], days: int = 30) -> List[Dict]:
        """Get recent task activity"""
        cutoff_date = datetime.now() - timedelta(days=days)
        recent = []
        
        for task in tasks:
            if task.get('created_date'):
                try:
                    created_date = datetime.strptime(str(task['created_date']), '%Y-%m-%d %H:%M:%S')
                    if created_date >= cutoff_date:
                        recent.append({
                            'title': task.get('title'),
                            'status': task.get('status'),
                            'date': created_date.strftime('%Y-%m-%d'),
                            'project': task.get('project_name')
                        })
                except:
                    pass
        
        return recent[:10]  # Return last 10 activities
    
    def generate_detailed_analysis(self, employee_name: str) -> Dict[str, Any]:
        """Generate comprehensive task analysis for an employee"""
        task_data = self.get_employee_tasks(employee_name)
        
        if not task_data.get('success'):
            return task_data
        
        # Generate detailed analysis text
        analysis = self._generate_analysis_text(task_data)
        
        return {
            'success': True,
            'employee': task_data['employee_name'],
            'analysis': analysis,
            'metrics': {
                'total_tasks': task_data['total_tasks'],
                'completed_tasks': task_data['completed_tasks'],
                'in_progress_tasks': task_data['in_progress_tasks'],
                'completion_rate': task_data['completion_rate'],
                'overdue_tasks': task_data['overdue_tasks']
            },
            'tasks': task_data['tasks']
        }
    
    def _generate_analysis_text(self, task_data: Dict) -> str:
        """Generate detailed analysis text with task breakdowns"""
        employee = task_data['employee_name']
        completion_rate = task_data['completion_rate']
        total_tasks = task_data['total_tasks']
        overdue = task_data['overdue_tasks']
        in_progress = task_data['in_progress_tasks']
        tasks = task_data['tasks']
        
        analysis = f"📋 **Task Analysis for {employee}**\n\n"
        
        # Performance evaluation
        if completion_rate >= 80:
            analysis += f"✅ **Excellent Performance**: {completion_rate}% completion rate - outstanding work!\n"
        elif completion_rate >= 60:
            analysis += f"👍 **Good Performance**: {completion_rate}% completion rate - above average.\n"
        elif completion_rate >= 40:
            analysis += f"⚠️ **Needs Improvement**: {completion_rate}% completion rate - requires attention.\n"
        else:
            analysis += f"🚨 **Performance Concern**: {completion_rate}% completion rate - immediate support needed.\n"
        
        # Workload assessment
        if total_tasks > 20:
            analysis += f"📊 **Heavy Workload**: Managing {total_tasks} tasks - may need prioritization support.\n"
        elif total_tasks > 10:
            analysis += f"📊 **High Workload**: Currently managing {total_tasks} tasks.\n"
        elif total_tasks > 5:
            analysis += f"📊 **Moderate Workload**: Currently managing {total_tasks} tasks.\n"
        else:
            analysis += f"📊 **Light Workload**: Currently managing {total_tasks} tasks.\n"
        
        # Overdue status
        if overdue > 0:
            analysis += f"⏰ **Action Required**: {overdue} overdue task(s) need immediate attention.\n"
        else:
            analysis += f"✅ **On Track**: No overdue tasks.\n"
        
        # Current in-progress tasks
        in_progress_tasks = [t for t in tasks if t.get('status') == 'in_progress']
        if in_progress_tasks:
            analysis += f"\n🔄 **Current In-Progress Tasks ({len(in_progress_tasks)}):**\n"
            for i, task in enumerate(in_progress_tasks[:5], 1):
                task_name = task.get('title', 'Untitled Task')
                project_name = task.get('project_name', 'No Project')
                due_date = task.get('due_date', 'No due date')
                analysis += f"{i}. **{task_name}**\n"
                analysis += f"   - Project: {project_name}\n"
                analysis += f"   - Due Date: {due_date}\n"
                if task.get('description'):
                    desc = task['description'][:100] + "..." if len(task.get('description', '')) > 100 else task.get('description', '')
                    analysis += f"   - Description: {desc}\n"
                analysis += f"\n"
        
        # Recently completed tasks
        completed_tasks = [t for t in tasks if t.get('status') == 'done']
        if completed_tasks:
            analysis += f"✅ **Recently Completed Tasks ({len(completed_tasks)}):**\n"
            for i, task in enumerate(completed_tasks[:3], 1):
                task_name = task.get('title', 'Untitled Task')
                project_name = task.get('project_name', 'No Project')
                analysis += f"{i}. {task_name} (Project: {project_name})\n"
        
        # Recommendations
        analysis += f"\n💡 **Recommendations:**\n"
        if overdue > 0:
            analysis += f"• **Priority**: Complete {overdue} overdue task(s) immediately\n"
        if completion_rate < 70:
            analysis += f"• **Process**: Review task prioritization and time management strategies\n"
            analysis += f"• **Support**: Consider breaking down complex tasks into smaller components\n"
        if in_progress > 5:
            analysis += f"• **Focus**: Complete current tasks before taking on new assignments\n"
        if total_tasks > 20:
            analysis += f"• **Workload**: Consider workload rebalancing or additional team support\n"
        analysis += f"• **Communication**: Schedule regular check-ins to monitor progress\n"
        
        return analysis


# Global instance
employee_task_analyzer = EmployeeTaskAnalyzer()