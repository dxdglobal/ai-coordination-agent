"""
Task Status and Priority Mappers

Utilities for mapping CRM task statuses and priorities to standardized formats.
"""

class TaskStatusMapper:
    """Maps CRM task status IDs to readable status strings"""
    
    STATUS_MAP = {
        1: 'not_started',
        2: 'in_progress',
        3: 'testing',
        4: 'awaiting_feedback',
        5: 'done'
    }
    
    @classmethod
    def map_status(cls, status_id: int) -> str:
        """Map CRM task status ID to readable status"""
        return cls.STATUS_MAP.get(status_id, 'in_progress')
    
    @classmethod
    def get_all_statuses(cls) -> dict:
        """Get all available status mappings"""
        return cls.STATUS_MAP.copy()
    
    @classmethod
    def is_completed(cls, status_id: int) -> bool:
        """Check if a status represents a completed task"""
        return cls.map_status(status_id) == 'done'
    
    @classmethod
    def is_active(cls, status_id: int) -> bool:
        """Check if a status represents an active/in-progress task"""
        return cls.map_status(status_id) == 'in_progress'


class TaskPriorityMapper:
    """Maps CRM task priority IDs to readable priority strings"""
    
    PRIORITY_MAP = {
        1: 'low',
        2: 'medium',
        3: 'high',
        4: 'urgent'
    }
    
    @classmethod
    def map_priority(cls, priority_id: int) -> str:
        """Map CRM priority ID to readable priority"""
        return cls.PRIORITY_MAP.get(priority_id, 'medium')
    
    @classmethod
    def get_all_priorities(cls) -> dict:
        """Get all available priority mappings"""
        return cls.PRIORITY_MAP.copy()
    
    @classmethod
    def get_priority_weight(cls, priority_id: int) -> int:
        """Get numeric weight for priority (higher = more urgent)"""
        weights = {1: 1, 2: 2, 3: 3, 4: 4}
        return weights.get(priority_id, 2)


class ProjectStatusMapper:
    """Maps CRM project status IDs to readable status strings"""
    
    STATUS_MAP = {
        1: 'not_started',
        2: 'in_progress',
        3: 'on_hold',
        4: 'cancelled',
        5: 'done'
    }
    
    @classmethod
    def map_status(cls, status_id: int) -> str:
        """Map CRM project status ID to readable status"""
        return cls.STATUS_MAP.get(status_id, 'in_progress')
    
    @classmethod
    def get_all_statuses(cls) -> dict:
        """Get all available status mappings"""
        return cls.STATUS_MAP.copy()