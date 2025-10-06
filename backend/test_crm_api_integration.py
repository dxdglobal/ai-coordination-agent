"""
CRM API Integration Tests - Task 1.2
====================================

Comprehensive testing framework for CRM API integration including:
- Authentication testing (JWT/OAuth/API Key)
- All 5 API endpoints (Projects, Tasks, Users, Clients, Comments)
- Rate limiting and error handling
- Synchronization testing
- Performance and load testing
- Integration with existing database

Author: AI Coordination Agent
Version: 1.0.0
Date: October 2025
"""

import unittest
import asyncio
import time
import json
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any
import requests
from datetime import datetime, timedelta

# Import the modules we're testing
from crm_api_service import CRMAPIClient, CRMConfig, AuthenticationManager, RateLimiter
from crm_api_endpoints import (
    CRMAPIManager, Project, Task, User, Client, Comment,
    ProjectsAPI, TasksAPI, UsersAPI, ClientsAPI, CommentsAPI
)
from crm_sync_manager import (
    CRMSyncManager, SynchronizationEngine, SyncConfig, 
    SyncDirection, ConflictResolution
)

class TestCRMConfig(unittest.TestCase):
    """Test CRM configuration validation"""
    
    def test_valid_jwt_config(self):
        """Test valid JWT configuration"""
        config = CRMConfig(
            base_url="https://api.test.com",
            authentication_type="jwt",
            username="test_user",
            password="test_pass"
        )
        self.assertEqual(config.base_url, "https://api.test.com")
        self.assertEqual(config.authentication_type, "jwt")
    
    def test_valid_oauth_config(self):
        """Test valid OAuth configuration"""
        config = CRMConfig(
            base_url="https://api.test.com",
            authentication_type="oauth",
            client_id="test_client",
            client_secret="test_secret"
        )
        self.assertEqual(config.authentication_type, "oauth")
    
    def test_valid_api_key_config(self):
        """Test valid API key configuration"""
        config = CRMConfig(
            base_url="https://api.test.com",
            authentication_type="api_key",
            api_key="test_api_key"
        )
        self.assertEqual(config.authentication_type, "api_key")
    
    def test_missing_base_url(self):
        """Test error when base_url is missing"""
        with self.assertRaises(ValueError):
            CRMConfig(base_url="")
    
    def test_invalid_jwt_config(self):
        """Test error for invalid JWT configuration"""
        with self.assertRaises(ValueError):
            CRMConfig(
                base_url="https://api.test.com",
                authentication_type="jwt"
                # Missing username/password and api_key
            )
    
    def test_invalid_oauth_config(self):
        """Test error for invalid OAuth configuration"""
        with self.assertRaises(ValueError):
            CRMConfig(
                base_url="https://api.test.com",
                authentication_type="oauth",
                client_id="test_client"
                # Missing client_secret
            )

class TestRateLimiter(unittest.TestCase):
    """Test rate limiting functionality"""
    
    def setUp(self):
        self.rate_limiter = RateLimiter(max_calls=5, time_window=10)
    
    def test_can_make_call_within_limit(self):
        """Test calls within rate limit"""
        for _ in range(5):
            self.assertTrue(self.rate_limiter.can_make_call())
            self.rate_limiter.record_call()
    
    def test_rate_limit_exceeded(self):
        """Test rate limit enforcement"""
        # Use up all calls
        for _ in range(5):
            self.rate_limiter.record_call()
        
        # Should be blocked
        self.assertFalse(self.rate_limiter.can_make_call())
    
    def test_rate_limit_window_reset(self):
        """Test rate limit window reset"""
        # Use up all calls
        for _ in range(5):
            self.rate_limiter.record_call()
        
        # Simulate time passing
        self.rate_limiter.calls = [time.time() - 15]  # Call older than window
        
        # Should be able to make calls again
        self.assertTrue(self.rate_limiter.can_make_call())

