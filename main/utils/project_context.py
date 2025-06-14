"""
Session-based project context management utilities.

This module provides robust session-based project context handling to replace
fragile URL parameter passing. Project context is maintained in the user's
session and can be easily retrieved and modified across views.
"""

import logging
from typing import Optional

from django.http import HttpRequest

from main.models import Project

logger = logging.getLogger(__name__)

# Session key for storing current project context
PROJECT_CONTEXT_SESSION_KEY = "current_project_id"


def get_current_project(request: HttpRequest) -> Optional[Project]:
    """
    Get the current project from session context.

    Args:
        request: Django HttpRequest object

    Returns:
        Project instance if one is set and valid, None otherwise
    """
    if not hasattr(request, "session"):
        logger.warning("Request has no session - cannot retrieve project context")
        return None

    project_id = request.session.get(PROJECT_CONTEXT_SESSION_KEY)
    if not project_id:
        return None

    try:
        # Only return active projects
        project = Project.objects.get(id=project_id, status="active")
        logger.debug(f"Retrieved project context: {project.name} (ID: {project.id})")
        return project
    except Project.DoesNotExist:
        # Project was deleted or deactivated - clear from session
        logger.info(f"Project ID {project_id} no longer exists or inactive - clearing from session")
        clear_project_context(request)
        return None
    except (ValueError, TypeError):
        # Invalid project ID format - clear from session
        logger.warning(f"Invalid project ID format in session: {project_id} - clearing")
        clear_project_context(request)
        return None


def set_project_context(request: HttpRequest, project: Optional[Project]) -> None:
    """
    Set the current project context in the session.

    Args:
        request: Django HttpRequest object
        project: Project instance to set as current, or None to clear
    """
    if not hasattr(request, "session"):
        logger.warning("Request has no session - cannot set project context")
        return

    if project is None:
        clear_project_context(request)
        return

    # Validate project is active
    if project.status != "active":
        logger.warning(f"Attempted to set inactive project {project.id} as context")
        return

    request.session[PROJECT_CONTEXT_SESSION_KEY] = project.id
    logger.debug(f"Set project context: {project.name} (ID: {project.id})")


def clear_project_context(request: HttpRequest) -> None:
    """
    Clear the current project context from the session.

    Args:
        request: Django HttpRequest object
    """
    if not hasattr(request, "session"):
        logger.warning("Request has no session - cannot clear project context")
        return

    if PROJECT_CONTEXT_SESSION_KEY in request.session:
        project_id = request.session[PROJECT_CONTEXT_SESSION_KEY]
        del request.session[PROJECT_CONTEXT_SESSION_KEY]
        logger.debug(f"Cleared project context (was project ID: {project_id})")


def get_project_context_from_request_params(request: HttpRequest, param_name: str = "project") -> Optional[Project]:
    """
    Get project from request parameters (GET/POST) for legacy compatibility.

    This function supports the transition from URL-based to session-based context
    by allowing views to check for project parameters and optionally set session context.

    Args:
        request: Django HttpRequest object
        param_name: Parameter name to check (default: 'project')

    Returns:
        Project instance if parameter is valid, None otherwise
    """
    # Check GET parameters first, then POST
    project_id = request.GET.get(param_name) or request.POST.get(param_name)

    if not project_id:
        return None

    try:
        project = Project.objects.get(id=project_id, status="active")
        logger.debug(f"Retrieved project from request params: {project.name} (ID: {project.id})")
        return project
    except Project.DoesNotExist:
        logger.info(f"Project ID {project_id} from request params does not exist or is inactive")
        return None
    except (ValueError, TypeError):
        logger.warning(f"Invalid project ID format in request params: {project_id}")
        return None


def ensure_project_context(request: HttpRequest, param_name: str = "project") -> Optional[Project]:
    """
    Comprehensive project context resolution with automatic session management.

    This function implements the priority order:
    1. Check for project in request parameters (and set session if found)
    2. Fall back to session-based project context
    3. Return None if no valid project found

    Args:
        request: Django HttpRequest object
        param_name: Parameter name to check for project override

    Returns:
        Project instance if found, None otherwise
    """
    # First priority: check request parameters (for direct navigation)
    project_from_params = get_project_context_from_request_params(request, param_name)
    if project_from_params:
        # Set this as the new session context for future requests
        set_project_context(request, project_from_params)
        return project_from_params

    # Second priority: use existing session context
    return get_current_project(request)


def get_project_aware_context(request: HttpRequest, **additional_context) -> dict:
    """
    Generate context dictionary with project information for templates.

    Args:
        request: Django HttpRequest object
        **additional_context: Additional context variables to include

    Returns:
        Dictionary containing project context and any additional variables
    """
    context = {"current_project": get_current_project(request), **additional_context}

    return context
