"""
Autonomous worker system for processing OrderItems.
Implements smart workers with automatic spawning and batch processing.
"""
import os
import time
import threading
import logging
from datetime import timedelta
from django.db import transaction
from django.utils import timezone
from django.conf import settings

from .models import Worker, OrderItem, FactoryMachineDefinition, LogEntry

logger = logging.getLogger(__name__)


class SmartWorker:
    """
    Autonomous worker that processes OrderItems in batches.
    Exits gracefully when no work is available.
    """
    
    def __init__(self, max_batch_size=5):
        self.max_batch_size = max_batch_size
        self.process_id = os.getpid()
        self.name = f"worker-{int(time.time())}"
        self.worker_record = None
        self.is_running = True
        
    def run(self):
        """Main worker loop."""
        try:
            self.register_worker()
            logger.info(f"Worker {self.name} started (PID: {self.process_id})")
            
            while self.is_running:
                # Claim available work
                claimed_items = self.claim_work_batch()
                
                if not claimed_items:
                    # No work available - exit gracefully
                    self.graceful_exit("No pending work available")
                    return
                
                # Process the batch
                self.process_batch(claimed_items)
                
                # Update heartbeat
                self.update_heartbeat()
                
                # Brief pause before next cycle
                time.sleep(10)
                
        except Exception as e:
            logger.error(f"Worker {self.name} encountered error: {e}")
            self.error_exit(str(e))
    
    def register_worker(self):
        """Register this worker in the database."""
        self.worker_record = Worker.objects.create(
            name=self.name,
            process_id=self.process_id,
            provider='universal',  # Can handle any provider
            max_batch_size=self.max_batch_size,
            status='starting'
        )
        
        LogEntry.objects.create(
            level='INFO',
            message=f'Worker {self.name} registered (PID: {self.process_id})',
            logger_name='worker',
            extra_data={
                'event_type': 'worker_started',
                'worker_id': self.worker_record.id,
                'provider': 'universal'
            }
        )
    
    def claim_work_batch(self):
        """Atomically claim multiple OrderItems for processing."""
        try:
            with transaction.atomic():
                # Find available work for any provider
                available_items = OrderItem.objects.select_for_update().filter(
                    status='pending'
                ).order_by('created_at')[:self.max_batch_size]
                
                claimed_items = []
                for item in available_items:
                    if self.can_process_item(item):
                        item.status = 'assigned'
                        item.assigned_worker = self.worker_record
                        item.save()
                        claimed_items.append(item)
                
                if claimed_items:
                    # Update worker status
                    self.worker_record.status = 'working'
                    self.worker_record.save()
                    
                    logger.info(f"Worker {self.name} claimed {len(claimed_items)} items")
                
                return claimed_items
                
        except Exception as e:
            logger.error(f"Worker {self.name} failed to claim work: {e}")
            return []
    
    def can_process_item(self, order_item):
        """Check if this item can be processed given current constraints."""
        try:
            # Get machine definition for rate limiting
            machine_def = FactoryMachineDefinition.objects.get(
                name=order_item.order.factory_machine_name
            )
            
            # For now, allow processing - rate limiting can be enhanced later
            # TODO: Implement sophisticated rate limiting based on parameter_schema
            return True
            
        except FactoryMachineDefinition.DoesNotExist:
            logger.warning(f"Machine definition not found: {order_item.order.factory_machine_name}")
            return False
        except Exception as e:
            logger.error(f"Error checking processing constraints: {e}")
            return False
    
    def process_batch(self, order_items):
        """Process a batch of OrderItems."""
        logger.info(f"Worker {self.name} processing batch of {len(order_items)} items")
        
        for item in order_items:
            try:
                self.process_single_item(item)
                self.worker_record.items_processed += 1
                
            except Exception as e:
                logger.error(f"Worker {self.name} failed to process item {item.id}: {e}")
                self.handle_item_failure(item, str(e))
                self.worker_record.items_failed += 1
        
        # Update worker metrics
        self.worker_record.save()
    
    def process_single_item(self, order_item):
        """Process a single OrderItem using synchronous batch factory machines."""
        # Import here to avoid circular imports
        from .factory_machines_sync import execute_order_item_sync_batch
        
        # Update item status
        order_item.status = 'processing'
        order_item.started_at = timezone.now()
        order_item.save()
        
        # Log processing start
        LogEntry.objects.create(
            level='INFO',
            message=f'Worker {self.name} processing item {order_item.id}',
            logger_name='worker',
            order=order_item.order,
            order_item=order_item,
            extra_data={
                'event_type': 'item_processing',
                'worker_id': self.worker_record.id
            }
        )
        
        # Use synchronous batch factory machines
        success = execute_order_item_sync_batch(order_item.id)
        
        # Handle result
        if success:
            # Refresh order item to get updated data
            order_item.refresh_from_db()
            
            # Log completion with product count
            products = order_item.products.all()
            product_count = products.count()
            
            LogEntry.objects.create(
                level='INFO',
                message=f'Worker {self.name} completed item {order_item.id} - {product_count} products created',
                logger_name='worker',
                order=order_item.order,
                order_item=order_item,
                extra_data={
                    'event_type': 'item_completed',
                    'worker_id': self.worker_record.id,
                    'products_created': product_count,
                    'batch_complete': True
                }
            )
            
            # Update order status
            self.update_order_status(order_item.order)
            
        else:
            # Refresh order item to get current status
            order_item.refresh_from_db()
            # Update order status even on failure
            self.update_order_status(order_item.order)
            raise Exception("Processing failed - check logs for details")
    
    def update_order_status(self, order):
        """Update order status based on its items."""
        items = order.orderitem_set.all()
        total_items = items.count()
        
        if total_items == 0:
            return
            
        completed_items = items.filter(status='completed').count()
        failed_items = items.filter(status='failed').count()
        
        if completed_items == total_items:
            order.status = 'completed'
            order.completed_at = timezone.now()
        elif failed_items == total_items:
            order.status = 'failed'
            order.completed_at = timezone.now()
        elif completed_items + failed_items == total_items:
            order.status = 'completed'  # Partial success
            order.completed_at = timezone.now()
        elif completed_items > 0 or failed_items > 0:
            order.status = 'processing'
        
        order.save()
    
    def handle_item_failure(self, order_item, error_message):
        """Handle failure of a single OrderItem."""
        order_item.status = 'failed'
        order_item.error_message = error_message
        order_item.completed_at = timezone.now()
        order_item.save()
        
        # Log failure
        LogEntry.objects.create(
            level='ERROR',
            message=f'Worker {self.name} failed item {order_item.id}: {error_message}',
            logger_name='worker',
            order=order_item.order,
            order_item=order_item,
            extra_data={
                'event_type': 'item_failed',
                'worker_id': self.worker_record.id,
                'error': error_message
            }
        )
        
        # Update order status after item failure
        self.update_order_status(order_item.order)
    
    def update_heartbeat(self):
        """Update worker heartbeat."""
        if self.worker_record:
            self.worker_record.update_heartbeat()
    
    def graceful_exit(self, reason):
        """Exit gracefully when no work is available."""
        logger.info(f"Worker {self.name} exiting: {reason}")
        
        LogEntry.objects.create(
            level='INFO',
            message=f'Worker {self.name} exiting: {reason}',
            logger_name='worker',
            extra_data={
                'event_type': 'worker_exit',
                'worker_id': self.worker_record.id if self.worker_record else None,
                'reason': reason
            }
        )
        
        # Clean up worker record
        if self.worker_record:
            self.worker_record.delete()
        
        self.is_running = False
    
    def error_exit(self, error_message):
        """Exit due to error."""
        logger.error(f"Worker {self.name} error exit: {error_message}")
        
        LogEntry.objects.create(
            level='ERROR',
            message=f'Worker {self.name} error exit: {error_message}',
            logger_name='worker',
            extra_data={
                'event_type': 'worker_error_exit',
                'worker_id': self.worker_record.id if self.worker_record else None,
                'error': error_message
            }
        )
        
        # Mark any assigned work as pending for retry
        if self.worker_record:
            assigned_items = OrderItem.objects.filter(
                assigned_worker=self.worker_record,
                status__in=['assigned', 'processing']
            )
            assigned_items.update(status='pending', assigned_worker=None)
            
            # Clean up worker record
            self.worker_record.delete()
        
        self.is_running = False


def spawn_worker_automatically():
    """Spawn a universal worker process automatically without user intervention."""
    try:
        # Start worker in background thread
        worker = SmartWorker()
        worker_thread = threading.Thread(target=worker.run)
        worker_thread.daemon = True
        worker_thread.start()
        
        logger.info(f"Spawned universal worker thread")
        
    except Exception as e:
        logger.error(f"Failed to spawn worker: {e}")


def run_smart_worker(max_batch_size=5):
    """Run a smart worker (used for management commands)."""
    worker = SmartWorker(max_batch_size=max_batch_size)
    worker.run()