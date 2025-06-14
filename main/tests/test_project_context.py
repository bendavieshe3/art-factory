"""
Tests for session-based project context management.

This module provides comprehensive tests for the project context utilities
to ensure robust session management and proper fallback behavior.
"""
from unittest.mock import Mock

from django.test import RequestFactory, TestCase

from main.models import Project
from main.utils.project_context import (
    PROJECT_CONTEXT_SESSION_KEY,
    clear_project_context,
    ensure_project_context,
    get_current_project,
    get_project_aware_context,
    get_project_context_from_request_params,
    set_project_context,
)


class ProjectContextTestCase(TestCase):
    """Test cases for project context management utilities."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        
        # Create test projects
        self.active_project = Project.objects.create(
            name="Active Test Project",
            description="An active project for testing",
            status="active"
        )
        
        self.inactive_project = Project.objects.create(
            name="Inactive Test Project", 
            description="An inactive project for testing",
            status="archived"
        )
    
    def _create_request_with_session(self, path='/', **session_data):
        """Helper to create request with session data."""
        request = self.factory.get(path)
        request.session = {}
        request.session.update(session_data)
        return request
    
    def _create_request_without_session(self, path='/'):
        """Helper to create request without session."""
        request = self.factory.get(path)
        # Don't set session attribute to simulate no session
        return request


class GetCurrentProjectTestCase(ProjectContextTestCase):
    """Test get_current_project function."""
    
    def test_get_current_project_with_valid_session(self):
        """Test retrieving project from valid session context."""
        request = self._create_request_with_session(
            **{PROJECT_CONTEXT_SESSION_KEY: self.active_project.id}
        )
        
        project = get_current_project(request)
        
        self.assertEqual(project, self.active_project)
    
    def test_get_current_project_no_session(self):
        """Test handling request without session."""
        request = self._create_request_without_session()
        
        project = get_current_project(request)
        
        self.assertIsNone(project)
    
    def test_get_current_project_empty_session(self):
        """Test handling empty session."""
        request = self._create_request_with_session()
        
        project = get_current_project(request)
        
        self.assertIsNone(project)
    
    def test_get_current_project_nonexistent_id(self):
        """Test handling nonexistent project ID in session."""
        request = self._create_request_with_session(
            **{PROJECT_CONTEXT_SESSION_KEY: 99999}
        )
        
        project = get_current_project(request)
        
        self.assertIsNone(project)
        # Session should be cleared of invalid ID
        self.assertNotIn(PROJECT_CONTEXT_SESSION_KEY, request.session)
    
    def test_get_current_project_inactive_project(self):
        """Test handling inactive project ID in session."""
        request = self._create_request_with_session(
            **{PROJECT_CONTEXT_SESSION_KEY: self.inactive_project.id}
        )
        
        project = get_current_project(request)
        
        self.assertIsNone(project)
        # Session should be cleared of inactive project
        self.assertNotIn(PROJECT_CONTEXT_SESSION_KEY, request.session)
    
    def test_get_current_project_invalid_id_format(self):
        """Test handling invalid project ID format in session."""
        request = self._create_request_with_session(
            **{PROJECT_CONTEXT_SESSION_KEY: "invalid_id"}
        )
        
        project = get_current_project(request)
        
        self.assertIsNone(project)
        # Session should be cleared of invalid ID
        self.assertNotIn(PROJECT_CONTEXT_SESSION_KEY, request.session)


class SetProjectContextTestCase(ProjectContextTestCase):
    """Test set_project_context function."""
    
    def test_set_project_context_valid_project(self):
        """Test setting valid active project in session."""
        request = self._create_request_with_session()
        
        set_project_context(request, self.active_project)
        
        self.assertEqual(request.session[PROJECT_CONTEXT_SESSION_KEY], self.active_project.id)
    
    def test_set_project_context_none_clears_session(self):
        """Test setting None clears session context."""
        request = self._create_request_with_session(
            **{PROJECT_CONTEXT_SESSION_KEY: self.active_project.id}
        )
        
        set_project_context(request, None)
        
        self.assertNotIn(PROJECT_CONTEXT_SESSION_KEY, request.session)
    
    def test_set_project_context_inactive_project_rejected(self):
        """Test setting inactive project is rejected."""
        request = self._create_request_with_session()
        
        set_project_context(request, self.inactive_project)
        
        self.assertNotIn(PROJECT_CONTEXT_SESSION_KEY, request.session)
    
    def test_set_project_context_no_session(self):
        """Test handling request without session."""
        request = self._create_request_without_session()
        
        # Should not raise error
        set_project_context(request, self.active_project)


class ClearProjectContextTestCase(ProjectContextTestCase):
    """Test clear_project_context function."""
    
    def test_clear_project_context_removes_from_session(self):
        """Test clearing project context removes from session."""
        request = self._create_request_with_session(
            **{PROJECT_CONTEXT_SESSION_KEY: self.active_project.id}
        )
        
        clear_project_context(request)
        
        self.assertNotIn(PROJECT_CONTEXT_SESSION_KEY, request.session)
    
    def test_clear_project_context_empty_session(self):
        """Test clearing from empty session doesn't error."""
        request = self._create_request_with_session()
        
        # Should not raise error
        clear_project_context(request)
        
        self.assertNotIn(PROJECT_CONTEXT_SESSION_KEY, request.session)
    
    def test_clear_project_context_no_session(self):
        """Test handling request without session."""
        request = self._create_request_without_session()
        
        # Should not raise error
        clear_project_context(request)


