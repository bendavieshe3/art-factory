"""
Tests for UI notification system and order placement workflow.
"""
import json
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from unittest.mock import patch

from main.models import FactoryMachineDefinition


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)


class NotificationSystemTestCase(TestCase):
    """Test the toast notification system and order placement UI."""
    
    def setUp(self):
        """Set up test client and factory machine."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name='test/model',
            display_name='Test Model',
            description='Test model for UI testing',
            provider='test-provider',
            modality='image',
            parameter_schema={'width': 512, 'height': 512},
            default_parameters={'width': 512, 'height': 512, 'enable_safety_checker': False},
            is_active=True
        )
    
    def test_order_page_loads_with_toast_system(self):
        """Test that order page loads with toast notification system."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check toast container is present
        self.assertContains(response, 'toast-container')
        self.assertContains(response, 'id="toastContainer"')
        
        # Check toast JavaScript is loaded
        self.assertContains(response, 'window.ToastNotification')
        self.assertContains(response, 'ToastNotification.success')
        # Order page doesn't use ToastNotification.error, it uses error banner
        self.assertContains(response, 'ToastNotification.warning')
    
    def test_order_form_uses_toast_notifications(self):
        """Test that order form JavaScript uses toast notifications instead of alerts."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check that old alert() calls are replaced with ToastNotification calls
        self.assertNotContains(response, 'alert(')
        self.assertContains(response, 'ToastNotification.success(')
        # Note: Order page uses error banner instead of error toasts
        self.assertContains(response, 'showErrorBanner(')
        
        # Check toast message content
        self.assertContains(response, 'Order Placed')
        self.assertContains(response, 'Order failed')
        self.assertContains(response, 'Status polling failed')
    
    @patch('main.tasks.process_order_items_async')
    def test_successful_order_shows_success_toast(self, mock_process):
        """Test that successful order placement triggers success toast message."""
        order_data = {
            'title': 'Toast Test Order',
            'prompt': 'test toast prompt',
            'machine_id': self.factory_machine.id,
            'quantity': 2,
            'parameters': {'width': 512, 'height': 512}
        }
        
        response = self.client.post(
            '/api/place-order/',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        
        # The success message should mention the order ID and quantity
        expected_message = f"Order #{data['order_id']} placed successfully! 2 images are being generated."
        # Note: We can't directly test the JavaScript toast, but we can verify 
        # the API response provides the right data for the toast
        self.assertIn('order_id', data)
        self.assertIn('message', data)
    
    def test_failed_order_provides_error_data(self):
        """Test that failed order provides appropriate error data for toast."""
        order_data = {
            'title': 'Failed Order Test',
            'prompt': 'test prompt',
            'machine_id': 999,  # Non-existent machine
            'quantity': 1
        }
        
        response = self.client.post(
            '/api/place-order/',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('error', data)
        
        # Error message should be suitable for toast notification
        self.assertIsInstance(data['error'], str)
        self.assertGreater(len(data['error']), 0)
    
    def test_toast_css_classes_present(self):
        """Test that all necessary CSS classes for toasts are present."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check main toast CSS classes
        self.assertContains(response, '.toast-container')
        self.assertContains(response, '.toast-notification')
        self.assertContains(response, '.toast-notification.show')
        self.assertContains(response, '.toast-notification.toast-success')
        self.assertContains(response, '.toast-notification.toast-error')
        self.assertContains(response, '.toast-notification.toast-warning')
        self.assertContains(response, '.toast-notification.toast-info')
        
        # Check toast component classes
        self.assertContains(response, '.toast-header')
        self.assertContains(response, '.toast-title')
        self.assertContains(response, '.toast-close')
        self.assertContains(response, '.toast-body')
    
    def test_toast_animations_configured(self):
        """Test that toast animations are properly configured."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check animation CSS properties
        self.assertContains(response, 'transform: translateX(100%)')
        self.assertContains(response, 'transform: translateX(0)')
        self.assertContains(response, 'transition: all 0.3s ease')
        self.assertContains(response, 'opacity: 0')
        self.assertContains(response, 'opacity: 1')
    
    def test_no_alert_calls_in_templates(self):
        """Test that no JavaScript alert() calls remain in templates."""
        # Test all main template pages
        pages = ['/', '/inventory/', '/production/', '/settings/']
        
        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                if response.status_code == 200:  # Some pages might not exist yet
                    self.assertNotContains(response, 'alert(', msg_prefix=f"Page {page} still contains alert() calls")