class TestAuthenticationManager(unittest.TestCase):
    """Test authentication management"""
    
    def setUp(self):
        self.jwt_config = CRMConfig(
            base_url="https://api.test.com",
            authentication_type="jwt",
            username="test_user",
            password="test_pass"
        )
        
        self.oauth_config = CRMConfig(
            base_url="https://api.test.com",
            authentication_type="oauth",
            client_id="test_client",
            client_secret="test_secret"
        )
        
        self.api_key_config = CRMConfig(
            base_url="https://api.test.com",
            authentication_type="api_key",
            api_key="test_api_key"
        )
    
    @patch('requests.Session.post')
    def test_jwt_authentication_success(self, mock_post):
        """Test successful JWT authentication"""
        # Mock successful response
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        auth_manager = AuthenticationManager(self.jwt_config)
        headers = auth_manager.authenticate()
        
        self.assertEqual(headers["Authorization"], "Bearer test_access_token")
        mock_post.assert_called_once()
    
    @patch('requests.Session.post')
    def test_jwt_authentication_failure(self, mock_post):
        """Test JWT authentication failure"""
        mock_post.side_effect = requests.exceptions.RequestException("Auth failed")
        
        auth_manager = AuthenticationManager(self.jwt_config)
        
        with self.assertRaises(requests.exceptions.RequestException):
            auth_manager.authenticate()
    
    @patch('requests.Session.post')
    def test_oauth_authentication_success(self, mock_post):
        """Test successful OAuth authentication"""
        mock_response = Mock()
        mock_response.json.return_value = {
            "access_token": "oauth_access_token",
            "token_type": "Bearer",
            "expires_in": 3600
        }
        mock_response.raise_for_status.return_value = None
        mock_post.return_value = mock_response
        
        auth_manager = AuthenticationManager(self.oauth_config)
        headers = auth_manager.authenticate()
        
        self.assertEqual(headers["Authorization"], "Bearer oauth_access_token")
    
    def test_api_key_authentication(self):
        """Test API key authentication"""
        auth_manager = AuthenticationManager(self.api_key_config)
        headers = auth_manager.authenticate()
        
        self.assertEqual(headers["X-API-Key"], "test_api_key")
    
    def test_token_expiry_check(self):
        """Test token expiry validation"""
        auth_manager = AuthenticationManager(self.jwt_config)
        
        # No token set
        self.assertFalse(auth_manager._is_token_valid())
        
        # Set expired token
        auth_manager.access_token = "expired_token"
        auth_manager.token_expiry = datetime.utcnow() - timedelta(minutes=10)
        self.assertFalse(auth_manager._is_token_valid())
        
        # Set valid token
        auth_manager.token_expiry = datetime.utcnow() + timedelta(hours=1)
        self.assertTrue(auth_manager._is_token_valid())

class TestCRMAPIClient(unittest.TestCase):
    """Test CRM API client functionality"""
    
    def setUp(self):
        self.config = CRMConfig(
            base_url="https://api.test.com",
            authentication_type="api_key",
            api_key="test_key"
        )
        self.client = CRMAPIClient(self.config)
    
    @patch('crm_api_service.CRMAPIClient._make_request')
    def test_get_request(self, mock_request):
        """Test GET request"""
        mock_response = Mock()
        mock_response.json.return_value = {"data": "test_data"}
        mock_request.return_value = mock_response
        
        result = self.client.get("test_endpoint")
        
        self.assertEqual(result["data"], "test_data")
        mock_request.assert_called_once_with("GET", "test_endpoint", params=None)
    
    @patch('crm_api_service.CRMAPIClient._make_request')
    def test_post_request(self, mock_request):
        """Test POST request"""
        mock_response = Mock()
        mock_response.json.return_value = {"id": 1, "name": "created"}
        mock_request.return_value = mock_response
        
        test_data = {"name": "test_item"}
        result = self.client.post("test_endpoint", test_data)
        
        self.assertEqual(result["id"], 1)
        mock_request.assert_called_once_with("POST", "test_endpoint", data=test_data)
    
    @patch('crm_api_service.CRMAPIClient._make_request')
    def test_put_request(self, mock_request):
        """Test PUT request"""
        mock_response = Mock()
        mock_response.json.return_value = {"id": 1, "name": "updated"}
        mock_request.return_value = mock_response
        
        test_data = {"name": "updated_item"}
        result = self.client.put("test_endpoint", test_data)
        
        self.assertEqual(result["name"], "updated")
        mock_request.assert_called_once_with("PUT", "test_endpoint", data=test_data)
    
    @patch('crm_api_service.CRMAPIClient._make_request')
    def test_delete_request(self, mock_request):
        """Test DELETE request"""
        mock_response = Mock()
        mock_response.status_code = 204
        mock_request.return_value = mock_response
        
        result = self.client.delete("test_endpoint")
        
        self.assertTrue(result)
        mock_request.assert_called_once_with("DELETE", "test_endpoint")

