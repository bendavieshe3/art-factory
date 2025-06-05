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
            parameter_schema={
                'width': 1024, 
                'height': 1024,
                'steps': 25,
                'guidance': 7.5
            },
            default_parameters={
                'width': 1024, 
                'height': 1024, 
                'steps': 25,
                'guidance': 7.5,
                'enable_safety_checker': False
            },
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
        
        # Check grid system - current layout uses col-lg-8 and col-lg-4
        self.assertContains(response, 'container-fluid')
        self.assertContains(response, 'row')
        self.assertContains(response, 'col-lg-8')
        self.assertContains(response, 'col-lg-4')
    
    def test_models_dropdown_display(self):
        """Test that AI models are displayed in dropdown."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check model selection dropdown
        self.assertContains(response, 'id="machine"')
        self.assertContains(response, 'Select an AI model...')
        
        # Check model appears in dropdown
        self.assertContains(response, 'Bootstrap Test Model')
        self.assertContains(response, 'data-provider="test-provider"')
        self.assertContains(response, 'data-modality="image"')
    
    def test_advanced_parameters_section(self):
        """Test that advanced parameters section works."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check collapsible advanced section
        self.assertContains(response, 'data-bs-toggle="collapse"')
        self.assertContains(response, 'advancedParams')
        self.assertContains(response, 'Advanced Parameters')
        
        # Check that dynamic parameters container exists
        self.assertContains(response, 'id="dynamicParameters"')
        # Parameters are loaded dynamically via JavaScript based on selected model
        self.assertContains(response, 'Select a model to see available parameters')
    
    
    def test_quantity_controls(self):
        """Test quantity increment/decrement controls."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check quantity input group
        self.assertContains(response, 'input-group')
        self.assertContains(response, 'changeGenerationCount(-1)')
        self.assertContains(response, 'changeGenerationCount(1)')
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
        self.assertContains(response, 'bi-gear')  # Production nav link
        self.assertContains(response, 'bi-eye')  # Preview area
        self.assertContains(response, 'bi-images')  # Recent products
    
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
        self.assertContains(response, 'window.ToastNotification')
        
        # The toast methods are defined in the included component
        # Check that the toast component is included
        self.assertContains(response, 'Enhanced Toast Notification System')
    
    def test_bootstrap_form_submission(self):
        """Test that Bootstrap form submits correctly."""
        order_data = {
            'title': 'Bootstrap Test Order',
            'prompt': 'test bootstrap integration',
            'machine_id': self.factory_machine.id,
            'generation_count': 1,
            'batch_size': 4,
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
        
        # Verify order and order items were created
        from .models import Order, OrderItem
        order = Order.objects.get(id=data['order_id'])
        self.assertEqual(order.title, 'Bootstrap Test Order')
        self.assertEqual(order.prompt, 'test bootstrap integration')
        
        # Verify order items were created with pending status
        items = OrderItem.objects.filter(order=order)
        self.assertEqual(items.count(), 1)
        self.assertEqual(items.first().status, 'pending')
    
    def test_javascript_functions_defined(self):
        """Test that required JavaScript functions are defined."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        content = response.content.decode()
        
        # Check that utility functions are defined
        self.assertIn('window.changeGenerationCount', content)
        self.assertIn('window.clearForm', content)
        
        # Check that event listeners are set up
        self.assertIn('addEventListener', content)
        self.assertIn('DOMContentLoaded', content)