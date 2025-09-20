"""
Script to add employee and invoice sample data including Haseeb and Hamza
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.models import db, Employee, Invoice, Task, Project, TaskStatus, Priority
from app import create_app
from datetime import datetime, timedelta
import random

def add_employee_data():
    app = create_app()
    
    with app.app_context():
        # Create tables if they don't exist
        db.create_all()
        
        print("Adding employee and invoice sample data...")
        
        # Create sample employees
        employees = [
            Employee(
                name="Haseeb Ahmed",
                email="haseeb@company.com",
                phone="+1-555-0101",
                department="Engineering",
                position="Senior Software Engineer",
                salary=85000.0,
                hire_date=datetime.now() - timedelta(days=730),  # 2 years ago
                is_active=True
            ),
            Employee(
                name="Hamza Haseeb",
                email="hamza.haseeb@company.com",
                phone="+1-555-0102",
                department="Engineering",
                position="Full Stack Developer",
                salary=75000.0,
                hire_date=datetime.now() - timedelta(days=365),  # 1 year ago
                is_active=True
            ),
            Employee(
                name="Sarah Johnson",
                email="sarah.johnson@company.com",
                phone="+1-555-0103",
                department="Design",
                position="UI/UX Designer",
                salary=70000.0,
                hire_date=datetime.now() - timedelta(days=500),
                is_active=True
            ),
            Employee(
                name="Mike Chen",
                email="mike.chen@company.com",
                phone="+1-555-0104",
                department="Engineering",
                position="DevOps Engineer",
                salary=80000.0,
                hire_date=datetime.now() - timedelta(days=600),
                is_active=True
            ),
            Employee(
                name="Emily Davis",
                email="emily.davis@company.com",
                phone="+1-555-0105",
                department="Project Management",
                position="Project Manager",
                salary=90000.0,
                hire_date=datetime.now() - timedelta(days=1000),
                is_active=True
            ),
            Employee(
                name="Alex Rodriguez",
                email="alex.rodriguez@company.com",
                phone="+1-555-0106",
                department="Sales",
                position="Sales Manager",
                salary=95000.0,
                hire_date=datetime.now() - timedelta(days=800),
                is_active=True
            )
        ]
        
        # Add employees to database
        for employee in employees:
            existing = Employee.query.filter_by(email=employee.email).first()
            if not existing:
                db.session.add(employee)
        
        db.session.commit()
        
        # Get the added employees
        haseeb = Employee.query.filter_by(name="Haseeb Ahmed").first()
        hamza = Employee.query.filter_by(name="Hamza Haseeb").first()
        sarah = Employee.query.filter_by(name="Sarah Johnson").first()
        mike = Employee.query.filter_by(name="Mike Chen").first()
        emily = Employee.query.filter_by(name="Emily Davis").first()
        alex = Employee.query.filter_by(name="Alex Rodriguez").first()
        
        # Set up manager relationships
        if emily and haseeb:
            haseeb.manager_id = emily.id
        if emily and hamza:
            hamza.manager_id = emily.id
        if emily and sarah:
            sarah.manager_id = emily.id
        if emily and mike:
            mike.manager_id = emily.id
        
        db.session.commit()
        
        # Create sample invoices for this month
        current_month = datetime.now().replace(day=1)
        next_month = (current_month + timedelta(days=32)).replace(day=1)
        
        invoices = [
            Invoice(
                invoice_number="INV-2025-001",
                client_name="Tech Corp Solutions",
                amount=15000.0,
                tax_amount=1500.0,
                total_amount=16500.0,
                status="paid",
                invoice_date=current_month + timedelta(days=2),
                due_date=current_month + timedelta(days=32),
                paid_date=current_month + timedelta(days=15),
                assigned_to=hamza.id if hamza else None
            ),
            Invoice(
                invoice_number="INV-2025-002",
                client_name="Digital Innovations Ltd",
                amount=22000.0,
                tax_amount=2200.0,
                total_amount=24200.0,
                status="pending",
                invoice_date=current_month + timedelta(days=5),
                due_date=current_month + timedelta(days=35),
                assigned_to=haseeb.id if haseeb else None
            ),
            Invoice(
                invoice_number="INV-2025-003",
                client_name="StartupX Inc",
                amount=8500.0,
                tax_amount=850.0,
                total_amount=9350.0,
                status="paid",
                invoice_date=current_month + timedelta(days=10),
                due_date=current_month + timedelta(days=40),
                paid_date=current_month + timedelta(days=25),
                assigned_to=sarah.id if sarah else None
            ),
            Invoice(
                invoice_number="INV-2025-004",
                client_name="Enterprise Systems",
                amount=35000.0,
                tax_amount=3500.0,
                total_amount=38500.0,
                status="pending",
                invoice_date=current_month + timedelta(days=15),
                due_date=current_month + timedelta(days=45),
                assigned_to=alex.id if alex else None
            ),
            Invoice(
                invoice_number="INV-2025-005",
                client_name="Cloud Services Co",
                amount=12000.0,
                tax_amount=1200.0,
                total_amount=13200.0,
                status="overdue",
                invoice_date=current_month - timedelta(days=10),
                due_date=current_month + timedelta(days=20),
                assigned_to=mike.id if mike else None
            )
        ]
        
        # Add invoices to database
        for invoice in invoices:
            existing = Invoice.query.filter_by(invoice_number=invoice.invoice_number).first()
            if not existing:
                db.session.add(invoice)
        
        # Get existing projects to assign tasks
        projects = Project.query.all()
        
        # Create sample tasks assigned to employees
        if projects and hamza and haseeb:
            hamza_tasks = [
                Task(
                    title="Implement user authentication system",
                    description="Create secure login and registration functionality",
                    status=TaskStatus.IN_PROGRESS,
                    priority=Priority.HIGH,
                    assignee="Hamza Haseeb",
                    assigned_to=hamza.id,
                    project_id=projects[0].id if projects else None,
                    estimated_hours=40.0,
                    actual_hours=25.0
                ),
                Task(
                    title="Design REST API endpoints",
                    description="Create comprehensive API documentation and implementation",
                    status=TaskStatus.DONE,
                    priority=Priority.MEDIUM,
                    assignee="Hamza Haseeb",
                    assigned_to=hamza.id,
                    project_id=projects[1].id if len(projects) > 1 else None,
                    estimated_hours=30.0,
                    actual_hours=28.0
                ),
                Task(
                    title="Code review and optimization",
                    description="Review existing codebase and optimize performance",
                    status=TaskStatus.TODO,
                    priority=Priority.MEDIUM,
                    assignee="Hamza Haseeb",
                    assigned_to=hamza.id,
                    project_id=projects[0].id if projects else None,
                    estimated_hours=20.0
                )
            ]
            
            haseeb_tasks = [
                Task(
                    title="Database schema design",
                    description="Design and implement database structure for new features",
                    status=TaskStatus.DONE,
                    priority=Priority.HIGH,
                    assignee="Haseeb Ahmed",
                    assigned_to=haseeb.id,
                    project_id=projects[2].id if len(projects) > 2 else None,
                    estimated_hours=35.0,
                    actual_hours=32.0
                ),
                Task(
                    title="Performance monitoring setup",
                    description="Implement comprehensive monitoring and alerting system",
                    status=TaskStatus.IN_PROGRESS,
                    priority=Priority.HIGH,
                    assignee="Haseeb Ahmed",
                    assigned_to=haseeb.id,
                    project_id=projects[3].id if len(projects) > 3 else None,
                    estimated_hours=25.0,
                    actual_hours=15.0
                ),
                Task(
                    title="Security audit and fixes",
                    description="Conduct security review and implement recommended fixes",
                    status=TaskStatus.REVIEW,
                    priority=Priority.URGENT,
                    assignee="Haseeb Ahmed",
                    assigned_to=haseeb.id,
                    project_id=projects[0].id if projects else None,
                    estimated_hours=45.0,
                    actual_hours=40.0
                )
            ]
            
            # Add tasks to database
            for task in hamza_tasks + haseeb_tasks:
                db.session.add(task)
        
        db.session.commit()
        
        print("✅ Successfully added employee and invoice data!")
        print(f"✅ Added {len(employees)} employees")
        print(f"✅ Added {len(invoices)} invoices")
        print("✅ Employee data includes:")
        for emp in employees:
            print(f"   - {emp.name} ({emp.position}) - {emp.department}")

if __name__ == '__main__':
    add_employee_data()