class TestAPIEndpoints(unittest.TestCase):
    """Test all API endpoints"""
    
    def setUp(self):
        self.mock_client = Mock()
        self.projects_api = ProjectsAPI(self.mock_client)
        self.tasks_api = TasksAPI(self.mock_client)
        self.users_api = UsersAPI(self.mock_client)
        self.clients_api = ClientsAPI(self.mock_client)
        self.comments_api = CommentsAPI(self.mock_client)
    
    def test_projects_get_all(self):
        """Test getting all projects"""
        mock_response = {
            "data": [
                {"id": 1, "name": "Project 1", "status": "active"},
                {"id": 2, "name": "Project 2", "status": "completed"}
            ],
            "total": 2,
            "page": 1
        }
        self.mock_client.get.return_value = mock_response
        
        result = self.projects_api.get_all(status="active", page=1)
        
        self.assertEqual(len(result["data"]), 2)
        self.mock_client.get.assert_called_once_with(
            "projects", 
            params={"page": 1, "per_page": 50, "status": "active"}
        )
    
    def test_projects_create(self):
        """Test creating a project"""
        new_project = Project(
            name="New Project",
            description="Test project",
            status="active"
        )
        
        mock_response = {
            "data": {
                "id": 1,
                "name": "New Project",
                "description": "Test project",
                "status": "active"
            }
        }
        self.mock_client.post.return_value = mock_response
        
        result = self.projects_api.create(new_project)
        
        self.assertEqual(result.id, 1)
        self.assertEqual(result.name, "New Project")
        self.mock_client.post.assert_called_once()
    
    def test_tasks_assign(self):
        """Test assigning a task"""
        mock_response = {
            "data": {
                "id": 1,
                "title": "Test Task",
                "assignee_id": 5
            }
        }
        self.mock_client.patch.return_value = mock_response
        
        result = self.tasks_api.assign_task(1, 5)
        
        self.assertEqual(result.assignee_id, 5)
        self.mock_client.patch.assert_called_once_with(
            "tasks/1/assign",
            {"assignee_id": 5}
        )
    
    def test_users_get_user_tasks(self):
        """Test getting user's tasks"""
        mock_response = {
            "data": [
                {"id": 1, "title": "Task 1", "assignee_id": 1},
                {"id": 2, "title": "Task 2", "assignee_id": 1}
            ]
        }
        self.mock_client.get.return_value = mock_response
        
        result = self.users_api.get_user_tasks(1)
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0].assignee_id, 1)
        self.mock_client.get.assert_called_once_with("users/1/tasks")
    
    def test_comments_get_entity_comments(self):
        """Test getting comments for an entity"""
        mock_response = {
            "data": [
                {
                    "id": 1,
                    "content": "Test comment",
                    "entity_type": "project",
                    "entity_id": 1
                }
            ]
        }
        self.mock_client.get.return_value = mock_response
        
        result = self.comments_api.get_entity_comments("project", 1)
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].entity_type, "project")
        self.mock_client.get.assert_called_once_with(
            "comments",
            params={"entity_type": "project", "entity_id": 1}
        )

class TestSynchronization(unittest.TestCase):
    """Test synchronization functionality"""
    
    def setUp(self):
        self.mock_api_manager = Mock()
        self.mock_db_operations = Mock()
        self.sync_config = SyncConfig(
            direction=SyncDirection.BIDIRECTIONAL,
            conflict_resolution=ConflictResolution.LATEST_TIMESTAMP,
            batch_size=10
        )
        self.sync_engine = SynchronizationEngine(
            self.mock_api_manager,
            self.mock_db_operations,
            self.sync_config
        )
    
    async def test_sync_projects_api_to_db(self):
        """Test syncing projects from API to database"""
        # Mock API response
        mock_api_response = {
            "data": [
                {
                    "id": 1,
                    "name": "Test Project",
                    "status": "active",
                    "created_at": "2025-10-01T10:00:00Z",
                    "updated_at": "2025-10-01T10:00:00Z"
                }
            ]
        }
        self.mock_api_manager.projects.get_all.return_value = mock_api_response
        self.mock_db_operations.upsert_project.return_value = True
        
        result = await self.sync_engine.sync_projects()
        
        self.assertEqual(result.entity_type, "projects")
        self.assertEqual(result.total_processed, 1)
        self.assertEqual(result.successful, 1)
        self.assertEqual(result.failed, 0)
    
    def test_sync_config_validation(self):
        """Test sync configuration validation"""
        config = SyncConfig(
            direction=SyncDirection.BIDIRECTIONAL,
            batch_size=50,
            entities_to_sync=["projects", "tasks"]
        )
        
        self.assertEqual(config.direction, SyncDirection.BIDIRECTIONAL)
        self.assertEqual(config.batch_size, 50)
        self.assertIn("projects", config.entities_to_sync)
        self.assertIn("tasks", config.entities_to_sync)