class GetProjectContextFromRequestParamsTestCase(ProjectContextTestCase):
    """Test get_project_context_from_request_params function."""
    
    def test_get_project_from_get_params(self):
        """Test retrieving project from GET parameters."""
        request = self.factory.get('/', {'project': str(self.active_project.id)})
        request.session = {}
        
        project = get_project_context_from_request_params(request)
        
        self.assertEqual(project, self.active_project)
    
    def test_get_project_from_post_params(self):
        """Test retrieving project from POST parameters."""
        request = self.factory.post('/', {'project': str(self.active_project.id)})
        request.session = {}
        
        project = get_project_context_from_request_params(request)
        
        self.assertEqual(project, self.active_project)
    
    def test_get_project_custom_param_name(self):
        """Test retrieving project with custom parameter name."""
        request = self.factory.get('/', {'custom_project': str(self.active_project.id)})
        request.session = {}
        
        project = get_project_context_from_request_params(request, 'custom_project')
        
        self.assertEqual(project, self.active_project)
    
    def test_get_project_no_param(self):
        """Test handling request without project parameter."""
        request = self.factory.get('/')
        request.session = {}
        
        project = get_project_context_from_request_params(request)
        
        self.assertIsNone(project)
    
    def test_get_project_invalid_param(self):
        """Test handling invalid project ID parameter."""
        request = self.factory.get('/', {'project': 'invalid'})
        request.session = {}
        
        project = get_project_context_from_request_params(request)
        
        self.assertIsNone(project)
    
    def test_get_project_nonexistent_param(self):
        """Test handling nonexistent project ID parameter."""
        request = self.factory.get('/', {'project': '99999'})
        request.session = {}
        
        project = get_project_context_from_request_params(request)
        
        self.assertIsNone(project)
    
    def test_get_project_inactive_param(self):
        """Test handling inactive project ID parameter."""
        request = self.factory.get('/', {'project': str(self.inactive_project.id)})
        request.session = {}
        
        project = get_project_context_from_request_params(request)
        
        self.assertIsNone(project)


