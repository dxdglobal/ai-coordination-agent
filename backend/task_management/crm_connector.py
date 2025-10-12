"""
CRM Connector - Interface to existing CRM database
Handles staff table queries and employee data management
"""

import pymysql
from typing import List, Dict, Optional, Any
import time
from .config import Config
from .logger import get_logger

logger = get_logger()

class CRMConnector:
    """Connector for CRM database operations"""
    
    def __init__(self):
        self.config = Config.DB_CONFIG
        self.connection = None
        self._employee_cache = {}
        self._cache_timestamp = None
        
    def _get_connection(self):
        """Get database connection with retry logic"""
        if self.connection is None or not self._is_connection_alive():
            try:
                self.connection = pymysql.connect(**self.config)
                logger.info("Database connection established")
            except Exception as e:
                logger.error("Failed to connect to database", error=e)
                raise
        return self.connection
    
    def _is_connection_alive(self) -> bool:
        """Check if database connection is alive"""
        try:
            if self.connection:
                self.connection.ping(reconnect=True)
                return True
        except:
            pass
        return False
    
    def get_all_employees(self, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get all active employees from staff table
        Returns: List of employee dictionaries with id, firstname, lastname, email
        """
        start_time = time.time()
        
        # Check cache first
        if not force_refresh and self._is_cache_valid():
            logger.debug("Returning cached employee data")
            return list(self._employee_cache.values())
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            query = """
                SELECT 
                    staffid as id,
                    firstname,
                    lastname,
                    email,
                    CONCAT(firstname, ' ', lastname) as full_name
                FROM tblstaff 
                WHERE active = 1
                ORDER BY firstname, lastname
            """
            
            cursor.execute(query)
            employees = cursor.fetchall()
            
            # Update cache
            self._employee_cache = {emp['id']: emp for emp in employees}
            self._cache_timestamp = time.time()
            
            execution_time = time.time() - start_time
            logger.log_db_operation('SELECT', 'tblstaff', True, execution_time, len(employees))
            
            return employees
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.log_db_operation('SELECT', 'tblstaff', False, execution_time)
            logger.error("Failed to fetch employees", error=e)
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def find_employee_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """
        Find employee by partial name match
        Args:
            name: Employee name (can be partial)
        Returns: Employee dictionary or None
        """
        employees = self.get_all_employees()
        name_lower = name.lower().strip()
        
        # Exact full name match
        for emp in employees:
            if emp['full_name'].lower() == name_lower:
                logger.debug(f"Found exact match for '{name}': {emp['full_name']}")
                return emp
        
        # Partial name match (firstname or lastname)
        for emp in employees:
            if (name_lower in emp['firstname'].lower() or 
                name_lower in emp['lastname'].lower() or
                name_lower in emp['full_name'].lower()):
                logger.debug(f"Found partial match for '{name}': {emp['full_name']}")
                return emp
        
        logger.debug(f"No employee found matching '{name}'")
        return None
    
    def get_employee_by_id(self, employee_id: int) -> Optional[Dict[str, Any]]:
        """
        Get employee by ID
        Args:
            employee_id: Staff ID
        Returns: Employee dictionary or None
        """
        employees = self.get_all_employees()
        
        for emp in employees:
            if emp['id'] == employee_id:
                return emp
        
        return None
    
    def get_tasks_for_employee(self, employee_id: int, status_filter: List[int] = None,
                              limit: int = None, offset: int = 0) -> List[Dict[str, Any]]:
        """
        Get tasks assigned to an employee
        Args:
            employee_id: Staff ID
            status_filter: List of status IDs to filter by
            limit: Maximum number of tasks to return
            offset: Number of tasks to skip
        Returns: List of task dictionaries
        """
        start_time = time.time()
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            # Build query
            base_query = """
                SELECT 
                    t.id,
                    t.name,
                    t.description,
                    t.status,
                    t.priority,
                    t.startdate,
                    t.duedate,
                    t.datefinished,
                    t.rel_type,
                    t.rel_id,
                    p.name as project_name,
                    c.company as client_name
                FROM tbltasks t
                INNER JOIN tbltask_assigned ta ON t.id = ta.taskid
                LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
                LEFT JOIN tblclients c ON p.clientid = c.userid
                WHERE ta.staffid = %s
            """
            
            params = [employee_id]
            
            # Add status filter
            if status_filter:
                placeholders = ','.join(['%s'] * len(status_filter))
                base_query += f" AND t.status IN ({placeholders})"
                params.extend(status_filter)
            
            # Add ordering and pagination
            base_query += " ORDER BY t.priority DESC, t.duedate ASC"
            
            if limit:
                base_query += " LIMIT %s OFFSET %s"
                params.extend([limit, offset])
            
            cursor.execute(base_query, params)
            tasks = cursor.fetchall()
            
            execution_time = time.time() - start_time
            logger.log_db_operation('SELECT', 'tbltasks', True, execution_time, len(tasks))
            
            return tasks
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.log_db_operation('SELECT', 'tbltasks', False, execution_time)
            logger.error("Failed to fetch tasks for employee", error=e, 
                        extra_data={'employee_id': employee_id})
            return []
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def get_task_by_id(self, task_id: int) -> Optional[Dict[str, Any]]:
        """
        Get task details by task ID
        Args:
            task_id: Task ID
        Returns: Task dictionary or None
        """
        start_time = time.time()
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor(pymysql.cursors.DictCursor)
            
            query = """
                SELECT 
                    t.id,
                    t.name,
                    t.description,
                    t.status,
                    t.priority,
                    t.startdate,
                    t.duedate,
                    t.datefinished,
                    ta.staffid as assigned,
                    t.rel_type,
                    t.rel_id,
                    CONCAT(s.firstname, ' ', s.lastname) as assigned_to,
                    p.name as project_name,
                    c.company as client_name
                FROM tbltasks t
                LEFT JOIN tbltask_assigned ta ON t.id = ta.taskid
                LEFT JOIN tblstaff s ON ta.staffid = s.staffid
                LEFT JOIN tblprojects p ON t.rel_id = p.id AND t.rel_type = 'project'
                LEFT JOIN tblclients c ON p.clientid = c.userid
                WHERE t.id = %s
            """
            
            cursor.execute(query, [task_id])
            task = cursor.fetchone()
            
            execution_time = time.time() - start_time
            logger.log_db_operation('SELECT', 'tbltasks', True, execution_time, 1 if task else 0)
            
            return task
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.log_db_operation('SELECT', 'tbltasks', False, execution_time)
            logger.error("Failed to fetch task by ID", error=e, 
                        extra_data={'task_id': task_id})
            return None
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def save_daily_summary(self, employee_id: int, summary_date: str, 
                          summary_data: Dict[str, Any]) -> bool:
        """
        Save daily summary for an employee
        Args:
            employee_id: Staff ID
            summary_date: Date in YYYY-MM-DD format
            summary_data: Summary data to store as JSON
        Returns: Success status
        """
        start_time = time.time()
        
        try:
            connection = self._get_connection()
            cursor = connection.cursor()
            
            # Create table if it doesn't exist
            create_table_query = """
                CREATE TABLE IF NOT EXISTS daily_summaries (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    employee_id INT NOT NULL,
                    summary_date DATE NOT NULL,
                    summary_data JSON NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                    UNIQUE KEY unique_employee_date (employee_id, summary_date),
                    FOREIGN KEY (employee_id) REFERENCES tblstaff(staffid)
                )
            """
            cursor.execute(create_table_query)
            
            # Insert or update summary
            insert_query = """
                INSERT INTO daily_summaries (employee_id, summary_date, summary_data)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                    summary_data = VALUES(summary_data),
                    updated_at = CURRENT_TIMESTAMP
            """
            
            import json
            cursor.execute(insert_query, [employee_id, summary_date, json.dumps(summary_data)])
            connection.commit()
            
            execution_time = time.time() - start_time
            logger.log_db_operation('INSERT/UPDATE', 'daily_summaries', True, execution_time, 1)
            
            return True
            
        except Exception as e:
            connection.rollback()
            execution_time = time.time() - start_time
            logger.log_db_operation('INSERT/UPDATE', 'daily_summaries', False, execution_time)
            logger.error("Failed to save daily summary", error=e, 
                        extra_data={'employee_id': employee_id, 'summary_date': summary_date})
            return False
        finally:
            if 'cursor' in locals():
                cursor.close()
    
    def _is_cache_valid(self) -> bool:
        """Check if employee cache is still valid"""
        if not self._cache_timestamp or not self._employee_cache:
            return False
        
        cache_age = time.time() - self._cache_timestamp
        return cache_age < Config.CACHE_TTL_SECONDS
    
    def close_connection(self):
        """Close database connection"""
        if self.connection:
            self.connection.close()
            self.connection = None
            logger.info("Database connection closed")

# Global CRM connector instance
crm_connector = CRMConnector()

def get_crm_connector() -> CRMConnector:
    """Get the global CRM connector instance"""
    return crm_connector