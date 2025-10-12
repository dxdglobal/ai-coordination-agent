"""
📊 Task Status Mapping Utility
Provides human-readable descriptions for task status codes
"""

class TaskStatusMapper:
    """🎯 Maps numerical task status codes to human-readable descriptions"""
    
    # Based on completion pattern analysis:
    # Status 1-4, 50+: 0% completion (various active states)
    # Status 5: 98% completion (completed tasks)
    
    STATUS_MAP = {
        1: {"name": "Not Started", "description": "Task has not been started yet", "emoji": "🔄"},
        2: {"name": "In Progress", "description": "Task is currently being worked on", "emoji": "⚡"},
        3: {"name": "Review", "description": "Task is under review", "emoji": "👀"},
        4: {"name": "Waiting", "description": "Task is waiting for dependencies or approval", "emoji": "⏳"},
        5: {"name": "Completed", "description": "Task has been completed successfully", "emoji": "✅"},
        50: {"name": "On Hold", "description": "Task is temporarily paused", "emoji": "⏸️"},
        51: {"name": "Cancelled", "description": "Task has been cancelled", "emoji": "❌"},
        52: {"name": "Archived", "description": "Task has been archived", "emoji": "📦"},
        53: {"name": "Blocked", "description": "Task is blocked by external factors", "emoji": "🚫"}
    }
    
    PRIORITY_MAP = {
        1: {"name": "Critical", "description": "Highest priority - urgent action required", "emoji": "🔴"},
        2: {"name": "High", "description": "High priority - important task", "emoji": "🟠"},
        3: {"name": "Medium", "description": "Medium priority - standard task", "emoji": "🟡"},
        4: {"name": "Low", "description": "Low priority - can be done later", "emoji": "🟢"},
        5: {"name": "Lowest", "description": "Lowest priority - when time permits", "emoji": "⚪"}
    }
    
    @classmethod
    def get_status_info(cls, status_code):
        """Get human-readable status information"""
        if status_code is None:
            return {"name": "Unknown", "description": "Status not set", "emoji": "❓"}
        
        status_code = int(status_code) if isinstance(status_code, str) else status_code
        return cls.STATUS_MAP.get(status_code, {
            "name": f"Status {status_code}", 
            "description": f"Custom status code {status_code}", 
            "emoji": "🔷"
        })
    
    @classmethod
    def get_priority_info(cls, priority_code):
        """Get human-readable priority information"""
        if priority_code is None:
            return {"name": "Normal", "description": "No priority set", "emoji": "⚪"}
        
        priority_code = int(priority_code) if isinstance(priority_code, str) else priority_code
        return cls.PRIORITY_MAP.get(priority_code, {
            "name": f"Priority {priority_code}", 
            "description": f"Custom priority level {priority_code}", 
            "emoji": "🔷"
        })
    
    @classmethod
    def format_status_distribution(cls, status_counts):
        """Format status distribution with human-readable names"""
        formatted = []
        total_tasks = sum(count for _, count in status_counts)
        
        for status_code, count in status_counts:
            status_info = cls.get_status_info(status_code)
            percentage = (count / total_tasks * 100) if total_tasks > 0 else 0
            
            formatted.append({
                'status_code': status_code,
                'status_name': status_info['name'],
                'emoji': status_info['emoji'],
                'count': count,
                'percentage': round(percentage, 1),
                'description': status_info['description']
            })
        
        return formatted
    
    @classmethod
    def get_status_summary(cls, status_counts):
        """Get a human-readable summary of task statuses"""
        formatted = cls.format_status_distribution(status_counts)
        
        summary_parts = []
        for item in formatted:
            summary_parts.append(
                f"{item['count']} {item['status_name']} tasks {item['emoji']}"
            )
        
        return ", ".join(summary_parts)