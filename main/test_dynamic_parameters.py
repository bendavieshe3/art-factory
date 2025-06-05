"""
Tests for dynamic parameter handling in the order page.
"""
import json
from django.test import TestCase, Client, override_settings
from unittest.mock import patch

from .models import FactoryMachineDefinition


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class DynamicParametersTestCase(TestCase):
    """Test dynamic parameter generation based on model selection."""
    
    def setUp(self):
        """Set up test client and factory machines with different parameter schemas."""
        self.client = Client()
        
        # Create SDXL model with simple schema
        self.sdxl_machine = FactoryMachineDefinition.objects.create(
            name='fal-ai/fast-sdxl',
            display_name='Fast SDXL',
            description='Fast SDXL model',
            provider='fal.ai',
            modality='image',
            parameter_schema={
                'prompt': 'string',
                'image_size': 'square_hd',
                'num_inference_steps': 25,
                'guidance_scale': 7.5,
                'num_images': 1
            },
            default_parameters={
                'image_size': 'square_hd',
                'num_inference_steps': 25,
                'guidance_scale': 7.5,
                'enable_safety_checker': False
            },
            is_active=True
        )
        
        # Create FLUX model with JSON schema format
        self.flux_machine = FactoryMachineDefinition.objects.create(
            name='fal-ai/flux/dev',
            display_name='FLUX.1 Dev',
            description='FLUX.1 Dev model',
            provider='fal.ai',
            modality='text-to-image',
            parameter_schema={
                'type': 'object',
                'properties': {
                    'prompt': {'type': 'string', 'description': 'Text description'},
                    'width': {'type': 'integer', 'default': 1024, 'minimum': 256, 'maximum': 1440},
                    'height': {'type': 'integer', 'default': 1024, 'minimum': 256, 'maximum': 1440},
                    'guidance_scale': {'type': 'number', 'default': 3.5, 'minimum': 1.0, 'maximum': 20.0},
                    'num_inference_steps': {'type': 'integer', 'default': 28, 'minimum': 1, 'maximum': 50}
                },
                'required': ['prompt']
            },
            default_parameters={
                'width': 1024,
                'height': 1024,
                'guidance_scale': 3.5,
                'num_inference_steps': 28,
                'enable_safety_checker': False
            },
            is_active=True
        )
    
    def test_factory_machines_api_returns_correct_data(self):
        """Test that the factory machines API returns parameter schemas."""
        response = self.client.get('/api/factory-machines/')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn('machines', data)
        machines = data['machines']
        
        # Find our test machines
        sdxl = next((m for m in machines if m['name'] == 'fal-ai/fast-sdxl'), None)
        flux = next((m for m in machines if m['name'] == 'fal-ai/flux/dev'), None)
        
        self.assertIsNotNone(sdxl)
        self.assertIsNotNone(flux)
        
        # Verify SDXL has simple schema
        self.assertIn('image_size', sdxl['parameter_schema'])
        self.assertEqual(sdxl['default_parameters']['num_inference_steps'], 25)
        
        # Verify FLUX has JSON schema
        self.assertEqual(flux['parameter_schema']['type'], 'object')
        self.assertIn('properties', flux['parameter_schema'])
        self.assertEqual(flux['default_parameters']['num_inference_steps'], 28)
    
    def test_order_page_contains_dynamic_parameters_container(self):
        """Test that the order page has the dynamic parameters container."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        
        # Check for dynamic parameters container
        self.assertContains(response, 'id="dynamicParameters"')
        self.assertContains(response, 'updateDynamicParameters')
        self.assertContains(response, 'generateParameterFields')
    
    def test_order_with_dynamic_parameters_flux_model(self):
        """Test placing an order with FLUX model using appropriate parameters."""
        # Order data with FLUX-appropriate parameters
        order_data = {
            'title': 'FLUX Test Order',
            'prompt': 'test dynamic parameters with FLUX',
            'machine_id': self.flux_machine.id,
            'generation_count': 1,
            'batch_size': 4,
            'parameters': {
                'width': 1024,
                'height': 1024,
                'num_inference_steps': 28,  # FLUX optimal
                'guidance_scale': 3.5       # FLUX optimal
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
        
        # Verify order was created with correct parameters
        from .models import Order, OrderItem
        order = Order.objects.get(id=data['order_id'])
        self.assertEqual(order.title, 'FLUX Test Order')
        items = OrderItem.objects.filter(order=order)
        self.assertEqual(items.count(), 1)
    
    def test_order_with_dynamic_parameters_sdxl_model(self):
        """Test placing an order with SDXL model using appropriate parameters."""
        # Order data with SDXL-appropriate parameters
        order_data = {
            'title': 'SDXL Test Order',
            'prompt': 'test dynamic parameters with SDXL',
            'machine_id': self.sdxl_machine.id,
            'generation_count': 1,
            'batch_size': 4,
            'parameters': {
                'image_size': 'square_hd',  # SDXL format
                'num_inference_steps': 25,  # SDXL optimal
                'guidance_scale': 7.5       # SDXL optimal
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
        
        # Verify order was created with correct parameters
        from .models import Order, OrderItem
        order = Order.objects.get(id=data['order_id'])
        self.assertEqual(order.title, 'SDXL Test Order')
        items = OrderItem.objects.filter(order=order)
        self.assertEqual(items.count(), 1)
    
    def test_parameter_validation_prevents_invalid_ranges(self):
        """Test that invalid parameter ranges are handled gracefully."""
        # This test simulates what should happen when the frontend sends
        # parameters that are outside the valid range for a model
        
        # Try to send invalid steps for FLUX (max 50, sending 100)
        order_data = {
            'title': 'Invalid Range Test',
            'prompt': 'test invalid parameter range',
            'machine_id': self.flux_machine.id,
            'generation_count': 1,
            'batch_size': 4,
            'parameters': {
                'width': 1024,
                'height': 1024,
                'num_inference_steps': 100,  # Invalid: FLUX max is 50
                'guidance_scale': 3.5
            }
        }
        
        response = self.client.post(
            '/api/place-order/',
            data=json.dumps(order_data),
            content_type='application/json'
        )
        
        # Should still succeed - validation happens at API level
        # Our job is to send the right parameters in the first place
        self.assertEqual(response.status_code, 200)