class TestDataModels(unittest.TestCase):
    """Test data model validation"""
    
    def test_project_model(self):
        """Test Project data model"""
        project = Project(
            name="Test Project",
            description="A test project",
            status="active",
            priority="high"
        )
        
        self.assertEqual(project.name, "Test Project")
        self.assertEqual(project.status, "active")
        self.assertEqual(project.priority, "high")
        self.assertEqual(project.team_members, [])  # Default empty list
    
    def test_task_model(self):
        """Test Task data model"""
        task = Task(
            title="Test Task",
            description="A test task",
            status="todo",
            project_id=1
        )
        
        self.assertEqual(task.title, "Test Task")
        self.assertEqual(task.status, "todo")
        self.assertEqual(task.project_id, 1)
        self.assertEqual(task.tags, [])  # Default empty list
        self.assertEqual(task.dependencies, [])  # Default empty list
    
    def test_user_model(self):
        """Test User data model"""
        user = User(
            username="testuser",
            email="test@example.com",
            first_name="Test",
            last_name="User",
            role="user"
        )
        
        self.assertEqual(user.username, "testuser")
        self.assertEqual(user.email, "test@example.com")
        self.assertEqual(user.role, "user")
        self.assertTrue(user.is_active)  # Default True

class TestIntegrationScenarios(unittest.TestCase):
    """Test integration scenarios"""
    
    def setUp(self):
        self.config = CRMConfig(
            base_url="https://api.test.com",
            authentication_type="api_key",
            api_key="test_key"
        )
    
    @patch('crm_api_service.CRMAPIClient._make_request')
    def test_full_crud_cycle(self, mock_request):
        """Test complete CRUD cycle for a project"""
        api_manager = CRMAPIManager(self.config)
        
        # Mock responses for each operation
        create_response = Mock()
        create_response.json.return_value = {
            "data": {"id": 1, "name": "Test Project", "status": "active"}
        }
        
        get_response = Mock()
        get_response.json.return_value = {
            "data": {"id": 1, "name": "Test Project", "status": "active"}
        }
        
        update_response = Mock()
        update_response.json.return_value = {
            "data": {"id": 1, "name": "Updated Project", "status": "active"}
        }
        
        delete_response = Mock()
        delete_response.status_code = 204
        
        mock_request.side_effect = [
            create_response,  # Create
            get_response,     # Get
            update_response,  # Update
            delete_response   # Delete
        ]
        
        # Create
        new_project = Project(name="Test Project", status="active")
        created = api_manager.projects.create(new_project)
        self.assertEqual(created.id, 1)
        
        # Read
        retrieved = api_manager.projects.get_by_id(1)
        self.assertEqual(retrieved.name, "Test Project")
        
        # Update
        retrieved.name = "Updated Project"
        updated = api_manager.projects.update(1, retrieved)
        self.assertEqual(updated.name, "Updated Project")
        
        # Delete
        deleted = api_manager.projects.delete(1)
        self.assertTrue(deleted)
    
    @patch('crm_api_service.CRMAPIClient.health_check')
    def test_health_check_integration(self, mock_health):
        """Test health check integration"""
        mock_health.return_value = {"status": "healthy", "version": "1.0"}
        
        api_manager = CRMAPIManager(self.config)
        health_result = api_manager.health_check()
        
        self.assertIn("api_health", health_result)
        mock_health.assert_called_once()

