#!/usr/bin/env python3
"""
CRM Sync Service - Complete integration between AI database and existing CRM
Handles bidirectional data synchronization for Task 1.1 completion
"""

import os
import mysql.connector
from datetime import datetime, timedelta
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from flask_sqlalchemy import SQLAlchemy
from models.models import db, Task, Project, Comment, User, Notification, Employee

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@dataclass
class CRMSyncConfig:
    """Configuration for CRM synchronization"""
    host: str = os.getenv('CRM_DB_HOST', '92.113.22.65')
    user: str = os.getenv('CRM_DB_USER', 'u906714182_sqlrrefdvdv')
    password: str = os.getenv('CRM_DB_PASSWORD', '')
    database: str = os.getenv('CRM_DB_NAME', 'u906714182_sqlrrefdvdv')
    port: int = int(os.getenv('CRM_DB_PORT', '3306'))
    sync_interval: int = 300  # 5 minutes
    batch_size: int = 100
    
class CRMSyncService:
    """Service for synchronizing data between AI database and CRM database"""
    
    def __init__(self, config: CRMSyncConfig = None):
        self.config = config or CRMSyncConfig()
        self.last_sync = {}  # Track last sync timestamps
        
    def get_crm_connection(self):
        """Get connection to CRM MySQL database"""
        try:
            return mysql.connector.connect(
                host=self.config.host,
                user=self.config.user,
                password=self.config.password,
                database=self.config.database,
                port=self.config.port,
                autocommit=True
            )
        except Exception as e:
            logger.error(f"Failed to connect to CRM database: {e}")
            raise
    
    def sync_staff_to_users(self) -> Dict[str, Any]:
        """Sync CRM staff data to AI users table"""
        try:
            crm_conn = self.get_crm_connection()
            cursor = crm_conn.cursor(dictionary=True)
            
            # Get staff data from CRM
            cursor.execute("""
                SELECT staffid, firstname, lastname, email, admin, role, 
                       active, last_login, last_activity, datecreated
                FROM tblstaff 
                WHERE active = 1
                ORDER BY staffid
            """)
            
            staff_records = cursor.fetchall()
            synced_count = 0
            updated_count = 0
            
            for staff in staff_records:
                try:
                    # Check if user exists
                    existing_user = User.query.filter_by(crm_user_id=staff['staffid']).first()
                    
                    user_data = {
                        'crm_user_id': staff['staffid'],
                        'email': staff['email'],
                        'name': f"{staff['firstname']} {staff['lastname']}",
                        'role': 'admin' if staff['admin'] else 'user',
                        'last_login': staff['last_login'],
                        'last_activity': staff['last_activity'],
                        'is_active': bool(staff['active'])
                    }
                    
                    if existing_user:
                        # Update existing user
                        for key, value in user_data.items():
                            if key != 'crm_user_id':  # Don't update the ID
                                setattr(existing_user, key, value)
                        existing_user.updated_at = datetime.utcnow()
                        updated_count += 1
                    else:
                        # Create new user
                        new_user = User(**user_data)
                        db.session.add(new_user)
                        synced_count += 1
                        
                except Exception as e:
                    logger.error(f"Error syncing staff {staff['staffid']}: {e}")
                    continue
            
            db.session.commit()
            cursor.close()
            crm_conn.close()
            
            result = {
                'status': 'success',
                'synced_new': synced_count,
                'updated_existing': updated_count,
                'total_processed': len(staff_records),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Staff sync completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Staff sync failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def sync_tasks_to_crm(self) -> Dict[str, Any]:
        """Sync AI tasks back to CRM tasks table"""
        try:
            crm_conn = self.get_crm_connection()
            cursor = crm_conn.cursor(dictionary=True)
            
            # Get recent AI tasks that need to be synced
            recent_tasks = Task.query.filter(
                Task.updated_at > datetime.utcnow() - timedelta(hours=1)
            ).all()
            
            synced_count = 0
            
            for task in recent_tasks:
                try:
                    # Check if task exists in CRM
                    cursor.execute("SELECT id FROM tbltasks WHERE description LIKE %s", 
                                 (f"%AI_TASK_{task.id}%",))
                    existing_task = cursor.fetchone()
                    
                    task_data = {
                        'name': task.title,
                        'description': f"{task.description}\n\n[AI_TASK_{task.id}]",
                        'status': self._map_status_to_crm(task.status),
                        'priority': self._map_priority_to_crm(task.priority),
                        'startdate': task.start_time,
                        'duedate': task.end_time,
                        'dateadded': task.created_at
                    }
                    
                    if not existing_task:
                        # Insert new task in CRM
                        columns = ', '.join(task_data.keys())
                        placeholders = ', '.join(['%s'] * len(task_data))
                        
                        cursor.execute(
                            f"INSERT INTO tbltasks ({columns}) VALUES ({placeholders})",
                            list(task_data.values())
                        )
                        synced_count += 1
                        
                except Exception as e:
                    logger.error(f"Error syncing task {task.id}: {e}")
                    continue
            
            cursor.close()
            crm_conn.close()
            
            result = {
                'status': 'success',
                'synced_tasks': synced_count,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Task sync completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Task sync failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def sync_crm_tasks_to_ai(self) -> Dict[str, Any]:
        """Sync CRM tasks to AI database"""
        try:
            crm_conn = self.get_crm_connection()
            cursor = crm_conn.cursor(dictionary=True)
            
            # Get recent CRM tasks
            cursor.execute("""
                SELECT id, name, description, status, priority, 
                       startdate, duedate, dateadded, datefinished
                FROM tbltasks 
                WHERE dateadded > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                OR dateupdated > DATE_SUB(NOW(), INTERVAL 1 HOUR)
                ORDER BY id DESC
                LIMIT %s
            """, (self.config.batch_size,))
            
            crm_tasks = cursor.fetchall()
            synced_count = 0
            
            for crm_task in crm_tasks:
                try:
                    # Check if AI task already exists
                    existing_task = Task.query.filter(
                        Task.description.contains(f"CRM_TASK_{crm_task['id']}")
                    ).first()
                    
                    if not existing_task:
                        # Create new AI task
                        ai_task = Task(
                            title=crm_task['name'] or f"CRM Task {crm_task['id']}",
                            description=f"{crm_task['description'] or ''}\n\n[CRM_TASK_{crm_task['id']}]",
                            status=self._map_crm_status_to_ai(crm_task['status']),
                            priority=self._map_crm_priority_to_ai(crm_task['priority']),
                            start_time=crm_task['startdate'],
                            end_time=crm_task['duedate'],
                            created_at=crm_task['dateadded']
                        )
                        
                        db.session.add(ai_task)
                        synced_count += 1
                        
                except Exception as e:
                    logger.error(f"Error importing CRM task {crm_task['id']}: {e}")
                    continue
            
            db.session.commit()
            cursor.close()
            crm_conn.close()
            
            result = {
                'status': 'success',
                'imported_tasks': synced_count,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"CRM task import completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"CRM task import failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def sync_notifications(self) -> Dict[str, Any]:
        """Sync notifications between systems"""
        try:
            crm_conn = self.get_crm_connection()
            cursor = crm_conn.cursor(dictionary=True)
            
            # Get recent CRM notifications
            cursor.execute("""
                SELECT id, description, touserid, isread, date
                FROM tblnotifications 
                WHERE date > DATE_SUB(NOW(), INTERVAL 24 HOUR)
                ORDER BY date DESC
                LIMIT %s
            """, (self.config.batch_size,))
            
            crm_notifications = cursor.fetchall()
            synced_count = 0
            
            for notif in crm_notifications:
                try:
                    # Find corresponding AI user
                    user = User.query.filter_by(crm_user_id=notif['touserid']).first()
                    
                    if user:
                        # Check if notification already exists
                        existing_notif = Notification.query.filter_by(
                            user_id=user.id,
                            message=notif['description']
                        ).first()
                        
                        if not existing_notif:
                            # Create new notification
                            ai_notification = Notification(
                                user_id=user.id,
                                title="CRM Notification",
                                message=notif['description'],
                                type='info',
                                read=bool(notif['isread']),
                                created_at=notif['date'],
                                metadata={'crm_notification_id': notif['id']}
                            )
                            
                            db.session.add(ai_notification)
                            synced_count += 1
                            
                except Exception as e:
                    logger.error(f"Error syncing notification {notif['id']}: {e}")
                    continue
            
            db.session.commit()
            cursor.close()
            crm_conn.close()
            
            result = {
                'status': 'success',
                'synced_notifications': synced_count,
                'timestamp': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Notification sync completed: {result}")
            return result
            
        except Exception as e:
            logger.error(f"Notification sync failed: {e}")
            return {'status': 'error', 'message': str(e)}
    
    def full_sync(self) -> Dict[str, Any]:
        """Perform full bidirectional sync"""
        results = {
            'timestamp': datetime.utcnow().isoformat(),
            'operations': {}
        }
        
        # Sync staff to users
        results['operations']['staff_sync'] = self.sync_staff_to_users()
        
        # Sync CRM tasks to AI
        results['operations']['crm_task_import'] = self.sync_crm_tasks_to_ai()
        
        # Sync AI tasks to CRM
        results['operations']['ai_task_export'] = self.sync_tasks_to_crm()
        
        # Sync notifications
        results['operations']['notification_sync'] = self.sync_notifications()
        
        # Calculate overall status
        all_success = all(
            op['status'] == 'success' 
            for op in results['operations'].values()
        )
        
        results['overall_status'] = 'success' if all_success else 'partial_success'
        
        logger.info(f"Full sync completed: {results['overall_status']}")
        return results
    
    def _map_status_to_crm(self, ai_status) -> int:
        """Map AI task status to CRM status codes"""
        status_map = {
            'todo': 1,
            'in_progress': 2,
            'review': 3,
            'done': 4,
            'blocked': 5
        }
        return status_map.get(ai_status.value if hasattr(ai_status, 'value') else ai_status, 1)
    
    def _map_priority_to_crm(self, ai_priority) -> int:
        """Map AI priority to CRM priority codes"""
        priority_map = {
            'low': 1,
            'medium': 2,
            'high': 3,
            'urgent': 4
        }
        return priority_map.get(ai_priority.value if hasattr(ai_priority, 'value') else ai_priority, 2)
    
    def _map_crm_status_to_ai(self, crm_status):
        """Map CRM status codes to AI status"""
        from models.models import TaskStatus
        status_map = {
            1: TaskStatus.TODO,
            2: TaskStatus.IN_PROGRESS,
            3: TaskStatus.REVIEW,
            4: TaskStatus.DONE,
            5: TaskStatus.BLOCKED
        }
        return status_map.get(crm_status, TaskStatus.TODO)
    
    def _map_crm_priority_to_ai(self, crm_priority):
        """Map CRM priority codes to AI priority"""
        from models.models import Priority
        priority_map = {
            1: Priority.LOW,
            2: Priority.MEDIUM,
            3: Priority.HIGH,
            4: Priority.URGENT
        }
        return priority_map.get(crm_priority, Priority.MEDIUM)

# Global sync service instance
crm_sync_service = CRMSyncService()

if __name__ == "__main__":
    print("🔄 Testing CRM Sync Service...")
    
    # Test connection
    try:
        conn = crm_sync_service.get_crm_connection()
        print("✅ CRM database connection successful!")
        conn.close()
    except Exception as e:
        print(f"❌ CRM connection failed: {e}")
    
    print("🔄 CRM Sync Service ready for integration!")