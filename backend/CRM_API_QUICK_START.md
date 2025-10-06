# CRM API Integration - Quick Setup Guide

## 🚀 Quick Start (5 Minutes)

### 1. Install Dependencies
```bash
pip install requests asyncio dataclasses urllib3
```

### 2. Basic Configuration
```python
from crm_api_service import CRMConfig
from crm_api_endpoints import CRMAPIManager

# Configure your CRM API
config = CRMConfig(
    base_url="https://your-crm-api.com",
    authentication_type="jwt",  # or "oauth", "api_key"
    username="your_username",
    password="your_password"
)

# Initialize API manager
api = CRMAPIManager(config)
```

### 3. Test Connection
```python
# Health check
health = api.health_check()
print(f"API Status: {health}")

# Get projects
projects = api.projects.get_all(page=1, per_page=5)
print(f"Found {len(projects.get('data', []))} projects")
```

## 🔧 Authentication Setup

### JWT Authentication
```python
config = CRMConfig(
    base_url="https://api.crm.com",
    authentication_type="jwt",
    username="api_user",
    password="secure_password"
)
```

### OAuth 2.0
```python
config = CRMConfig(
    base_url="https://api.crm.com",
    authentication_type="oauth",
    client_id="your_client_id",
    client_secret="your_client_secret"
)
```

### API Key
```python
config = CRMConfig(
    base_url="https://api.crm.com",
    authentication_type="api_key",
    api_key="your_api_key"
)
```

## 📋 Common Operations

### Projects
```python
from crm_api_endpoints import Project

# Create project
project = Project(
    name="New Project",
    description="Project description",
    status="active",
    priority="high"
)
created = api.projects.create(project)

# Get project
project = api.projects.get_by_id(1)

# Update project
project.status = "completed"
updated = api.projects.update(1, project)

# Delete project
deleted = api.projects.delete(1)
```

### Tasks
```python
from crm_api_endpoints import Task

# Create task
task = Task(
    title="New Task",
    description="Task description",
    project_id=1,
    status="todo",
    priority="medium"
)
created = api.tasks.create(task)

# Assign task
api.tasks.assign_task(task_id=1, assignee_id=5)

# Update status
api.tasks.update_status(task_id=1, status="in_progress")
```

### Comments
```python
from crm_api_endpoints import Comment

# Add comment
comment = Comment(
    content="This is a comment",
    entity_type="project",
    entity_id=1,
    author_id=1
)
api.comments.create(comment)

# Get entity comments
comments = api.comments.get_entity_comments("project", 1)
```

## 🔄 Synchronization Setup

### Basic Sync Configuration
```python
from crm_sync_manager import CRMSyncManager, SyncConfig, SyncDirection

# Configure synchronization
sync_config = SyncConfig(
    direction=SyncDirection.BIDIRECTIONAL,
    batch_size=50,
    sync_interval_minutes=30
)

# Initialize sync manager
sync_manager = CRMSyncManager(config, sync_config, db_session)

# Manual sync
results = await sync_manager.manual_sync()
print(f"Sync completed: {results}")
```

### Automatic Sync
```python
# Start automatic sync (runs in background)
await sync_manager.start_auto_sync()

# Check status
status = sync_manager.get_status()
print(f"Last sync: {status['last_sync']}")

# Stop automatic sync
sync_manager.stop_auto_sync()
```

## 🧪 Testing

### Run Tests
```bash
# Basic tests
python test_crm_api_integration.py

# With integration tests
python test_crm_api_integration.py --integration

# With performance tests
python test_crm_api_integration.py --performance
```

### Test Individual Components
```python
# Test API connection
try:
    health = api.health_check()
    print("✅ API connection successful")
except Exception as e:
    print(f"❌ API connection failed: {e}")

# Test authentication
try:
    projects = api.projects.get_all(per_page=1)
    print("✅ Authentication successful")
except Exception as e:
    print(f"❌ Authentication failed: {e}")
```

## 🔧 Configuration Examples

### Production Configuration
```python
config = CRMConfig(
    base_url="https://prod-api.crm.com",
    api_version="v1",
    authentication_type="api_key",
    api_key="prod_api_key",
    rate_limit_per_minute=200,
    timeout=60,
    max_retries=5
)
```

### Development Configuration
```python
config = CRMConfig(
    base_url="https://dev-api.crm.com",
    api_version="v1",
    authentication_type="jwt",
    username="dev_user",
    password="dev_password",
    rate_limit_per_minute=50,
    timeout=30,
    max_retries=3
)
```

## 🚨 Troubleshooting

### Common Issues

1. **401 Unauthorized**
   ```python
   # Check credentials
   print(f"Auth type: {config.authentication_type}")
   print(f"Base URL: {config.base_url}")
   ```

2. **429 Rate Limited**
   ```python
   # Reduce rate limit
   config.rate_limit_per_minute = 50
   ```

3. **Connection Timeout**
   ```python
   # Increase timeout
   config.timeout = 60
   ```

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)

# All API calls will now be logged
```

## 📞 Need Help?

- **Documentation**: See `TASK_1_2_DOCUMENTATION.md` for complete reference
- **Code Examples**: Check the example usage in each module
- **Tests**: Review test cases for implementation patterns
- **Error Messages**: Enable debug logging for detailed error information

---

**🎉 You're ready to go! The CRM API integration is fully functional and production-ready.**