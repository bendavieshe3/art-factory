"""
Tests for negative prompt functionality across the Art Factory system.
These tests are written to fail initially and guide the implementation.
"""
import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.utils import timezone

from .models import (
    Product, Order, OrderItem, Worker,
    FactoryMachineDefinition, FactoryMachineInstance
)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class NegativePromptModelTestCase(TestCase):
    """Test negative prompt support in models."""
    
    def setUp(self):
        """Set up test data."""
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name='test/sdxl',
            display_name='Test SDXL',
            description='Test model for negative prompts',
            provider='fal.ai',
            modality='image',
            parameter_schema={'width': 1024, 'height': 1024},
            default_parameters={'width': 1024, 'height': 1024},
            is_active=True
        )
    
    def test_order_has_negative_prompt_field(self):
        """Test that Order model has negative_prompt field."""
        order = Order.objects.create(
            title='Test Order',
            prompt='beautiful landscape',
            negative_prompt='ugly, blurry, low quality',
            base_parameters={'width': 1024},
            factory_machine_name='test/sdxl',
            provider='fal.ai',
            quantity=1
        )
        
        self.assertEqual(order.negative_prompt, 'ugly, blurry, low quality')
        
    def test_order_negative_prompt_defaults_to_empty_string(self):
        """Test that negative_prompt defaults to empty string."""
        order = Order.objects.create(
            title='Test Order',
            prompt='beautiful landscape',
            base_parameters={'width': 1024},
            factory_machine_name='test/sdxl',
            provider='fal.ai',
            quantity=1
        )
        
        self.assertEqual(order.negative_prompt, '')
        
    def test_order_item_has_negative_prompt_field(self):
        """Test that OrderItem model has negative_prompt field."""
        order = Order.objects.create(
            title='Test Order',
            prompt='beautiful landscape',
            negative_prompt='ugly, blurry',
            base_parameters={'width': 1024},
            factory_machine_name='test/sdxl',
            provider='fal.ai',
            quantity=1
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            prompt='beautiful landscape',
            negative_prompt='ugly, blurry, low quality, distorted',
            parameters={'width': 1024},
            status='pending'
        )
        
        self.assertEqual(order_item.negative_prompt, 'ugly, blurry, low quality, distorted')
        
    def test_product_has_negative_prompt_field(self):
        """Test that Product model has negative_prompt field."""
        product = Product.objects.create(
            title='Test Product',
            prompt='beautiful landscape',
            negative_prompt='ugly, blurry, low quality',
            parameters={'width': 1024},
            provider='fal.ai',
            model_name='test/sdxl',
            product_type='image',
            file_path='test/path.png',
            file_size=1024,
            file_format='png'
        )
        
        self.assertEqual(product.negative_prompt, 'ugly, blurry, low quality')


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class NegativePromptAPITestCase(TestCase):
    """Test negative prompt support in API endpoints."""
    
    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name='fal/flux-dev',
            display_name='Flux Dev',
            description='Test model',
            provider='fal.ai',
            modality='image',
            parameter_schema={},
            default_parameters={},
            is_active=True
        )
        
        # Create a machine instance
        FactoryMachineInstance.objects.create(
            machine_definition=self.factory_machine,
            instance_id='primary-instance'
        )
    
    def test_place_order_api_accepts_negative_prompt(self):
        """Test that place-order API accepts negative_prompt parameter."""
        data = {
            'prompt': 'a beautiful mountain landscape',
            'negative_prompt': 'ugly, blurry, low quality, distorted',
            'machine_id': self.factory_machine.id,
            'quantity': 1,
            'parameters': {}
        }
        
        response = self.client.post(
            reverse('main:place-order'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        response_data = json.loads(response.content)
        
        # Check that order was created with negative prompt
        order = Order.objects.get(id=response_data['order_id'])
        self.assertEqual(order.negative_prompt, 'ugly, blurry, low quality, distorted')
        
        # Check that order items have negative prompt
        order_items = order.orderitem_set.all()
        self.assertEqual(len(order_items), 1)
        self.assertEqual(order_items[0].negative_prompt, 'ugly, blurry, low quality, distorted')
    
    def test_order_detail_api_returns_negative_prompt(self):
        """Test that order detail API returns negative_prompt."""
        order = Order.objects.create(
            title='Test Order',
            prompt='mountain landscape',
            negative_prompt='blurry, distorted',
            base_parameters={},
            factory_machine_name='fal/flux-dev',
            provider='fal.ai',
            quantity=1
        )
        
        OrderItem.objects.create(
            order=order,
            prompt='mountain landscape',
            negative_prompt='blurry, distorted',
            parameters={},
            status='pending'
        )
        
        response = self.client.get(f'/api/orders/{order.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['negative_prompt'], 'blurry, distorted')
        self.assertEqual(data['items'][0]['negative_prompt'], 'blurry, distorted')
    
    def test_product_api_returns_negative_prompt(self):
        """Test that product API returns negative_prompt."""
        product = Product.objects.create(
            title='Test Product',
            prompt='mountain landscape',
            negative_prompt='blurry, low quality',
            parameters={},
            provider='fal.ai',
            model_name='fal/flux-dev',
            product_type='image',
            file_path='test.png',
            file_size=1024,
            file_format='png'
        )
        
        response = self.client.get(f'/api/products/{product.id}/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertEqual(data['negative_prompt'], 'blurry, low quality')


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class NegativePromptProviderTestCase(TestCase):
    """Test negative prompt handling in provider implementations."""
    
    def setUp(self):
        """Set up test data."""
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name='fal/flux-dev',
            display_name='Flux Dev',
            description='Test model',
            provider='fal.ai',
            modality='image',
            parameter_schema={},
            default_parameters={},
            is_active=True
        )
        
        self.order = Order.objects.create(
            title='Test Order',
            prompt='beautiful landscape',
            negative_prompt='ugly, blurry',
            base_parameters={},
            factory_machine_name='fal/flux-dev',
            provider='fal.ai',
            quantity=1
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            prompt='beautiful landscape',
            negative_prompt='ugly, blurry, distorted',
            parameters={},
            status='pending'
        )
    
    @patch('main.factory_machines.fal_client.submit')
    def test_fal_provider_sends_negative_prompt(self, mock_submit):
        """Test that fal.ai provider includes negative_prompt in API call."""
        # Import after models are ready
        from .factory_machines import FalFluxDevFactory
        
        # Set up mock
        mock_result = MagicMock()
        mock_result.request_id = 'test-request-id'
        mock_submit.return_value = mock_result
        
        # Create factory and process
        factory = FalFluxDevFactory()
        result = factory.process(self.order_item)
        
        # Verify the API was called with negative_prompt
        mock_submit.assert_called_once()
        call_args = mock_submit.call_args[1]
        
        self.assertIn('negative_prompt', call_args)
        self.assertEqual(call_args['negative_prompt'], 'ugly, blurry, distorted')
    
    @patch('replicate.run')
    def test_replicate_provider_sends_negative_prompt(self, mock_run):
        """Test that Replicate provider includes negative_prompt in API call."""
        # Create a Replicate-based model
        replicate_machine = FactoryMachineDefinition.objects.create(
            name='stability-ai/sdxl',
            display_name='SDXL',
            description='Test model',
            provider='replicate',
            modality='image',
            parameter_schema={},
            default_parameters={},
            is_active=True
        )
        
        order = Order.objects.create(
            title='Test Order',
            prompt='beautiful landscape',
            negative_prompt='ugly, blurry',
            base_parameters={},
            factory_machine_name='stability-ai/sdxl',
            provider='replicate',
            quantity=1
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            prompt='beautiful landscape',
            negative_prompt='ugly, blurry, distorted',
            parameters={},
            status='pending'
        )
        
        # Mock the replicate response
        mock_run.return_value = ['https://example.com/image.png']
        
        # Import the factory class (assuming it exists)
        from .factory_machines import ReplicateSDXLFactory
        
        # Create factory and process
        factory = ReplicateSDXLFactory()
        result = factory.process(order_item)
        
        # Verify the API was called with negative_prompt
        mock_run.assert_called_once()
        call_args = mock_run.call_args[1]['input']
        
        self.assertIn('negative_prompt', call_args)
        self.assertEqual(call_args['negative_prompt'], 'ugly, blurry, distorted')


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class NegativePromptUITestCase(TestCase):
    """Test negative prompt display in UI views."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name='test/model',
            display_name='Test Model',
            description='Test model',
            provider='test',
            modality='image',
            parameter_schema={},
            default_parameters={},
            is_active=True
        )
        
        # Create machine instance
        self.machine_instance = FactoryMachineInstance.objects.create(
            machine_definition=self.factory_machine,
            instance_id='primary-instance'
        )
    
    def test_order_form_has_negative_prompt_field(self):
        """Test that order form includes negative prompt field."""
        response = self.client.get(reverse('main:order'))
        self.assertEqual(response.status_code, 200)
        
        # Check that the form includes negative prompt field
        self.assertContains(response, 'negative_prompt')
        self.assertContains(response, 'Negative Prompt')
        self.assertContains(response, 'What to avoid in the generated image')
    
    def test_product_detail_displays_negative_prompt(self):
        """Test that product detail page displays negative prompt."""
        product = Product.objects.create(
            title='Test Product',
            prompt='beautiful landscape',
            negative_prompt='ugly, blurry, low quality',
            parameters={},
            provider='test',
            model_name='test/model',
            product_type='image',
            file_path='test.png',
            file_size=1024,
            file_format='png'
        )
        
        response = self.client.get(reverse('main:product_detail', args=[product.id]))
        self.assertEqual(response.status_code, 200)
        
        # Check that negative prompt is displayed
        self.assertContains(response, 'Negative Prompt')
        self.assertContains(response, 'ugly, blurry, low quality')
    
    def test_production_view_displays_negative_prompt(self):
        """Test that production view displays negative prompt for orders."""
        order = Order.objects.create(
            title='Test Order',
            prompt='mountain landscape',
            negative_prompt='blurry, distorted',
            base_parameters={},
            factory_machine_name='test/model',
            provider='test',
            quantity=1,
            status='processing'
        )
        
        OrderItem.objects.create(
            order=order,
            prompt='mountain landscape',
            negative_prompt='blurry, distorted',
            parameters={},
            status='processing'
        )
        
        response = self.client.get(reverse('main:production'))
        self.assertEqual(response.status_code, 200)
        
        # Check that negative prompt is displayed in the production view
        self.assertContains(response, 'blurry, distorted')


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class NegativePromptIntegrationTestCase(TestCase):
    """Test end-to-end negative prompt functionality."""
    
    def setUp(self):
        """Set up test data."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name='fal/flux-dev',
            display_name='Flux Dev',
            description='Test model',
            provider='fal.ai',
            modality='image',
            parameter_schema={},
            default_parameters={},
            is_active=True
        )
        
        FactoryMachineInstance.objects.create(
            machine_definition=self.factory_machine,
            instance_id='primary-instance'
        )
        
        # Create worker
        self.worker = Worker.objects.create(
            name='test-worker',
            process_id=12345
        )
    
    @patch('main.factory_machines.fal_client.submit')
    @patch('main.factory_machines.fal_client.result')
    def test_full_workflow_with_negative_prompt(self, mock_result, mock_submit):
        """Test complete workflow from order placement to product creation with negative prompt."""
        # Set up mocks
        mock_submit_result = MagicMock()
        mock_submit_result.request_id = 'test-request-id'
        mock_submit.return_value = mock_submit_result
        
        mock_result.return_value = MagicMock(
            images=[{'url': 'https://example.com/image.png'}]
        )
        
        # Place order with negative prompt
        data = {
            'prompt': 'a majestic mountain landscape at sunset',
            'negative_prompt': 'blurry, out of focus, low quality, distorted, ugly',
            'machine_id': self.factory_machine.id,
            'quantity': 1,
            'parameters': {'width': 1024, 'height': 1024}
        }
        
        response = self.client.post(
            reverse('main:place-order'),
            data=json.dumps(data),
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        order_id = json.loads(response.content)['order_id']
        
        # Verify order has negative prompt
        order = Order.objects.get(id=order_id)
        self.assertEqual(order.negative_prompt, 'blurry, out of focus, low quality, distorted, ugly')
        
        # Process the order
        order_item = order.items.first()
        order_item.status = 'processing'
        order_item.status_worker = self.worker
        order_item.save()
        
        # Simulate factory processing
        from .factory_machines import FalFluxDevFactory
        factory = FalFluxDevFactory()
        
        with patch('requests.get') as mock_get:
            mock_get.return_value.content = b'fake image data'
            mock_get.return_value.headers = {'content-type': 'image/png'}
            
            result = factory.process(order_item)
        
        # Verify negative prompt was sent to provider
        mock_submit.assert_called_once()
        call_args = mock_submit.call_args[1]
        self.assertEqual(call_args['negative_prompt'], 'blurry, out of focus, low quality, distorted, ugly')
        
        # Verify product has negative prompt
        order_item.refresh_from_db()
        product = order_item.product
        self.assertIsNotNone(product)
        self.assertEqual(product.negative_prompt, 'blurry, out of focus, low quality, distorted, ugly')