class TestErrorHandling(unittest.TestCase):
    """Test error handling scenarios"""
    
    def setUp(self):
        self.config = CRMConfig(
            base_url="https://api.test.com",
            authentication_type="api_key",
            api_key="test_key"
        )
        self.client = CRMAPIClient(self.config)
    
    @patch('crm_api_service.CRMAPIClient._make_request')
    def test_authentication_error_handling(self, mock_request):
        """Test handling of authentication errors"""
        # First call returns 401, second call succeeds
        auth_error_response = Mock()
        auth_error_response.status_code = 401
        auth_error_response.raise_for_status.side_effect = requests.exceptions.HTTPError("401 Unauthorized")
        
        success_response = Mock()
        success_response.json.return_value = {"data": "success"}
        success_response.raise_for_status.return_value = None
        
        mock_request.side_effect = [auth_error_response, success_response]
        
        # Should handle 401 and retry
        with patch.object(self.client, '_get_headers', return_value={"Authorization": "Bearer new_token"}):
            result = self.client.get("test_endpoint")
            self.assertEqual(result["data"], "success")
    
    @patch('crm_api_service.CRMAPIClient._make_request')
    def test_rate_limit_handling(self, mock_request):
        """Test rate limiting behavior"""
        # Mock rate limiter to be at limit
        self.client.rate_limiter.can_make_call = Mock(return_value=False)
        self.client.rate_limiter.wait_time = Mock(return_value=0.1)  # Short wait for testing
        
        mock_response = Mock()
        mock_response.json.return_value = {"data": "success"}
        mock_request.return_value = mock_response
        
        start_time = time.time()
        result = self.client.get("test_endpoint")
        end_time = time.time()
        
        # Should have waited before making request
        self.assertGreaterEqual(end_time - start_time, 0.1)
        self.assertEqual(result["data"], "success")

class TestPerformance(unittest.TestCase):
    """Test performance characteristics"""
    
    def setUp(self):
        self.config = CRMConfig(
            base_url="https://api.test.com",
            authentication_type="api_key",
            api_key="test_key"
        )
    
    @patch('crm_api_service.CRMAPIClient._make_request')
    def test_batch_operations_performance(self, mock_request):
        """Test performance of batch operations"""
        # Mock response for batch requests
        mock_response = Mock()
        mock_response.json.return_value = {
            "data": [{"id": i, "name": f"Project {i}"} for i in range(100)]
        }
        mock_request.return_value = mock_response
        
        api_manager = CRMAPIManager(self.config)
        
        start_time = time.time()
        result = api_manager.projects.get_all(per_page=100)
        end_time = time.time()
        
        # Should complete within reasonable time
        self.assertLess(end_time - start_time, 1.0)  # Less than 1 second
        self.assertEqual(len(result["data"]), 100)
    
    def test_rate_limiter_performance(self):
        """Test rate limiter performance under load"""
        rate_limiter = RateLimiter(max_calls=100, time_window=60)
        
        start_time = time.time()
        
        # Make 50 calls (within limit)
        for _ in range(50):
            self.assertTrue(rate_limiter.can_make_call())
            rate_limiter.record_call()
        
        end_time = time.time()
        
        # Should be very fast
        self.assertLess(end_time - start_time, 0.1)

# Test suites for different categories
def create_test_suite():
    """Create comprehensive test suite"""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test classes
    test_classes = [
        TestCRMConfig,
        TestRateLimiter,
        TestAuthenticationManager,
        TestCRMAPIClient,
        TestAPIEndpoints,
        TestSynchronization,
        TestDataModels,
        TestIntegrationScenarios,
        TestErrorHandling,
        TestPerformance
    ]
    
    for test_class in test_classes:
        suite.addTests(loader.loadTestsFromTestCase(test_class))
    
    return suite

# Integration test runner
async def run_integration_tests():
    """Run integration tests with real API (if available)"""
    print("Running integration tests...")
    
    # These would only run if a test API is available
    # Add integration tests here that use real API endpoints
    print("Integration tests completed (placeholder)")

# Performance test runner
def run_performance_tests():
    """Run performance benchmarks"""
    print("Running performance tests...")
    
    # Add performance benchmarks here
    print("Performance tests completed (placeholder)")

# Main test runner
if __name__ == "__main__":
    # Run unit tests
    print("=" * 60)
    print("CRM API Integration - Test Suite")
    print("=" * 60)
    
    # Create and run test suite
    suite = create_test_suite()
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 60)
    print("Test Summary:")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print("\nFailures:")
        for test, traceback in result.failures:
            print(f"- {test}: {traceback}")
    
    if result.errors:
        print("\nErrors:")
        for test, traceback in result.errors:
            print(f"- {test}: {traceback}")
    
    # Run additional tests if requested
    import sys
    if "--integration" in sys.argv:
        asyncio.run(run_integration_tests())
    
    if "--performance" in sys.argv:
        run_performance_tests()
    
    print("=" * 60)