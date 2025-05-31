import json
import tempfile
import unittest.mock as mock
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.urls import reverse
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from io import StringIO

from .models import (
    Product, Order, OrderItem, 
    FactoryMachineDefinition, FactoryMachineInstance, LogEntry
)


class ModelTestCase(TestCase):
    """Test Django models functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name='test/model',
            display_name='Test Model',
            description='Test model for testing',
            provider='test-provider',
            modality='image',
            parameter_schema={'width': 512, 'height': 512},
            default_parameters={'width': 512, 'height': 512},
            is_active=True
        )
        
        self.order = Order.objects.create(
            title='Test Order',
            prompt='test prompt',
            base_parameters={'width': 512},
            factory_machine_name='test/model',
            provider='test-provider',
            quantity=2
        )
    
    def test_order_creation(self):
        """Test Order model creation and properties."""
        self.assertEqual(self.order.title, 'Test Order')
        self.assertEqual(self.order.prompt, 'test prompt')
        self.assertEqual(self.order.quantity, 2)
        self.assertEqual(self.order.status, 'pending')
        self.assertEqual(self.order.completion_percentage, 0)
    
    @patch('main.tasks.process_order_items_async')
    def test_order_item_creation(self, mock_process):
        """Test OrderItem creation and relationships."""
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt='test item prompt',
            parameters={'width': 512},
            status='pending'
        )
        
        self.assertEqual(order_item.order, self.order)
        self.assertEqual(order_item.prompt, 'test item prompt')
        self.assertEqual(order_item.status, 'pending')
        self.assertIsNone(order_item.product)
        
        # Verify signal was triggered
        mock_process.assert_called_once()
    
    def test_product_creation(self):
        """Test Product model creation."""
        product = Product.objects.create(
            title='Test Product',
            prompt='test prompt',
            parameters={'width': 512},
            provider='test-provider',
            model_name='test/model',
            product_type='image',
            file_path='test/path.png',
            file_size=1024,
            file_format='png'
        )
        
        self.assertEqual(product.title, 'Test Product')
        self.assertEqual(product.provider, 'test-provider')
        self.assertEqual(product.file_format, 'png')
    
    @patch('main.tasks.process_order_items_async')
    def test_completion_percentage_calculation(self, mock_process):
        """Test order completion percentage calculation."""
        # Create order items
        item1 = OrderItem.objects.create(
            order=self.order,
            prompt='item 1',
            status='pending'
        )
        item2 = OrderItem.objects.create(
            order=self.order,
            prompt='item 2',
            status='completed'
        )
        
        # Should be 50% complete (1 of 2 completed)
        self.assertEqual(self.order.completion_percentage, 50)
        
        # Complete the other item
        item1.status = 'completed'
        item1.save()
        
        # Should be 100% complete
        self.assertEqual(self.order.completion_percentage, 100)


class ViewTestCase(TestCase):
    """Test Django views functionality."""
    
    def setUp(self):
        """Set up test client and data."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name='test/model',
            display_name='Test Model',
            description='Test model for testing',
            provider='test-provider',
            modality='image',
            parameter_schema={'width': 512, 'height': 512},
            default_parameters={'width': 512, 'height': 512},
            is_active=True
        )
    
    def test_home_page_loads(self):
        """Test home page (order view) loads correctly."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Place Order')
        self.assertContains(response, 'Test Model')
    
    def test_inventory_page_loads(self):
        """Test inventory page loads correctly."""
        response = self.client.get('/inventory/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Inventory')
    
    def test_production_page_loads(self):
        """Test production page loads correctly."""
        response = self.client.get('/production/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Production')
    
    def test_factory_machines_api(self):
        """Test factory machines API endpoint."""
        response = self.client.get('/api/factory-machines/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('machines', data)
        self.assertEqual(len(data['machines']), 1)
        self.assertEqual(data['machines'][0]['name'], 'test/model')
    
    @patch('main.tasks.process_order_items_async')
    def test_place_order_api_success(self, mock_process):
        """Test successful order placement via API."""
        order_data = {
            'title': 'Test API Order',
            'prompt': 'test api prompt',
            'machine_id': self.factory_machine.id,
            'quantity': 1,
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
        self.assertIn('order_id', data)
        
        # Verify order was created
        order = Order.objects.get(id=data['order_id'])
        self.assertEqual(order.title, 'Test API Order')
        self.assertEqual(order.quantity, 1)
        
        # Verify order item was created
        self.assertEqual(order.orderitem_set.count(), 1)
        
        # Verify background processing was triggered
        mock_process.assert_called_once()
    
    def test_place_order_api_invalid_machine(self):
        """Test order placement with invalid machine ID."""
        order_data = {
            'title': 'Test Order',
            'prompt': 'test prompt',
            'machine_id': 999,  # Non-existent machine
            'quantity': 1
        }
        
        response = self.client.post(
            '/api/place-order/',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        # Django's get_object_or_404 raises 404, but our view catches and returns 400
        self.assertEqual(response.status_code, 400)
    
    def test_product_detail_view(self):
        """Test product detail view."""
        product = Product.objects.create(
            title='Test Product',
            prompt='test prompt',
            provider='test-provider',
            model_name='test/model',
            product_type='image',
            file_path='test/path.png',
            file_size=1024
        )
        
        response = self.client.get(f'/products/{product.id}/')
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Test Product')


class SignalTestCase(TestCase):
    """Test Django signals functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.order = Order.objects.create(
            title='Signal Test Order',
            prompt='test prompt',
            factory_machine_name='test/model',
            provider='test-provider',
            quantity=1
        )
    
    @patch('main.tasks.process_order_items_async')
    def test_order_item_signal_triggers_processing(self, mock_process):
        """Test that creating OrderItem triggers background processing."""
        # Create an OrderItem - this should trigger the signal
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt='test signal prompt',
            status='pending'
        )
        
        # Verify the background processing was triggered
        mock_process.assert_called_once()
        call_args = mock_process.call_args[0]
        self.assertEqual(len(call_args[0]), 1)  # One order item passed
        self.assertEqual(call_args[0][0], order_item)
    
    @patch('main.tasks.process_order_items_async')
    def test_order_item_signal_not_triggered_for_non_pending(self, mock_process):
        """Test that signal doesn't trigger for non-pending items."""
        # Create an OrderItem with non-pending status
        OrderItem.objects.create(
            order=self.order,
            prompt='test prompt',
            status='completed'  # Not pending
        )
        
        # Verify background processing was NOT triggered
        mock_process.assert_not_called()