class EnsureProjectContextTestCase(ProjectContextTestCase):
    """Test ensure_project_context function."""
    
    def test_ensure_project_param_takes_priority(self):
        """Test that request parameter takes priority over session."""
        # Create second project for testing priority
        other_project = Project.objects.create(
            name="Other Project",
            description="Another project",
            status="active"
        )
        
        request = self.factory.get('/', {'project': str(self.active_project.id)})
        request.session = {PROJECT_CONTEXT_SESSION_KEY: other_project.id}
        
        project = ensure_project_context(request)
        
        self.assertEqual(project, self.active_project)
        # Session should be updated with new project
        self.assertEqual(request.session[PROJECT_CONTEXT_SESSION_KEY], self.active_project.id)
    
    def test_ensure_project_falls_back_to_session(self):
        """Test fallback to session when no parameter provided."""
        request = self.factory.get('/')
        request.session = {PROJECT_CONTEXT_SESSION_KEY: self.active_project.id}
        
        project = ensure_project_context(request)
        
        self.assertEqual(project, self.active_project)
    
    def test_ensure_project_no_context_returns_none(self):
        """Test returns None when no context available."""
        request = self.factory.get('/')
        request.session = {}
        
        project = ensure_project_context(request)
        
        self.assertIsNone(project)
    
    def test_ensure_project_invalid_param_uses_session(self):
        """Test invalid parameter falls back to session."""
        request = self.factory.get('/', {'project': 'invalid'})
        request.session = {PROJECT_CONTEXT_SESSION_KEY: self.active_project.id}
        
        project = ensure_project_context(request)
        
        self.assertEqual(project, self.active_project)


class GetProjectAwareContextTestCase(ProjectContextTestCase):
    """Test get_project_aware_context function."""
    
    def test_get_project_aware_context_with_project(self):
        """Test context generation with project set."""
        request = self._create_request_with_session(
            **{PROJECT_CONTEXT_SESSION_KEY: self.active_project.id}
        )
        
        context = get_project_aware_context(request, test_var="test_value")
        
        self.assertEqual(context['current_project'], self.active_project)
        self.assertEqual(context['test_var'], "test_value")
    
    def test_get_project_aware_context_no_project(self):
        """Test context generation without project set."""
        request = self._create_request_with_session()
        
        context = get_project_aware_context(request, test_var="test_value")
        
        self.assertIsNone(context['current_project'])
        self.assertEqual(context['test_var'], "test_value")
    
    def test_get_project_aware_context_empty(self):
        """Test context generation with no additional variables."""
        request = self._create_request_with_session(
            **{PROJECT_CONTEXT_SESSION_KEY: self.active_project.id}
        )
        
        context = get_project_aware_context(request)
        
        self.assertEqual(context['current_project'], self.active_project)
        self.assertEqual(len(context), 1)  # Only current_project


class ProjectContextIntegrationTestCase(ProjectContextTestCase):
    """Integration tests for complete project context workflows."""
    
    def test_complete_project_context_workflow(self):
        """Test complete workflow: set, get, clear."""
        request = self._create_request_with_session()
        
        # Initially no project
        self.assertIsNone(get_current_project(request))
        
        # Set project
        set_project_context(request, self.active_project)
        project = get_current_project(request)
        self.assertEqual(project, self.active_project)
        
        # Clear project
        clear_project_context(request)
        self.assertIsNone(get_current_project(request))
    
    def test_project_context_persistence_across_requests(self):
        """Test that project context persists across simulated requests."""
        # Simulate first request setting context
        request1 = self._create_request_with_session()
        set_project_context(request1, self.active_project)
        
        # Simulate second request with same session data
        request2 = self._create_request_with_session(
            **{PROJECT_CONTEXT_SESSION_KEY: self.active_project.id}
        )
        
        project = get_current_project(request2)
        self.assertEqual(project, self.active_project)
    
    def test_automatic_cleanup_of_deleted_project(self):
        """Test automatic cleanup when project is deleted."""
        request = self._create_request_with_session(
            **{PROJECT_CONTEXT_SESSION_KEY: self.active_project.id}
        )
        
        # Verify project is initially found
        project = get_current_project(request)
        self.assertEqual(project, self.active_project)
        
        # Delete the project
        project_id = self.active_project.id
        self.active_project.delete()
        
        # Verify project context is automatically cleared
        project = get_current_project(request)
        self.assertIsNone(project)
        self.assertNotIn(PROJECT_CONTEXT_SESSION_KEY, request.session)