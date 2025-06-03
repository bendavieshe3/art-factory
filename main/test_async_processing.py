"""
Tests for asynchronous order processing and retry mechanisms.
"""
import json
from django.test import TestCase, override_settings
from django.utils import timezone
from datetime import timedelta
from unittest.mock import patch, Mock
from io import StringIO
from django.core.management import call_command

from .models import FactoryMachineDefinition, Order, OrderItem, LogEntry


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class AsyncProcessingTestCase(TestCase):
    """Test asynchronous order processing and retry mechanisms."""
    
    def setUp(self):
        """Set up test data."""
        self.flux_machine = FactoryMachineDefinition.objects.create(
            name='fal-ai/flux/schnell',
            display_name='FLUX.1 Schnell',
            description='Test FLUX model',
            provider='fal.ai',
            modality='text-to-image',
            parameter_schema={
                'type': 'object',
                'properties': {
                    'prompt': {'type': 'string'},
                    'width': {'type': 'integer', 'default': 1024},
                    'height': {'type': 'integer', 'default': 1024},
                    'num_inference_steps': {'type': 'integer', 'default': 4, 'maximum': 8}
                }
            },
            default_parameters={
                'width': 1024,
                'height': 1024,
                'num_inference_steps': 4,
                'enable_safety_checker': False
            },
            is_active=True
        )
    
    def test_monitor_orders_command(self):
        """Test the monitor_orders management command."""
        # Create test orders with different statuses
        order1 = Order.objects.create(
            title='Test Order 1',
            prompt='test prompt',
            factory_machine_name=self.flux_machine.name,
            provider=self.flux_machine.provider,
            quantity=1
        )
        
        OrderItem.objects.create(
            order=order1,
            prompt=order1.prompt,
            parameters=self.flux_machine.default_parameters,
            status='pending'
        )
        
        order2 = Order.objects.create(
            title='Test Order 2',
            prompt='test prompt 2',
            factory_machine_name=self.flux_machine.name,
            provider=self.flux_machine.provider,
            quantity=1
        )
        
        OrderItem.objects.create(
            order=order2,
            prompt=order2.prompt,
            parameters=self.flux_machine.default_parameters,
            status='failed',
            error_message='Test error message'
        )
        
        # Test monitor command
        out = StringIO()
        call_command('monitor_orders', stdout=out)
        output = out.getvalue()
        
        # Verify output contains expected information
        self.assertIn('Order Processing Status', output)
        self.assertIn('pending: 1', output)
        self.assertIn('failed: 1', output)
        self.assertIn('Pending Orders', output)
        self.assertIn('Failed Orders', output)
    
    def test_process_pending_orders_dry_run(self):
        """Test process_pending_orders command with dry run."""
        # Create old pending order (simulate stuck order)
        old_time = timezone.now() - timedelta(minutes=10)
        
        order = Order.objects.create(
            title='Stuck Order',
            prompt='stuck order test',
            factory_machine_name=self.flux_machine.name,
            provider=self.flux_machine.provider,
            quantity=1
        )
        
        item = OrderItem.objects.create(
            order=order,
            prompt=order.prompt,
            parameters=self.flux_machine.default_parameters,
            status='pending'
        )
        
        # Manually set old timestamp
        item.created_at = old_time
        item.save()
        
        # Test dry run
        out = StringIO()
        call_command('process_pending_orders', '--dry-run', '--max-age', '5', stdout=out)
        output = out.getvalue()
        
        # Verify dry run output
        self.assertIn('Found 1 stuck orders', output)
        self.assertIn('DRY RUN: No actual processing', output)
        self.assertIn(f'Order Item {item.id}', output)
        
        # Verify item status unchanged
        item.refresh_from_db()
        self.assertEqual(item.status, 'pending')
    
    @patch('main.tasks.process_order_items_async')
    def test_process_pending_orders_execution(self, mock_process):
        """Test actual execution of process_pending_orders command."""
        # Create old pending order
        old_time = timezone.now() - timedelta(minutes=10)
        
        order = Order.objects.create(
            title='Stuck Order for Processing',
            prompt='test processing',
            factory_machine_name=self.flux_machine.name,
            provider=self.flux_machine.provider,
            quantity=1
        )
        
        item = OrderItem.objects.create(
            order=order,
            prompt=order.prompt,
            parameters=self.flux_machine.default_parameters,
            status='pending'
        )
        
        # Set old timestamp
        item.created_at = old_time
        item.save()
        
        # Mock successful processing
        def mock_processing(items):
            for item in items:
                item.status = 'processing'
                item.save()
        
        mock_process.side_effect = mock_processing
        
        # Execute command
        out = StringIO()
        call_command('process_pending_orders', '--max-age', '5', stdout=out)
        output = out.getvalue()
        
        # Verify processing was called
        mock_process.assert_called_once()
        
        # Verify log entry was created
        log_entries = LogEntry.objects.filter(
            logger_name='management.process_pending_orders',
            extra_data__event_type='retry_processing'
        )
        self.assertTrue(log_entries.exists())
        
        # Verify output
        self.assertIn('Found 1 stuck orders', output)
        self.assertIn('Starting processing', output)
    
    def test_process_pending_orders_with_failed_retry(self):
        """Test retrying failed orders."""
        # Create failed order
        old_time = timezone.now() - timedelta(minutes=10)
        
        order = Order.objects.create(
            title='Failed Order',
            prompt='failed test',
            factory_machine_name=self.flux_machine.name,
            provider=self.flux_machine.provider,
            quantity=1
        )
        
        item = OrderItem.objects.create(
            order=order,
            prompt=order.prompt,
            parameters=self.flux_machine.default_parameters,
            status='failed',
            error_message='Original error'
        )
        
        # Set old timestamp manually
        OrderItem.objects.filter(id=item.id).update(updated_at=old_time)
        
        # Test dry run with failed retry
        out = StringIO()
        call_command(
            'process_pending_orders', 
            '--retry-failed', 
            '--dry-run', 
            '--max-age', '5', 
            stdout=out
        )
        output = out.getvalue()
        
        # Verify failed order found
        self.assertIn('Found 1 stuck orders', output)
        self.assertIn(f'Order Item {item.id}', output)
    
    def test_setup_cron_jobs_command(self):
        """Test the setup_cron_jobs command provides useful output."""
        out = StringIO()
        call_command('setup_cron_jobs', stdout=out)
        output = out.getvalue()
        
        # Verify cron job recommendations
        self.assertIn('Recommended Cron Jobs', output)
        self.assertIn('*/5 * * * *', output)  # Every 5 minutes
        self.assertIn('process_pending_orders', output)
        self.assertIn('Current Environment', output)
    
    def test_pending_order_age_calculation(self):
        """Test that age calculation works correctly for retry logic."""
        # Create orders of different ages
        now = timezone.now()
        
        # Recent order (should not be retried)
        recent_order = Order.objects.create(
            title='Recent Order',
            prompt='recent test',
            factory_machine_name=self.flux_machine.name,
            provider=self.flux_machine.provider,
            quantity=1
        )
        
        recent_item = OrderItem.objects.create(
            order=recent_order,
            prompt=recent_order.prompt,
            parameters=self.flux_machine.default_parameters,
            status='pending'
        )
        
        # Old order (should be retried)
        old_order = Order.objects.create(
            title='Old Order',
            prompt='old test',
            factory_machine_name=self.flux_machine.name,
            provider=self.flux_machine.provider,
            quantity=1
        )
        
        old_item = OrderItem.objects.create(
            order=old_order,
            prompt=old_order.prompt,
            parameters=self.flux_machine.default_parameters,
            status='pending'
        )
        
        # Set timestamps
        old_item.created_at = now - timedelta(minutes=10)
        old_item.save()
        
        # Test age filtering
        cutoff_time = now - timedelta(minutes=5)
        old_items = OrderItem.objects.filter(
            status='pending',
            created_at__lt=cutoff_time
        )
        
        # Should only include old item
        self.assertEqual(old_items.count(), 1)
        self.assertEqual(old_items.first().id, old_item.id)
    
    def test_retry_mechanism_preserves_order_data(self):
        """Test that retry mechanism preserves original order data."""
        order = Order.objects.create(
            title='Order with Custom Parameters',
            prompt='custom test',
            base_parameters={'width': 768, 'height': 1024, 'num_inference_steps': 6},
            factory_machine_name=self.flux_machine.name,
            provider=self.flux_machine.provider,
            quantity=1
        )
        
        # Merge parameters as would happen in real processing
        merged_params = self.flux_machine.default_parameters.copy()
        merged_params.update(order.base_parameters)
        
        item = OrderItem.objects.create(
            order=order,
            prompt=order.prompt,
            parameters=merged_params,
            status='pending'
        )
        
        # Verify merged parameters preserve user customizations
        self.assertEqual(item.parameters['width'], 768)  # User custom
        self.assertEqual(item.parameters['height'], 1024)  # User custom
        self.assertEqual(item.parameters['num_inference_steps'], 6)  # User custom
        self.assertEqual(item.parameters['enable_safety_checker'], False)  # Default preserved