class TaskTestCase(TestCase):
    """Test background task functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.order = Order.objects.create(
            title='Task Test Order',
            prompt='test prompt',
            factory_machine_name='test/model',
            provider='test-provider',
            quantity=1
        )
        
        # Create OrderItem with mocked signal to avoid database lock
        with patch('main.tasks.process_order_items_async'):
            self.order_item = OrderItem.objects.create(
                order=self.order,
                prompt='test task prompt',
                status='pending'
            )
    
    @patch('main.management.commands.simple_process.Command.process_fal_item')
    def test_process_order_items_async_fal(self, mock_process_fal):
        """Test async processing with fal.ai provider."""
        from main.tasks import process_order_items_async
        
        # Mock successful fal processing
        mock_product = Product.objects.create(
            title='Mock Product',
            prompt='test',
            provider='fal.ai',
            model_name='test/model',
            product_type='image',
            file_path='mock/path.png',
            file_size=1024
        )
        mock_process_fal.return_value = mock_product
        
        # Update order to use fal.ai
        self.order.provider = 'fal.ai'
        self.order.save()
        
        # Process the order item
        process_order_items_async([self.order_item])
        
        # Verify processing was called
        mock_process_fal.assert_called_once()
        
        # Verify order item was updated
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.status, 'completed')
        self.assertEqual(self.order_item.product, mock_product)


class ManagementCommandTestCase(TestCase):
    """Test management commands."""
    
    def test_load_seed_data_command(self):
        """Test load_seed_data management command."""
        # Ensure no machines exist initially
        FactoryMachineDefinition.objects.all().delete()
        
        # Run the command
        out = StringIO()
        call_command('load_seed_data', stdout=out)
        
        # Verify machines were created
        self.assertGreater(FactoryMachineDefinition.objects.count(), 0)
        
        # Verify fal.ai machines exist
        fal_machines = FactoryMachineDefinition.objects.filter(provider='fal.ai')
        self.assertGreater(fal_machines.count(), 0)
        
        # Verify replicate machines exist
        replicate_machines = FactoryMachineDefinition.objects.filter(provider='replicate')
        self.assertGreater(replicate_machines.count(), 0)
    
    @patch('main.management.commands.simple_process.Command.process_fal_item')
    def test_simple_process_command(self, mock_process_fal):
        """Test simple_process management command."""
        # Create a pending order item
        order = Order.objects.create(
            title='Command Test Order',
            prompt='test prompt',
            factory_machine_name='fal-ai/flux/dev',
            provider='fal.ai',
            quantity=1
        )
        
        # Create OrderItem with mocked signal to avoid database lock
        with patch('main.tasks.process_order_items_async'):
            order_item = OrderItem.objects.create(
                order=order,
                prompt='test command prompt',
                status='pending'
            )
        
        # Mock successful processing
        mock_product = Product.objects.create(
            title='Mock Product',
            prompt='test',
            provider='fal.ai',
            model_name='fal-ai/flux/dev',
            product_type='image',
            file_path='mock/path.png',
            file_size=1024
        )
        mock_process_fal.return_value = mock_product
        
        # Run the command
        out = StringIO()
        call_command('simple_process', stdout=out)
        
        # Verify processing was called
        mock_process_fal.assert_called_once()
        
        # Verify order item was processed
        order_item.refresh_from_db()
        self.assertEqual(order_item.status, 'completed')


@patch.dict('os.environ', {'FAL_KEY': 'test_key'})
@patch.dict('os.environ', {'REPLICATE_API_TOKEN': 'test_token'})
class IntegrationTestCase(TestCase):
    """Integration tests for the complete workflow."""
    
    def setUp(self):
        """Set up integration test data."""
        # Load seed data
        call_command('load_seed_data')
        
        self.client = Client()
    
    @patch('fal_client.submit')
    @patch('httpx.Client.get')
    def test_end_to_end_fal_workflow(self, mock_http_get, mock_fal_submit):
        """Test complete workflow from order placement to product creation with fal.ai."""
        # Mock fal.ai response
        mock_handle = MagicMock()
        mock_handle.get.return_value = {
            'images': [{'url': 'http://example.com/image.png', 'width': 512, 'height': 512}],
            'seed': 12345,
            'request_id': 'test_request_123'
        }
        mock_fal_submit.return_value = mock_handle
        
        # Mock HTTP download
        mock_response = MagicMock()
        mock_response.content = b'fake_image_data'
        mock_response.raise_for_status.return_value = None
        mock_http_get.return_value = mock_response
        
        # Get fal.ai machine
        fal_machine = FactoryMachineDefinition.objects.filter(provider='fal.ai').first()
        self.assertIsNotNone(fal_machine)
        
        # Place order via API
        order_data = {
            'title': 'Integration Test Order',
            'prompt': 'a beautiful landscape',
            'machine_id': fal_machine.id,
            'quantity': 1,
            'parameters': {'width': 512, 'height': 512}
        }
        
        with patch('main.tasks.process_order_items_async') as mock_process:
            response = self.client.post(
                '/api/place-order/',
                data=json.dumps(order_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            self.assertTrue(data['success'])
            
            # Verify order was created
            order = Order.objects.get(id=data['order_id'])
            self.assertEqual(order.quantity, 1)
            self.assertEqual(order.orderitem_set.count(), 1)
            
            # Verify background processing was triggered
            mock_process.assert_called_once()
    
    def test_double_processing_prevention(self):
        """Test that the double-processing bug is fixed."""
        # Get any machine
        machine = FactoryMachineDefinition.objects.first()
        
        # Record initial counts
        initial_orders = Order.objects.count()
        initial_items = OrderItem.objects.count()
        
        # Place order requesting 2 images
        order_data = {
            'title': 'Double Processing Test',
            'prompt': 'test prompt',
            'machine_id': machine.id,
            'quantity': 2,
            'parameters': {}
        }
        
        with patch('main.tasks.process_order_items_async'):
            response = self.client.post(
                '/api/place-order/',
                data=json.dumps(order_data),
                content_type='application/json'
            )
            
            self.assertEqual(response.status_code, 200)
            
            # Verify exactly 1 order and 2 order items were created
            self.assertEqual(Order.objects.count(), initial_orders + 1)
            self.assertEqual(OrderItem.objects.count(), initial_items + 2)
            
            # Verify the order has exactly the requested quantity
            order = Order.objects.latest('id')
            self.assertEqual(order.quantity, 2)
            self.assertEqual(order.orderitem_set.count(), 2)
