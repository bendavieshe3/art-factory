"""
Tests for Bootstrap 5 integration and enhanced UI components.
"""
import json
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from unittest.mock import patch

from .models import FactoryMachineDefinition


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)


class BootstrapIntegrationTestCase(TestCase):
    """Test Bootstrap 5 integration and UI enhancements."""
    
    def setUp(self):
        """Set up test client and factory machine."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name='test/bootstrap-model',
            display_name='Bootstrap Test Model',
            description='Test model for Bootstrap UI testing',
            provider='test-provider',
            modality='image',
            parameter_schema={'width': 1024, 'height': 1024},
            default_parameters={'width': 1024, 'height': 1024, 'enable_safety_checker': False},
            is_active=True
        )
    
    def test_bootstrap_order_page_loads(self):
        """Test that Bootstrap order page loads correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check Bootstrap CSS is loaded
        self.assertContains(response, 'bootstrap')
        
        # Check Bootstrap Icons are loaded
        self.assertContains(response, 'bootstrap-icons')
        
        # Check our custom toast system is preserved
        self.assertContains(response, 'toast-container')
        self.assertContains(response, 'window.ToastNotification')
    
    def test_bootstrap_components_present(self):
        """Test that Bootstrap components are properly rendered."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check navigation components
        self.assertContains(response, 'navbar')
        self.assertContains(response, 'navbar-brand')
        self.assertContains(response, 'nav-link')
        
        # Check card components
        self.assertContains(response, 'card')
        self.assertContains(response, 'card-header')
        self.assertContains(response, 'card-body')
        
        # Check form components
        self.assertContains(response, 'form-control')
        self.assertContains(response, 'form-label')
        self.assertContains(response, 'btn btn-primary')
        
        # Check grid system
        self.assertContains(response, 'container-fluid')
        self.assertContains(response, 'row')
        self.assertContains(response, 'col-lg-3')
        self.assertContains(response, 'col-lg-9')
    
    def test_sidebar_models_display(self):
        """Test that AI models are displayed in sidebar."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check model appears in sidebar
        self.assertContains(response, 'Bootstrap Test Model')
        self.assertContains(response, 'test-provider')
        self.assertContains(response, 'model-option')
        
        # Check sidebar has proper structure
        self.assertContains(response, 'list-group')
        self.assertContains(response, 'list-group-item')
        self.assertContains(response, 'badge')
    
    def test_advanced_parameters_section(self):
        """Test that advanced parameters section works."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check collapsible advanced section
        self.assertContains(response, 'data-bs-toggle="collapse"')
        self.assertContains(response, 'advancedParams')
        self.assertContains(response, 'Advanced Parameters')
        
        # Check parameter inputs
        self.assertContains(response, 'id="width"')
        self.assertContains(response, 'id="height"')
        self.assertContains(response, 'id="steps"')
        self.assertContains(response, 'id="guidance"')
    
    def test_template_buttons_functionality(self):
        """Test that template buttons are present."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check template buttons
        self.assertContains(response, 'Fantasy Template')
        self.assertContains(response, 'Portrait Template')
        self.assertContains(response, 'Landscape Template')
        
        # Check template functionality
        self.assertContains(response, 'loadTemplate(')
        self.assertContains(response, 'onclick="loadTemplate(\'fantasy\')"')
    
    def test_quantity_controls(self):
        """Test quantity increment/decrement controls."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check quantity input group
        self.assertContains(response, 'input-group')
        self.assertContains(response, 'changeQuantity(-1)')
        self.assertContains(response, 'changeQuantity(1)')
        self.assertContains(response, 'bi-plus')
        self.assertContains(response, 'bi-dash')
    
    def test_form_validation_styling(self):
        """Test that form validation styling is in place."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check required field indicators
        self.assertContains(response, 'text-danger')
        self.assertContains(response, 'required')
        
        # Check form help text
        self.assertContains(response, 'form-text')
        
        # Check form density class
        self.assertContains(response, 'form-dense')
    
    def test_icons_integration(self):
        """Test that Bootstrap Icons are properly integrated."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check various icons are used
        self.assertContains(response, 'bi-palette')  # Logo
        self.assertContains(response, 'bi-plus-circle')  # Add/Create
        self.assertContains(response, 'bi-lightning')  # Submit
        self.assertContains(response, 'bi-cpu')  # AI Models
        self.assertContains(response, 'bi-gear')  # Settings
        self.assertContains(response, 'bi-magic')  # Fantasy template
    
    def test_responsive_design_classes(self):
        """Test that responsive design classes are used."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check responsive breakpoints
        self.assertContains(response, 'col-lg-')
        self.assertContains(response, 'col-md-')
        self.assertContains(response, 'd-md-flex')
        self.assertContains(response, 'navbar-expand-lg')
    
    def test_toast_system_preservation(self):
        """Test that our custom toast system is preserved with Bootstrap."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check toast system is still there and functional
        self.assertContains(response, 'toast-container')
        self.assertContains(response, 'z-index: 1055')  # Higher than Bootstrap modals
        self.assertContains(response, 'ToastNotification.success')
        self.assertContains(response, 'ToastNotification.error')
        
        # Check toast is used in form submission
        self.assertContains(response, 'Order Placed')
        self.assertContains(response, 'Order Failed')
    
    @patch('main.tasks.process_order_items_async')
    def test_bootstrap_form_submission(self, mock_process):
        """Test that Bootstrap form submits correctly."""
        order_data = {
            'title': 'Bootstrap Test Order',
            'prompt': 'test bootstrap integration',
            'machine_id': self.factory_machine.id,
            'quantity': 1,
            'parameters': {
                'width': 1024,
                'height': 1024,
                'num_inference_steps': 25,
                'guidance_scale': 7.5
            }
        }
        
        response = self.client.post(
            '/api/place-order/',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # Verify background processing was triggered
        mock_process.assert_called_once()
    
    def test_javascript_functions_defined(self):
        """Test that required JavaScript functions are defined."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode()
        
        # Check that utility functions are defined
        self.assertIn('window.changeQuantity', content)
        self.assertIn('window.clearForm', content)
        self.assertIn('window.loadTemplate', content)
        
        # Check that event listeners are set up
        self.assertIn('addEventListener', content)
        self.assertIn('DOMContentLoaded', content)