"""
Tests for the autonomous worker system.
"""
import os
import time
import threading
from unittest.mock import patch, Mock
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta

from .models import Order, OrderItem, FactoryMachineDefinition
from .models.orders import Worker
from .workers import SmartWorker, spawn_worker_automatically
from .foreman import Foreman


class WorkerSystemTestCase(TestCase):
    """Test the autonomous worker system."""
    
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
    
    def test_worker_model_creation(self):
        """Test Worker model creation and basic functionality."""
        worker = Worker.objects.create(
            name='test-worker',
            process_id=12345,
            provider='fal.ai',
            max_batch_size=3,
            status='starting'
        )
        
        self.assertEqual(worker.name, 'test-worker')
        self.assertEqual(worker.process_id, 12345)
        self.assertEqual(worker.provider, 'fal.ai')
        self.assertEqual(worker.max_batch_size, 3)
        self.assertEqual(worker.status, 'starting')
        self.assertEqual(worker.items_processed, 0)
        self.assertEqual(worker.items_failed, 0)
        
        # Test stall detection
        self.assertFalse(worker.is_stalled())
        
        # Make worker appear stalled
        old_time = timezone.now() - timedelta(minutes=5)
        Worker.objects.filter(id=worker.id).update(last_heartbeat=old_time)
        worker.refresh_from_db()
        self.assertTrue(worker.is_stalled())
    
    def test_order_item_status_choices(self):
        """Test that new status choices are available."""
        order = Order.objects.create(
            title='Test Order',
            prompt='test prompt',
            factory_machine_name=self.flux_machine.name,
            provider=self.flux_machine.provider,
            quantity=1
        )
        
        item = OrderItem.objects.create(
            order=order,
            prompt=order.prompt,
            parameters=self.flux_machine.default_parameters,
            status='assigned'  # New status
        )
        
        self.assertEqual(item.status, 'assigned')
        self.assertTrue(item.can_be_assigned())  # Should be False for assigned items
        
        # Test stalled status
        item.status = 'stalled'
        item.save()
        self.assertEqual(item.status, 'stalled')
    
    def test_smart_worker_initialization(self):
        """Test SmartWorker initialization."""
        worker = SmartWorker(provider='fal.ai', max_batch_size=3)
        
        self.assertEqual(worker.provider, 'fal.ai')
        self.assertEqual(worker.max_batch_size, 3)
        self.assertTrue(worker.is_running)
        self.assertIsNotNone(worker.process_id)
        self.assertIsNotNone(worker.name)
    
    @patch('main.workers.SimpleProcessCommand')
    def test_worker_work_claiming(self, mock_processor_class):
        """Test worker work claiming logic."""
        # Create test order items
        order = Order.objects.create(
            title='Test Batch Order',
            prompt='test batch processing',
            factory_machine_name=self.flux_machine.name,
            provider=self.flux_machine.provider,
            quantity=3
        )
        
        items = []
        for i in range(3):
            item = OrderItem.objects.create(
                order=order,
                prompt=f'{order.prompt} {i}',
                parameters=self.flux_machine.default_parameters,
                status='pending'
            )
            items.append(item)
        
        # Create and register worker
        worker = SmartWorker(provider='fal.ai', max_batch_size=2)
        worker.register_worker()
        
        # Test work claiming
        claimed_items = worker.claim_work_batch()
        
        # Should claim 2 items (batch size limit)
        self.assertEqual(len(claimed_items), 2)
        
        # Check that items are marked as assigned
        for item in claimed_items:
            item.refresh_from_db()
            self.assertEqual(item.status, 'assigned')
            self.assertEqual(item.assigned_worker, worker.worker_record)
        
        # Worker should be marked as working
        worker.worker_record.refresh_from_db()
        self.assertEqual(worker.worker_record.status, 'working')
        
        # Third item should still be pending
        remaining_item = OrderItem.objects.get(id=items[2].id)
        self.assertEqual(remaining_item.status, 'pending')
        self.assertIsNone(remaining_item.assigned_worker)
    
    def test_worker_no_work_exit(self):
        """Test that worker exits when no work is available."""
        worker = SmartWorker(provider='fal.ai', max_batch_size=5)
        worker.register_worker()
        
        # No OrderItems exist, so worker should find no work
        claimed_items = worker.claim_work_batch()
        self.assertEqual(len(claimed_items), 0)
        
        # Simulate graceful exit
        worker.graceful_exit("No work available")
        self.assertFalse(worker.is_running)
        
        # Worker record should be cleaned up
        self.assertFalse(Worker.objects.filter(id=worker.worker_record.id).exists())
    
    def test_foreman_stalled_worker_detection(self):
        """Test foreman detection of stalled workers."""
        # Create a stalled worker
        old_time = timezone.now() - timedelta(minutes=5)
        stalled_worker = Worker.objects.create(
            name='stalled-worker',
            process_id=99999,  # Non-existent PID
            provider='fal.ai',
            status='working'
        )
        
        # Manually set old heartbeat
        Worker.objects.filter(id=stalled_worker.id).update(last_heartbeat=old_time)
        
        # Create some assigned work for the stalled worker
        order = Order.objects.create(
            title='Stalled Work',
            prompt='work assigned to stalled worker',
            factory_machine_name=self.flux_machine.name,
            provider=self.flux_machine.provider,
            quantity=2
        )
        
        for i in range(2):
            OrderItem.objects.create(
                order=order,
                prompt=f'{order.prompt} {i}',
                parameters=self.flux_machine.default_parameters,
                status='assigned',
                assigned_worker=stalled_worker
            )
        
        # Run foreman cycle
        foreman = Foreman()
        foreman.handle_stalled_workers()
        
        # Stalled worker should be removed
        self.assertFalse(Worker.objects.filter(id=stalled_worker.id).exists())
        
        # Assigned work should be reassigned to pending
        reassigned_items = OrderItem.objects.filter(order=order)
        for item in reassigned_items:
            self.assertEqual(item.status, 'pending')
            self.assertIsNone(item.assigned_worker)
    
    def test_foreman_orphaned_work_detection(self):
        """Test foreman detection of orphaned work."""
        # Create orphaned work (assigned but no worker)
        order = Order.objects.create(
            title='Orphaned Work',
            prompt='work with no assigned worker',
            factory_machine_name=self.flux_machine.name,
            provider=self.flux_machine.provider,
            quantity=1
        )
        
        orphaned_item = OrderItem.objects.create(
            order=order,
            prompt=order.prompt,
            parameters=self.flux_machine.default_parameters,
            status='assigned',
            assigned_worker=None  # No worker assigned
        )
        
        # Run foreman cycle
        foreman = Foreman()
        foreman.reassign_orphaned_work()
        
        # Orphaned work should be reassigned to pending
        orphaned_item.refresh_from_db()
        self.assertEqual(orphaned_item.status, 'pending')
    
    def test_spawn_worker_automatically(self):
        """Test automatic worker spawning."""
        # Mock the threading to avoid actual thread creation in tests
        with patch('main.workers.threading.Thread') as mock_thread:
            spawn_worker_automatically(provider='fal.ai')
            
            # Verify thread was created and started
            mock_thread.assert_called_once()
            mock_thread.return_value.start.assert_called_once()
    
    def test_worker_batch_processing_scenario(self):
        """Test the scenario described: 20 items with 5-item limit."""
        # Create order with 20 items
        order = Order.objects.create(
            title='Large Batch Order',
            prompt='test large batch processing',
            factory_machine_name=self.flux_machine.name,
            provider=self.flux_machine.provider,
            quantity=20
        )
        
        items = []
        for i in range(20):
            item = OrderItem.objects.create(
                order=order,
                prompt=f'{order.prompt} {i}',
                parameters=self.flux_machine.default_parameters,
                status='pending'
            )
            items.append(item)
        
        # Create worker with 5-item batch limit
        worker = SmartWorker(provider='fal.ai', max_batch_size=5)
        worker.register_worker()
        
        # Worker should be able to claim multiple batches
        first_batch = worker.claim_work_batch()
        self.assertEqual(len(first_batch), 5)
        
        # Simulate completing first batch
        for item in first_batch:
            item.status = 'completed'
            item.assigned_worker = None
            item.save()
        
        # Worker can claim next batch
        second_batch = worker.claim_work_batch()
        self.assertEqual(len(second_batch), 5)
        
        # Verify total progress
        completed_count = OrderItem.objects.filter(order=order, status='completed').count()
        assigned_count = OrderItem.objects.filter(order=order, status='assigned').count()
        pending_count = OrderItem.objects.filter(order=order, status='pending').count()
        
        self.assertEqual(completed_count, 5)  # First batch
        self.assertEqual(assigned_count, 5)   # Second batch
        self.assertEqual(pending_count, 10)   # Remaining
    
    def test_multiple_workers_different_providers(self):
        """Test multiple workers for different providers."""
        # Create Replicate machine
        replicate_machine = FactoryMachineDefinition.objects.create(
            name='replicate/flux-schnell',
            display_name='FLUX Schnell (Replicate)',
            provider='replicate',
            modality='text-to-image',
            parameter_schema={'prompt': 'string'},
            default_parameters={'width': 1024, 'height': 1024},
            is_active=True
        )
        
        # Create orders for different providers
        fal_order = Order.objects.create(
            title='Fal.ai Order',
            prompt='fal.ai test',
            factory_machine_name=self.flux_machine.name,
            provider='fal.ai',
            quantity=2
        )
        
        replicate_order = Order.objects.create(
            title='Replicate Order',
            prompt='replicate test',
            factory_machine_name=replicate_machine.name,
            provider='replicate',
            quantity=2
        )
        
        # Create order items
        for order in [fal_order, replicate_order]:
            for i in range(order.quantity):
                OrderItem.objects.create(
                    order=order,
                    prompt=f'{order.prompt} {i}',
                    parameters=order.base_parameters or {},
                    status='pending'
                )
        
        # Create workers for different providers
        fal_worker = SmartWorker(provider='fal.ai', max_batch_size=5)
        fal_worker.register_worker()
        
        replicate_worker = SmartWorker(provider='replicate', max_batch_size=5)
        replicate_worker.register_worker()
        
        # Each worker should only claim work for their provider
        fal_claimed = fal_worker.claim_work_batch()
        replicate_claimed = replicate_worker.claim_work_batch()
        
        self.assertEqual(len(fal_claimed), 2)
        self.assertEqual(len(replicate_claimed), 2)
        
        # Verify provider isolation
        for item in fal_claimed:
            self.assertEqual(item.order.provider, 'fal.ai')
        
        for item in replicate_claimed:
            self.assertEqual(item.order.provider, 'replicate')