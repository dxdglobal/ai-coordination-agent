"""
Scheduler - Daily AI summary job for task management
Handles automated daily summaries and periodic tasks
"""

import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
import atexit
import json

from .config import Config
from .crm_connector import get_crm_connector
from .retriever import get_task_retriever
from .generator import get_response_generator
from .logger import get_logger

# Initialize components
logger = get_logger()
crm = get_crm_connector()
retriever = get_task_retriever()
generator = get_response_generator()

class TaskScheduler:
    """Manages scheduled tasks for the task management system"""
    
    def __init__(self):
        self.scheduler = BackgroundScheduler(timezone=Config.SCHEDULER_TIMEZONE)
        self.is_running = False
        self._setup_jobs()
        
        # Register shutdown handler
        atexit.register(self.shutdown)
    
    def _setup_jobs(self):
        """Setup scheduled jobs"""
        
        # Daily summary job - runs at 6 AM UTC
        self.scheduler.add_job(
            func=self.generate_daily_summaries,
            trigger=CronTrigger.from_crontab(f"0 6 * * *"),  # 6 AM daily
            id='daily_summaries',
            name='Generate Daily Task Summaries',
            max_instances=1,
            coalesce=True
        )
        
        # Weekly performance reports - runs every Monday at 8 AM UTC
        self.scheduler.add_job(
            func=self.generate_weekly_reports,
            trigger=CronTrigger.from_crontab(f"0 8 * * 1"),  # Monday 8 AM
            id='weekly_reports',
            name='Generate Weekly Performance Reports',
            max_instances=1,
            coalesce=True
        )
        
        # Hourly embeddings refresh for active tasks
        self.scheduler.add_job(
            func=self.refresh_embeddings,
            trigger=CronTrigger.from_crontab(f"0 * * * *"),  # Every hour
            id='refresh_embeddings',
            name='Refresh Task Embeddings',
            max_instances=1,
            coalesce=True
        )
        
        # Daily anomaly detection - runs at 9 AM UTC
        self.scheduler.add_job(
            func=self.detect_anomalies,
            trigger=CronTrigger.from_crontab(f"0 9 * * *"),  # 9 AM daily
            id='anomaly_detection',
            name='Daily Anomaly Detection',
            max_instances=1,
            coalesce=True
        )
        
        logger.info("Scheduled jobs configured")
    
    def start(self):
        """Start the scheduler"""
        if not self.is_running:
            self.scheduler.start()
            self.is_running = True
            logger.info("Task scheduler started")
    
    def shutdown(self):
        """Shutdown the scheduler"""
        if self.is_running:
            self.scheduler.shutdown()
            self.is_running = False
            logger.info("Task scheduler stopped")
    
    def generate_daily_summaries(self):
        """Generate daily summaries for all employees"""
        start_time = time.time()
        
        try:
            logger.info("Starting daily summary generation")
            
            # Get all active employees
            employees = crm.get_all_employees()
            
            if not employees:
                logger.warning("No employees found for daily summary")
                return
            
            summaries_generated = 0
            errors = 0
            
            for employee in employees:
                try:
                    summary = self._generate_employee_daily_summary(employee)
                    
                    if summary['success']:
                        # Save to database
                        today = datetime.now().strftime('%Y-%m-%d')
                        save_success = crm.save_daily_summary(
                            employee['id'], 
                            today, 
                            summary['data']
                        )
                        
                        if save_success:
                            summaries_generated += 1
                            logger.debug(f"Daily summary saved for {employee['full_name']}")
                        else:
                            errors += 1
                            logger.error(f"Failed to save daily summary for {employee['full_name']}")
                    else:
                        errors += 1
                        logger.error(f"Failed to generate daily summary for {employee['full_name']}")
                
                except Exception as e:
                    errors += 1
                    logger.error(f"Error processing daily summary for {employee['full_name']}", error=e)
            
            processing_time = time.time() - start_time
            
            logger.info(f"Daily summary generation completed", extra_data={
                'summaries_generated': summaries_generated,
                'errors': errors,
                'total_employees': len(employees),
                'processing_time': processing_time
            })
            
        except Exception as e:
            logger.error("Failed to generate daily summaries", error=e)
    
    def _generate_employee_daily_summary(self, employee: Dict[str, Any]) -> Dict[str, Any]:
        """Generate daily summary for a single employee"""
        try:
            # Retrieve tasks for the employee
            retrieved_data = retriever.retrieve_tasks_for_employee(
                employee_id=employee['id'],
                intent='task_summary',
                query=f"Daily summary for {employee['full_name']}",
                limit=50
            )
            
            if retrieved_data.get('error'):
                return {
                    'success': False,
                    'error': retrieved_data['error']
                }
            
            # Generate AI summary
            response = generator.generate_response(
                intent='task_summary',
                employee=employee['full_name'],
                retrieved_data=retrieved_data,
                original_query=f"Generate daily summary for {employee['full_name']}"
            )
            
            if response.get('error'):
                return {
                    'success': False,
                    'error': response['error']
                }
            
            # Structure the daily summary data
            summary_data = {
                'employee_id': employee['id'],
                'employee_name': employee['full_name'],
                'summary_date': datetime.now().strftime('%Y-%m-%d'),
                'ai_summary': response.get('ai_summary', ''),
                'key_insights': response.get('key_insights', []),
                'task_breakdown': response.get('task_breakdown', {}),
                'total_tasks': retrieved_data.get('total_count', 0),
                'generated_at': datetime.now().isoformat(),
                'processing_time': response.get('processing_time', 0)
            }
            
            return {
                'success': True,
                'data': summary_data
            }
            
        except Exception as e:
            logger.error(f"Failed to generate daily summary for {employee['full_name']}", error=e)
            return {
                'success': False,
                'error': str(e)
            }
    
    def generate_weekly_reports(self):
        """Generate weekly performance reports for all employees"""
        start_time = time.time()
        
        try:
            logger.info("Starting weekly report generation")
            
            employees = crm.get_all_employees()
            reports_generated = 0
            errors = 0
            
            for employee in employees:
                try:
                    # Retrieve tasks for performance analysis
                    retrieved_data = retriever.retrieve_tasks_for_employee(
                        employee_id=employee['id'],
                        intent='performance_report',
                        query=f"Weekly performance report for {employee['full_name']}",
                        limit=100  # More tasks for performance analysis
                    )
                    
                    if not retrieved_data.get('error'):
                        # Generate performance report
                        response = generator.generate_response(
                            intent='performance_report',
                            employee=employee['full_name'],
                            retrieved_data=retrieved_data,
                            original_query=f"Generate weekly performance report for {employee['full_name']}"
                        )
                        
                        if not response.get('error'):
                            # Save weekly report (you might want to create a separate table)
                            report_data = {
                                'employee_id': employee['id'],
                                'report_type': 'weekly_performance',
                                'report_date': datetime.now().strftime('%Y-%m-%d'),
                                'ai_analysis': response.get('ai_analysis', ''),
                                'metrics': response.get('metrics', {}),
                                'recommendations': response.get('recommendations', []),
                                'generated_at': datetime.now().isoformat()
                            }
                            
                            # For now, save as daily summary with special type
                            save_success = crm.save_daily_summary(
                                employee['id'],
                                datetime.now().strftime('%Y-%m-%d'),
                                report_data
                            )
                            
                            if save_success:
                                reports_generated += 1
                                logger.debug(f"Weekly report saved for {employee['full_name']}")
                        
                except Exception as e:
                    errors += 1
                    logger.error(f"Error generating weekly report for {employee['full_name']}", error=e)
            
            processing_time = time.time() - start_time
            
            logger.info("Weekly report generation completed", extra_data={
                'reports_generated': reports_generated,
                'errors': errors,
                'processing_time': processing_time
            })
            
        except Exception as e:
            logger.error("Failed to generate weekly reports", error=e)
    
    def refresh_embeddings(self):
        """Refresh embeddings for recently updated tasks"""
        start_time = time.time()
        
        try:
            logger.info("Starting embeddings refresh")
            
            # Build embeddings index (this will update existing embeddings)
            result = retriever.build_embeddings_index()
            
            if result.get('success'):
                logger.info("Embeddings refresh completed", extra_data={
                    'indexed_count': result.get('indexed_count', 0),
                    'processing_time': result.get('processing_time', 0)
                })
            else:
                logger.error("Embeddings refresh failed", extra_data={'error': result.get('error')})
            
        except Exception as e:
            logger.error("Failed to refresh embeddings", error=e)
    
    def detect_anomalies(self):
        """Run daily anomaly detection for all employees"""
        start_time = time.time()
        
        try:
            logger.info("Starting daily anomaly detection")
            
            employees = crm.get_all_employees()
            total_anomalies = 0
            critical_anomalies = 0
            
            for employee in employees:
                try:
                    # Retrieve tasks for anomaly detection
                    retrieved_data = retriever.retrieve_tasks_for_employee(
                        employee_id=employee['id'],
                        intent='anomaly_check',
                        query=f"Check for anomalies in {employee['full_name']}'s tasks",
                        limit=50
                    )
                    
                    if not retrieved_data.get('error'):
                        # Generate anomaly report
                        response = generator.generate_response(
                            intent='anomaly_check',
                            employee=employee['full_name'],
                            retrieved_data=retrieved_data,
                            original_query=f"Daily anomaly check for {employee['full_name']}"
                        )
                        
                        if not response.get('error'):
                            anomalies = response.get('anomalies', [])
                            total_anomalies += len(anomalies)
                            
                            # Count critical anomalies
                            critical_count = len([a for a in anomalies if a.get('severity') == 'high'])
                            critical_anomalies += critical_count
                            
                            # Log critical anomalies
                            if critical_count > 0:
                                logger.warning(f"Critical anomalies detected for {employee['full_name']}", 
                                             extra_data={
                                                 'employee': employee['full_name'],
                                                 'critical_anomalies': critical_count,
                                                 'total_anomalies': len(anomalies)
                                             })
                
                except Exception as e:
                    logger.error(f"Error in anomaly detection for {employee['full_name']}", error=e)
            
            processing_time = time.time() - start_time
            
            logger.info("Daily anomaly detection completed", extra_data={
                'total_anomalies': total_anomalies,
                'critical_anomalies': critical_anomalies,
                'employees_checked': len(employees),
                'processing_time': processing_time
            })
            
        except Exception as e:
            logger.error("Failed to run anomaly detection", error=e)
    
    def run_manual_job(self, job_name: str) -> Dict[str, Any]:
        """Run a scheduled job manually"""
        try:
            if job_name == 'daily_summaries':
                self.generate_daily_summaries()
                return {'success': True, 'message': 'Daily summaries generated'}
            elif job_name == 'weekly_reports':
                self.generate_weekly_reports()
                return {'success': True, 'message': 'Weekly reports generated'}
            elif job_name == 'refresh_embeddings':
                self.refresh_embeddings()
                return {'success': True, 'message': 'Embeddings refreshed'}
            elif job_name == 'anomaly_detection':
                self.detect_anomalies()
                return {'success': True, 'message': 'Anomaly detection completed'}
            else:
                return {'success': False, 'error': f'Unknown job: {job_name}'}
        
        except Exception as e:
            logger.error(f"Failed to run manual job: {job_name}", error=e)
            return {'success': False, 'error': str(e)}
    
    def get_job_status(self) -> Dict[str, Any]:
        """Get status of all scheduled jobs"""
        jobs = []
        
        for job in self.scheduler.get_jobs():
            next_run = job.next_run_time
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': next_run.isoformat() if next_run else None,
                'trigger': str(job.trigger)
            })
        
        return {
            'scheduler_running': self.is_running,
            'jobs': jobs
        }

# Global scheduler instance
task_scheduler = TaskScheduler()

def get_task_scheduler() -> TaskScheduler:
    """Get the global task scheduler instance"""
    return task_scheduler

def start_scheduler():
    """Start the task scheduler"""
    task_scheduler.start()

def stop_scheduler():
    """Stop the task scheduler"""
    task_scheduler.shutdown()