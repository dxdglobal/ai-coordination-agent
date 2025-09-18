"""
Script to add sample data for testing the AI Coordination Agent
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from models.models import db, Project, Task, Comment, Label, TaskStatus, Priority
from app import create_app
from datetime import datetime, timedelta

def add_sample_data():
    app = create_app()
    
    with app.app_context():
        # Clear existing data (optional)
        print("Adding sample data...")
        
        # Create sample projects
        projects = [
            Project(
                name="Website Redesign",
                description="Complete overhaul of company website with modern design",
                status=TaskStatus.IN_PROGRESS,
                start_date=datetime.now() - timedelta(days=30),
                deadline=datetime.now() + timedelta(days=60)
            ),
            Project(
                name="Mobile App Development",
                description="Develop cross-platform mobile application",
                status=TaskStatus.TODO,
                start_date=datetime.now() + timedelta(days=7),
                deadline=datetime.now() + timedelta(days=120)
            ),
            Project(
                name="Database Migration",
                description="Migrate legacy database to new cloud infrastructure",
                status=TaskStatus.DONE,
                start_date=datetime.now() - timedelta(days=60),
                end_date=datetime.now() - timedelta(days=10)
            ),
            Project(
                name="AI Integration Project",
                description="Integrate AI capabilities into existing systems",
                status=TaskStatus.REVIEW,
                start_date=datetime.now() - timedelta(days=20),
                deadline=datetime.now() + timedelta(days=30)
            )
        ]
        
        for project in projects:
            db.session.add(project)
        
        db.session.commit()
        print(f"✅ Added {len(projects)} projects")
        
        # Create sample tasks
        tasks = [
            Task(
                title="Design mockups for homepage",
                description="Create wireframes and visual mockups for the new homepage design",
                status=TaskStatus.DONE,
                priority=Priority.HIGH,
                project_id=1,
                assignee="Designer Team",
                estimated_hours=20,
                actual_hours=18
            ),
            Task(
                title="Implement responsive navigation",
                description="Code the responsive navigation menu with mobile support",
                status=TaskStatus.IN_PROGRESS,
                priority=Priority.MEDIUM,
                project_id=1,
                assignee="Frontend Developer",
                estimated_hours=15,
                start_time=datetime.now() - timedelta(days=5)
            ),
            Task(
                title="Set up React Native environment",
                description="Configure development environment for React Native app",
                status=TaskStatus.TODO,
                priority=Priority.HIGH,
                project_id=2,
                assignee="Mobile Developer",
                estimated_hours=8
            ),
            Task(
                title="Design app architecture",
                description="Plan the overall architecture and component structure",
                status=TaskStatus.IN_PROGRESS,
                priority=Priority.URGENT,
                project_id=2,
                assignee="Tech Lead",
                estimated_hours=12,
                start_time=datetime.now() - timedelta(days=2)
            ),
            Task(
                title="Data backup verification",
                description="Verify all data has been properly backed up before migration",
                status=TaskStatus.DONE,
                priority=Priority.URGENT,
                project_id=3,
                assignee="Database Admin",
                estimated_hours=6,
                actual_hours=8
            ),
            Task(
                title="Train AI model",
                description="Train and fine-tune the AI model for specific use cases",
                status=TaskStatus.REVIEW,
                priority=Priority.HIGH,
                project_id=4,
                assignee="ML Engineer",
                estimated_hours=40,
                actual_hours=35
            ),
            Task(
                title="API endpoint development",
                description="Develop REST API endpoints for AI integration",
                status=TaskStatus.IN_PROGRESS,
                priority=Priority.MEDIUM,
                project_id=4,
                assignee="Backend Developer",
                estimated_hours=25,
                start_time=datetime.now() - timedelta(days=7)
            ),
            Task(
                title="User acceptance testing",
                description="Conduct comprehensive testing with end users",
                status=TaskStatus.TODO,
                priority=Priority.MEDIUM,
                project_id=1,
                assignee="QA Team",
                estimated_hours=30
            )
        ]
        
        for task in tasks:
            db.session.add(task)
        
        db.session.commit()
        print(f"✅ Added {len(tasks)} tasks")
        
        # Create sample comments
        comments = [
            Comment(
                content="Great progress on the design! The mockups look very modern and user-friendly.",
                author="Project Manager",
                task_id=1
            ),
            Comment(
                content="Need to ensure the navigation works well on tablets too, not just mobile phones.",
                author="UX Designer",
                task_id=2
            ),
            Comment(
                content="Environment setup is taking longer than expected due to some dependency conflicts.",
                author="Mobile Developer",
                task_id=3
            ),
            Comment(
                content="Architecture looks solid. Let's schedule a review meeting for next week.",
                author="CTO",
                task_id=4
            ),
            Comment(
                content="All backup procedures completed successfully. Ready for migration.",
                author="Database Admin",
                task_id=5
            ),
            Comment(
                content="Model performance is exceeding expectations. Accuracy is at 94%.",
                author="ML Engineer",
                task_id=6
            )
        ]
        
        for comment in comments:
            db.session.add(comment)
        
        db.session.commit()
        print(f"✅ Added {len(comments)} comments")
        
        # Create sample labels
        labels = [
            Label(name="Frontend", color="#3498db"),
            Label(name="Backend", color="#e74c3c"),
            Label(name="Design", color="#9b59b6"),
            Label(name="Testing", color="#f39c12"),
            Label(name="Documentation", color="#2ecc71"),
            Label(name="Bug", color="#e67e22"),
            Label(name="Feature", color="#1abc9c"),
            Label(name="Urgent", color="#c0392b")
        ]
        
        for label in labels:
            db.session.add(label)
        
        db.session.commit()
        print(f"✅ Added {len(labels)} labels")
        
        print("\n🎉 Sample data added successfully!")
        print("\nSummary:")
        print(f"- {Project.query.count()} total projects")
        print(f"- {Task.query.count()} total tasks")
        print(f"- {Comment.query.count()} total comments")
        print(f"- {Label.query.count()} total labels")
        
        # Show project status breakdown
        print(f"\nProject Status Breakdown:")
        for status in TaskStatus:
            count = Project.query.filter_by(status=status).count()
            print(f"- {status.value}: {count}")
        
        # Show task status breakdown
        print(f"\nTask Status Breakdown:")
        for status in TaskStatus:
            count = Task.query.filter_by(status=status).count()
            print(f"- {status.value}: {count}")

if __name__ == "__main__":
    add_sample_data()