# Tasks Module

A comprehensive task management module for the AI Coordination Agent system.

## 🚀 Overview

The Tasks module provides advanced task management capabilities including:
- **Employee Task Analysis** - Deep analysis of employee performance and task metrics
- **Task Status Management** - Track and update task statuses across the system  
- **Performance Analytics** - Generate insights and recommendations
- **CRM Integration** - Direct integration with CRM database for real-time data

## 📁 Module Structure

```
tasks/
├── __init__.py                    # Module initialization
├── README.md                      # This file
├── services/                      # Business logic services
│   ├── __init__.py
│   ├── employee_task_analyzer.py  # Employee performance analysis
│   └── task_service.py           # Core task operations
├── routes/                        # API endpoints
│   ├── __init__.py
│   └── task_routes.py            # REST API routes
├── models/                        # Data models (future)
│   └── __init__.py
├── schemas/                       # Data validation schemas (future)
│   └── __init__.py
└── utils/                         # Utility functions
    ├── __init__.py
    └── task_mapper.py            # Status/priority mappers
```

## 🔧 Core Services

### EmployeeTaskAnalyzer
Advanced service for employee task performance analysis:
- **Deep CRM Integration** - Searches actual task assignments via `tbltask_assigned` table
- **Comprehensive Metrics** - Calculates completion rates, overdue tasks, workload analysis
- **Detailed Analysis** - Generates human-readable performance reports with recommendations

### TaskService  
Core task management operations:
- **Task CRUD** - Get, update, and manage individual tasks
- **Status Management** - Update task statuses with proper validation
- **Filtering** - Get tasks by status, overdue tasks, etc.

### TaskStatusMapper & TaskPriorityMapper
Utility classes for mapping CRM status/priority IDs to readable formats:
- **Status Mapping**: `1=not_started, 2=in_progress, 3=testing, 4=awaiting_feedback, 5=done`
- **Priority Mapping**: `1=low, 2=medium, 3=high, 4=urgent`

## 🌐 API Endpoints

### Employee Analysis
- `GET /tasks/employee/{name}/analysis` - Get comprehensive task analysis
- `GET /tasks/employee/{name}/tasks` - Get all tasks for employee  
- `GET /tasks/employee/{name}/current` - Get current in-progress tasks

### Task Management
- `GET /tasks/{id}` - Get specific task details
- `PUT /tasks/{id}/status` - Update task status
- `GET /tasks/status/{status}` - Get tasks by status
- `GET /tasks/overdue` - Get all overdue tasks

### Analytics
- `GET /tasks/analytics/summary` - Get overall task analytics

## 💡 Usage Examples

### Get Employee Analysis
```python
from tasks.services.employee_task_analyzer import employee_task_analyzer

# Get comprehensive analysis
result = employee_task_analyzer.generate_detailed_analysis('Nawaz')
print(result['analysis'])  # Human-readable analysis
print(result['metrics'])   # Performance metrics
```

### Check Task Status
```python
from tasks.services.task_service import task_service

# Get overdue tasks
overdue = task_service.get_overdue_tasks()
print(f"Found {overdue['total']} overdue tasks")

# Update task status
result = task_service.update_task_status(123, 'done')
```

### Use Status Mappers
```python
from tasks.utils.task_mapper import TaskStatusMapper

# Map CRM status ID to readable format
status = TaskStatusMapper.map_status(2)  # Returns 'in_progress'
is_completed = TaskStatusMapper.is_completed(5)  # Returns True
```

## 🔍 Key Features

### 1. **Deep CRM Integration**
- Directly queries CRM `tbltasks` and `tbltask_assigned` tables
- Handles both direct task assignments and project-level assignments
- Real-time data with no caching delays

### 2. **Intelligent Analysis**
- Calculates completion rates, workload metrics, overdue tracking
- Generates actionable recommendations based on performance data
- Provides detailed breakdowns of current and completed tasks

### 3. **Flexible Task Management**
- Support for multiple task statuses and priorities
- Easy status updates with proper validation
- Overdue task detection with days calculation

### 4. **Performance Analytics**
- Employee performance trending
- Workload analysis and recommendations  
- Recent activity tracking

## 🚀 Integration

To use the tasks module in your application:

```python
# Import the blueprint and register it
from tasks.routes.task_routes import task_bp

app.register_blueprint(task_bp, url_prefix='/tasks')

# Use services directly
from tasks.services.employee_task_analyzer import employee_task_analyzer
from tasks.services.task_service import task_service
```

## 🔧 Configuration

The module automatically connects to the CRM database using the existing `core.crm.real_crm_server` connection manager. No additional configuration required.

## 📊 Example API Response

```json
{
  "success": true,
  "employee": "Nawaz Muhammed", 
  "analysis": "📋 **Task Analysis for Nawaz Muhammed**\n\n🚨 **Performance Concern**: 37.93% completion rate...",
  "metrics": {
    "total_tasks": 29,
    "completed_tasks": 11,
    "in_progress_tasks": 1,
    "completion_rate": 37.93,
    "overdue_tasks": 0
  },
  "tasks": [...]
}
```

This module provides a solid foundation for task management operations while maintaining clean separation of concerns and easy extensibility.