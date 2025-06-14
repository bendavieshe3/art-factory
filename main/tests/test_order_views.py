"""
Tests for order views and template functionality.
"""

import re

from django.test import Client, TestCase, override_settings

from main.models import FactoryMachineDefinition, Project


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class OrderViewTestCase(TestCase):
    """Test order view functionality and template rendering."""

    def setUp(self):
        """Set up test client and factory machine."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            description="Test model for view testing",
            provider="test-provider",
            modality="image",
            parameter_schema={"width": 512, "height": 512},
            default_parameters={"width": 512, "height": 512, "enable_safety_checker": False},
            is_active=True,
        )

    def test_order_page_no_project_dropdown(self):
        """Test that order page no longer has project dropdown (uses session context instead)."""
        # Create test projects
        project1 = Project.objects.create(name="Test Project 1", description="First test project", status="active")
        project2 = Project.objects.create(name="Test Project 2", description="Second test project", status="active")
        project3 = Project.objects.create(name="Inactive Project", description="Should not appear", status="inactive")

        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        # Should NOT include projects dropdown (projects are managed via session context now)
        self.assertNotContains(response, 'name="project"', msg_prefix="Project dropdown should be removed")
        self.assertNotContains(response, 'id="project"', msg_prefix="Project dropdown ID should not exist")

        # Project names should not appear in form since dropdown is removed
        self.assertNotContains(response, "Test Project 1")
        self.assertNotContains(response, "Test Project 2")

    def test_order_page_sets_project_context_from_url(self):
        """Test that order page sets session context when coming from project page."""
        # Create test project
        test_project = Project.objects.create(
            name="Pre-selected Project", description="Should be pre-selected", status="active"
        )

        # Visit order page with project parameter (simulating click from project page)
        response = self.client.get(f"/order/?project={test_project.id}")
        self.assertEqual(response.status_code, 200)

        # Should include current_project in context (from session)
        self.assertIn("current_project", response.context)
        self.assertEqual(response.context["current_project"], test_project)

        # Should show project context indicator instead of dropdown
        self.assertContains(response, "Pre-selected Project", msg_prefix="Project name should appear in context indicator")

        # Should NOT contain project dropdown
        self.assertNotContains(response, 'name="project"')

    def test_order_page_handles_invalid_project_parameter(self):
        """Test that order page handles invalid project ID gracefully."""
        # Visit with non-existent project ID
        response = self.client.get("/order/?project=99999")
        self.assertEqual(response.status_code, 200)

        # Should not have current_project set
        self.assertIsNone(response.context.get("current_project"))

        # Should not contain project dropdown
        self.assertNotContains(response, 'name="project"')

        # Visit with invalid project ID format
        response = self.client.get("/order/?project=invalid")
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.context.get("current_project"))

        # Should not contain project dropdown
        self.assertNotContains(response, 'name="project"')

    def test_order_form_javascript_components_loaded(self):
        """Test that all required JavaScript components are loaded for order functionality."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        # Should include critical JavaScript functions from components
        required_functions = [
            "handleOrderSubmission",  # from order_progress_management.html
            "loadPageData",  # from order_recent_data.html
            "loadFormValues",  # from order_form_management.html
            "saveFormValues",  # from order_form_management.html
            "updateTotalProducts",  # from order_form_management.html
            "showOrderProgress",  # from order_progress_management.html
            "updateDynamicParameters",  # from order_machine_parameters.html
            "showErrorBanner",  # from order_template_management.html
        ]

        for function in required_functions:
            self.assertContains(response, function, msg_prefix=f"Missing required JavaScript function: {function}")

        # Should include form field management
        self.assertContains(response, 'id="machine"', msg_prefix="Missing machine select field")
        self.assertContains(response, 'id="prompt"', msg_prefix="Missing prompt field")
        self.assertContains(response, 'id="orderForm"', msg_prefix="Missing order form")

        # Should include CSRF token for form submission
        self.assertContains(response, 'name="csrfmiddlewaretoken"', msg_prefix="Missing CSRF token")

    def test_order_form_persistence_functions_loaded(self):
        """Test that form persistence JavaScript functions are loaded and properly configured."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        # Should include form persistence functions
        persistence_functions = [
            "saveFormValues",  # Save form data to localStorage
            "loadFormValues",  # Load form data from localStorage
            "updateTotalProducts",  # Update total calculation
            "changeGenerationCount",  # Generation count controls
        ]

        for function in persistence_functions:
            self.assertContains(response, function, msg_prefix=f"Missing form persistence function: {function}")

        # Should include localStorage operations
        self.assertContains(response, "localStorage.setItem", msg_prefix="Missing localStorage save")
        self.assertContains(response, "localStorage.getItem", msg_prefix="Missing localStorage load")
        self.assertContains(response, "'orderFormData'", msg_prefix="Missing localStorage key")

        # Should include event listeners for form changes
        self.assertContains(response, "addEventListener('change'", msg_prefix="Missing change event listeners")
        self.assertContains(response, "addEventListener('input'", msg_prefix="Missing input event listeners")

        # Should include proper form field references
        form_fields = ["machine", "prompt", "negative_prompt", "title", "generationCount", "batchSize"]
        for field in form_fields:
            self.assertContains(
                response, f"getElementById('{field}')", msg_prefix=f"Missing getElementById reference for field: {field}"
            )

    def test_order_form_has_required_ids(self):
        """Test that order form has all required element IDs for persistence."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        # Check that all form fields have the correct IDs for JavaScript
        required_ids = [
            "machine",  # AI model select
            "prompt",  # Main prompt textarea
            "negative_prompt",  # Negative prompt textarea
            "title",  # Optional title input
            "generationCount",  # Generation count input
            "batchSize",  # Batch size select
            "totalProducts",  # Total products display
            "orderForm",  # Main form element
        ]

        for element_id in required_ids:
            self.assertContains(response, f'id="{element_id}"', msg_prefix=f"Missing required element ID: {element_id}")

    def test_order_form_initialization_order(self):
        """Test that form components are loaded in the correct order for initialization."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        content = response.content.decode()

        # Find positions of key components
        form_mgmt_pos = content.find("order_form_management.html")
        main_init_pos = content.find("order_main_init.html")
        load_form_values_pos = content.find("loadFormValues()")

        # Form management should be loaded before main init
        self.assertLess(form_mgmt_pos, main_init_pos, "Form management component should be loaded before main init")

        # loadFormValues should be called in main init
        self.assertGreater(load_form_values_pos, 0, "loadFormValues() should be called during initialization")

        # Check that DOMContentLoaded handlers are properly structured
        self.assertContains(response, "DOMContentLoaded", msg_prefix="Missing DOMContentLoaded event handlers")
