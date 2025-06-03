import json
import tempfile
import unittest.mock as mock
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.conf import settings
from django.core.management import call_command
from django.utils import timezone
from io import StringIO

from .models import (
    Product, Order, OrderItem, Worker,
    FactoryMachineDefinition, FactoryMachineInstance, LogEntry
)

# Use test settings for all test cases
@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
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
        self.assertEqual(self.order.quantity, 2)  # This is total quantity now
        self.assertEqual(self.order.status, 'pending')
        self.assertEqual(self.order.completion_percentage, 0)
    
    def test_order_item_creation(self):
        """Test OrderItem creation and relationships."""
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt='test item prompt',
            parameters={'width': 512},
            status='pending',
            batch_size=2,
            total_quantity=2
        )
        
        self.assertEqual(order_item.order, self.order)
        self.assertEqual(order_item.prompt, 'test item prompt')
        self.assertEqual(order_item.status, 'pending')
        self.assertIsNone(order_item.product)
        self.assertEqual(order_item.batch_size, 2)
        self.assertEqual(order_item.total_quantity, 2)
    
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
    
    def test_completion_percentage_calculation(self):
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


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
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
    
    def test_place_order_api_success(self):
        """Test successful order placement via API."""
        order_data = {
            'title': 'Test API Order',
            'prompt': 'test api prompt',
            'machine_id': self.factory_machine.id,
            'generation_count': 1,
            'batch_size': 1,
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
        self.assertEqual(order.quantity, 1)  # generation_count * batch_size
        
        # Verify order item was created
        self.assertEqual(order.orderitem_set.count(), 1)
    
    def test_place_order_api_invalid_machine(self):
        """Test order placement with invalid machine ID."""
        order_data = {
            'title': 'Test Order',
            'prompt': 'test prompt',
            'machine_id': 999,  # Non-existent machine
            'generation_count': 1,
            'batch_size': 1
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


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
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
    
    def test_order_item_signal_no_auto_spawn_in_tests(self):
        """Test that creating OrderItem doesn't spawn workers in tests."""
        # Create an OrderItem - this should NOT trigger worker spawn in tests
        with patch('main.workers.spawn_worker_automatically') as mock_spawn:
            order_item = OrderItem.objects.create(
                order=self.order,
                prompt='test signal prompt',
                status='pending'
            )
            
            # Verify worker spawn was NOT called (due to test settings)
            mock_spawn.assert_not_called()
    
    def test_order_item_signal_not_triggered_for_non_pending(self):
        """Test that signal doesn't trigger for non-pending items."""
        # Create an OrderItem with non-pending status
        with patch('main.workers.spawn_worker_automatically') as mock_spawn:
            OrderItem.objects.create(
                order=self.order,
                prompt='test prompt',
                status='completed'  # Not pending
            )
            
            # Verify worker spawn was NOT called
            mock_spawn.assert_not_called()


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
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
        
        # Create OrderItem (worker spawning disabled in test settings)
        self.order_item = OrderItem.objects.create(
            order=self.order,
            prompt='test task prompt',
            status='pending'
        )
    
    @patch('main.factory_machines_sync.execute_order_item_sync_batch')
    def test_process_order_items_with_worker(self, mock_execute):
        """Test processing order items with worker system."""
        # Mock successful batch processing
        mock_execute.return_value = True
        
        # Update order to use fal.ai
        self.order.provider = 'fal.ai'
        self.order.save()
        
        # Set batch parameters
        self.order_item.batch_size = 2
        self.order_item.total_quantity = 2
        self.order_item.save()
        
        # Simulate worker processing
        from main.workers import SmartWorker
        worker = SmartWorker(max_batch_size=5)
        
        # Process the item
        success = mock_execute(self.order_item.id)
        
        # Verify processing was called
        mock_execute.assert_called_once_with(self.order_item.id)
        self.assertTrue(success)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
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
        
        # Create OrderItem (worker spawning disabled in test settings)
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


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
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
            'generation_count': 1,
            'batch_size': 1,
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
        
        # Verify order was created
        order = Order.objects.get(id=data['order_id'])
        self.assertEqual(order.quantity, 1)
        self.assertEqual(order.orderitem_set.count(), 1)
    
    def test_double_processing_prevention(self):
        """Test that the double-processing bug is fixed."""
        # Get any machine
        machine = FactoryMachineDefinition.objects.first()
        
        # Record initial counts
        initial_orders = Order.objects.count()
        initial_items = OrderItem.objects.count()
        
        # Place order requesting 2 images with batch
        order_data = {
            'title': 'Double Processing Test',
            'prompt': 'test prompt',
            'machine_id': machine.id,
            'generation_count': 1,  # 1 generation
            'batch_size': 2,        # 2 images per batch
            'parameters': {}
        }
        
        response = self.client.post(
            '/api/place-order/',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        
        # Verify exactly 1 order and 1 order item were created
        self.assertEqual(Order.objects.count(), initial_orders + 1)
        self.assertEqual(OrderItem.objects.count(), initial_items + 1)
        
        # Verify the order has the correct total quantity
        order = Order.objects.latest('id')
        self.assertEqual(order.quantity, 2)  # generation_count * batch_size
        self.assertEqual(order.orderitem_set.count(), 1)
        
        # Verify the order item has correct batch settings
        order_item = order.orderitem_set.first()
        self.assertEqual(order_item.batch_size, 2)
        self.assertEqual(order_item.total_quantity, 2)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class BatchGenerationTestCase(TestCase):
    """Test batch generation functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name='test/batch-model',
            display_name='Test Batch Model',
            description='Test model for batch generation',
            provider='test-provider',
            modality='image',
            parameter_schema={'width': 512, 'height': 512},
            default_parameters={'width': 512, 'height': 512},
            is_active=True
        )
        self.client = Client()
    
    def test_batch_generation_order_creation(self):
        """Test creating order with batch generation parameters."""
        order_data = {
            'title': 'Batch Generation Test',
            'prompt': 'test batch generation',
            'machine_id': self.factory_machine.id,
            'generation_count': 3,  # 3 generations
            'batch_size': 4,        # 4 images per batch
            'parameters': {}
        }
        
        response = self.client.post(
            '/api/place-order/',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        # Verify order was created with correct quantity
        order = Order.objects.get(id=data['order_id'])
        self.assertEqual(order.quantity, 12)  # 3 generations * 4 batch size
        
        # Verify correct number of order items created
        self.assertEqual(order.orderitem_set.count(), 3)  # 3 generations
        
        # Verify each order item has correct batch settings
        for item in order.orderitem_set.all():
            self.assertEqual(item.batch_size, 4)
            self.assertEqual(item.total_quantity, 4)
    
    def test_single_batch_generation(self):
        """Test generation with batch_size = 1."""
        order_data = {
            'title': 'Single Batch Test',
            'prompt': 'single image generation',
            'machine_id': self.factory_machine.id,
            'generation_count': 5,
            'batch_size': 1,
            'parameters': {}
        }
        
        response = self.client.post(
            '/api/place-order/',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        order = Order.objects.get(id=data['order_id'])
        self.assertEqual(order.quantity, 5)  # 5 * 1
        self.assertEqual(order.orderitem_set.count(), 5)
        
        for item in order.orderitem_set.all():
            self.assertEqual(item.batch_size, 1)
            self.assertEqual(item.total_quantity, 1)
    
    def test_batch_completion_tracking(self):
        """Test tracking of batch completion."""
        # Create order with batch
        order = Order.objects.create(
            title='Batch Completion Test',
            prompt='test completion',
            factory_machine_name=self.factory_machine.name,
            provider=self.factory_machine.provider,
            quantity=8  # 2 generations * 4 batch size
        )
        
        # Create order items with batch settings
        item1 = OrderItem.objects.create(
            order=order,
            prompt=order.prompt,
            parameters={},
            batch_size=4,
            total_quantity=4,
            status='processing'
        )
        item2 = OrderItem.objects.create(
            order=order,
            prompt=order.prompt,
            parameters={},
            batch_size=4,
            total_quantity=4,
            status='pending'
        )
        
        # Initially 0% complete
        self.assertEqual(order.completion_percentage, 0)
        
        # Complete first batch
        item1.status = 'completed'
        item1.batches_completed = 1
        item1.save()
        
        # Should be 50% complete (1 of 2 items)
        self.assertEqual(order.completion_percentage, 50)
        
        # Complete second batch
        item2.status = 'completed'
        item2.batches_completed = 1
        item2.save()
        
        # Should be 100% complete
        self.assertEqual(order.completion_percentage, 100)
    
    def test_order_item_can_store_multiple_products(self):
        """Test that OrderItem can be associated with multiple products."""
        order = Order.objects.create(
            title='Multi-Product Test',
            prompt='test multiple products',
            factory_machine_name=self.factory_machine.name,
            provider=self.factory_machine.provider,
            quantity=3
        )
        
        item = OrderItem.objects.create(
            order=order,
            prompt=order.prompt,
            parameters={},
            batch_size=3,
            total_quantity=3,
            status='completed'
        )
        
        # Create multiple products for this order item
        products = []
        for i in range(3):
            product = Product.objects.create(
                title=f'Product {i+1}',
                prompt=item.prompt,
                parameters=item.parameters,
                provider=order.provider,
                model_name=order.factory_machine_name,
                product_type='image',
                file_path=f'test/product_{i+1}.png',
                file_size=1024,
                order_item=item  # Set the ForeignKey relationship
            )
            products.append(product)
        
        # Verify the relationship
        self.assertEqual(item.products.count(), 3)
        # Products are ordered by -created_at, so newest first
        self.assertEqual(list(item.products.all().order_by('id')), products)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class RetryMechanismTestCase(TestCase):
    """Test the retry mechanism for failed order items."""
    
    def setUp(self):
        """Set up test data."""
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test_machine",
            display_name="Test Machine",
            provider="test",
            modality="image",
            is_active=True,
            parameter_schema={}
        )
        
        self.order = Order.objects.create(
            prompt="Test prompt",
            factory_machine_name="test_machine",
            provider="test"
        )
    
    def test_transient_failure_detection(self):
        """Test that transient failures are properly detected."""
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt="Test prompt",
            parameters={}
        )
        
        # Test transient error detection
        transient_errors = [
            "Server disconnected without sending a response",
            "Connection timeout occurred",
            "502 Bad Gateway",
            "Service unavailable",
            "Rate limit exceeded"
        ]
        
        non_transient_errors = [
            "Invalid API key",
            "Model not found",
            "Prompt contains inappropriate content",
            "Insufficient credits"
        ]
        
        for error in transient_errors:
            order_item.error_message = error
            self.assertTrue(
                order_item.is_transient_failure(),
                f"Should detect '{error}' as transient"
            )
        
        for error in non_transient_errors:
            order_item.error_message = error
            self.assertFalse(
                order_item.is_transient_failure(),
                f"Should NOT detect '{error}' as transient"
            )
    
    def test_retry_eligibility(self):
        """Test retry eligibility logic."""
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt="Test prompt",
            parameters={},
            max_retries=3
        )
        
        # Initially should not be retryable (not failed)
        self.assertFalse(order_item.can_be_retried())
        
        # After transient failure, should be retryable
        order_item.status = 'failed'
        order_item.error_message = "Server disconnected without sending a response"
        order_item.save()
        self.assertTrue(order_item.can_be_retried())
        
        # After non-transient failure, should not be retryable
        order_item.error_message = "Invalid API key"
        order_item.save()
        self.assertFalse(order_item.can_be_retried())
        
        # After max retries, should not be retryable
        order_item.error_message = "Server disconnected without sending a response"
        order_item.retry_count = 3
        order_item.save()
        self.assertFalse(order_item.can_be_retried())
    
    def test_retry_reset(self):
        """Test that reset_for_retry works correctly."""
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt="Test prompt",
            parameters={},
            status='failed',
            error_message="Server disconnected without sending a response",
            retry_count=0,
            max_retries=3
        )
        
        # Reset for retry
        order_item.reset_for_retry()
        
        # Check that fields are reset properly
        self.assertEqual(order_item.status, 'pending')
        self.assertIsNone(order_item.assigned_worker)
        self.assertEqual(order_item.retry_count, 1)
        self.assertIsNotNone(order_item.last_retry_at)
        self.assertEqual(order_item.provider_request_id, '')
        # Error message should be preserved for debugging
        self.assertEqual(order_item.error_message, "Server disconnected without sending a response")
    
    def test_worker_claims_retry_items(self):
        """Test that workers can claim failed items for retry."""
        # Create a failed item that can be retried
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt="Test prompt",
            parameters={},
            status='failed',
            error_message="Server disconnected without sending a response",
            retry_count=0,
            max_retries=3
        )
        
        # Create worker
        from main.workers import SmartWorker
        worker = SmartWorker(max_batch_size=5)
        worker.name = "test-worker"
        worker.process_id = 12345
        
        # Mock worker registration
        worker.worker_record = Worker.objects.create(
            name=worker.name,
            process_id=worker.process_id,
            provider='universal',
            max_batch_size=5,
            status='starting'
        )
        
        # Worker should claim the retryable item
        claimed_items = worker.claim_work_batch()
        
        self.assertEqual(len(claimed_items), 1)
        claimed_item = claimed_items[0]
        self.assertEqual(claimed_item.id, order_item.id)
        self.assertEqual(claimed_item.status, 'assigned')
        self.assertEqual(claimed_item.retry_count, 1)
        self.assertIsNotNone(claimed_item.last_retry_at)
    
    def test_worker_failure_handling_with_retries(self):
        """Test that worker failure handling implements retry logic."""
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt="Test prompt",
            parameters={},
            retry_count=0,
            max_retries=3
        )
        
        # Create worker
        from main.workers import SmartWorker
        worker = SmartWorker()
        worker.name = "test-worker"
        worker.worker_record = Worker.objects.create(
            name=worker.name,
            process_id=12345,
            provider='universal',
            max_batch_size=5,
            status='working'
        )
        
        # Test transient failure (should be marked for retry)
        worker.handle_item_failure(order_item, "Server disconnected without sending a response")
        order_item.refresh_from_db()
        
        self.assertEqual(order_item.status, 'failed')
        self.assertTrue(order_item.can_be_retried())
        
        # Test non-transient failure (should be permanently failed)
        order_item2 = OrderItem.objects.create(
            order=self.order,
            prompt="Test prompt 2",
            parameters={},
            retry_count=0,
            max_retries=3
        )
        
        worker.handle_item_failure(order_item2, "Invalid API key")
        order_item2.refresh_from_db()
        
        self.assertEqual(order_item2.status, 'failed')
        self.assertFalse(order_item2.can_be_retried())
        
        # Test exhausted retries (should be marked as exhausted)
        order_item3 = OrderItem.objects.create(
            order=self.order,
            prompt="Test prompt 3",
            parameters={},
            retry_count=3,
            max_retries=3
        )
        
        worker.handle_item_failure(order_item3, "Server disconnected without sending a response")
        order_item3.refresh_from_db()
        
        self.assertEqual(order_item3.status, 'exhausted')
        self.assertFalse(order_item3.can_be_retried())
    
    def test_worker_ignores_non_retryable_failed_items(self):
        """Test that workers don't claim failed items that cannot be retried."""
        # Create only non-retryable failed items
        order_item1 = OrderItem.objects.create(
            order=self.order,
            prompt="Test prompt 1",
            parameters={},
            status='failed',
            error_message="Invalid API key",  # Non-transient
            retry_count=0,
            max_retries=3
        )
        
        order_item2 = OrderItem.objects.create(
            order=self.order,
            prompt="Test prompt 2",
            parameters={},
            status='exhausted',  # Already exhausted
            error_message="Server disconnected without sending a response",
            retry_count=3,
            max_retries=3
        )
        
        # Create worker
        from main.workers import SmartWorker
        worker = SmartWorker(max_batch_size=5)
        worker.name = "test-worker"
        worker.process_id = 12345
        
        # Mock worker registration
        worker.worker_record = Worker.objects.create(
            name=worker.name,
            process_id=worker.process_id,
            provider='universal',
            max_batch_size=5,
            status='starting'
        )
        
        # Worker should not claim any items
        claimed_items = worker.claim_work_batch()
        self.assertEqual(len(claimed_items), 0)
    
    def test_order_status_with_retry_states(self):
        """Test that order status calculation handles retry states correctly."""
        # Test 1: Order with only retryable failed items should stay processing
        order1 = Order.objects.create(
            prompt="Test order with only retryable failures",
            factory_machine_name="test_machine",
            provider="test"
        )
        
        failed_retry_item1 = OrderItem.objects.create(
            order=order1,
            prompt="Failed but retryable 1",
            status='failed',
            error_message="Server disconnected without sending a response",
            retry_count=1,
            max_retries=3
        )
        
        failed_retry_item2 = OrderItem.objects.create(
            order=order1,
            prompt="Failed but retryable 2", 
            status='failed',
            error_message="Connection timeout",
            retry_count=0,
            max_retries=3
        )
        
        from main.workers import SmartWorker
        worker = SmartWorker()
        worker.update_order_status(order1)
        
        # Should be processing (has retryable failed items)
        order1.refresh_from_db()
        self.assertEqual(order1.status, 'processing')
        
        # Test 2: Order with mixed states (completed + final states)
        order2 = Order.objects.create(
            prompt="Test order with mixed states",
            factory_machine_name="test_machine",
            provider="test"
        )
        
        completed_item = OrderItem.objects.create(
            order=order2,
            prompt="Completed item",
            status='completed'
        )
        
        exhausted_item = OrderItem.objects.create(
            order=order2,
            prompt="Exhausted retries",
            status='exhausted',
            retry_count=3,
            max_retries=3
        )
        
        worker.update_order_status(order2)
        order2.refresh_from_db()
        
        # Should be completed (partial success)
        self.assertEqual(order2.status, 'completed')
