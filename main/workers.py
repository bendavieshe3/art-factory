"""
Autonomous worker system for processing OrderItems.
Implements smart workers with automatic spawning and batch processing.
"""

import logging
import os
import random
import threading
import time

from django.db import transaction
from django.utils import timezone

from .error_handling import ErrorCategory, ErrorHandler
from .models import FactoryMachineDefinition, LogEntry, OrderItem, Worker

logger = logging.getLogger(__name__)


class SmartWorker:
    """
    Autonomous worker that processes OrderItems in batches.
    Exits gracefully when no work is available.
    """

    def __init__(self, max_batch_size=5):
        self.max_batch_size = max_batch_size
        # Generate unique process ID to avoid collisions between threads
        self.process_id = os.getpid() * 1000 + random.randint(1, 999)  # nosec B311
        self.name = f"worker-{int(time.time())}-{random.randint(100, 999)}"  # nosec B311
        self.worker_record = None
        self.is_running = True
        self.error_handler = ErrorHandler(provider="universal")

    def run(self):
        """Main worker loop."""
        try:
            self.register_worker()
            logger.info(f"Worker {self.name} started (PID: {self.process_id})")

            while self.is_running:
                # Claim available work
                claimed_items = self.claim_work_batch()

                if not claimed_items:
                    # Check if there are any retryable failed items before exiting
                    retryable_count = self.count_retryable_failed_items()
                    if retryable_count > 0:
                        logger.info(f"Worker {self.name} found {retryable_count} retryable failed items, waiting...")
                        time.sleep(30)  # Wait longer before trying again
                        continue

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
        """Register this worker in the database with retry logic."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                self.worker_record = Worker.objects.create(
                    name=self.name,
                    process_id=self.process_id,
                    provider="universal",  # Can handle any provider
                    max_batch_size=self.max_batch_size,
                    status="starting",
                )
                break
            except Exception as e:
                if attempt == max_attempts - 1:
                    logger.error(f"Failed to register worker after {max_attempts} attempts: {e}")
                    raise
                else:
                    # If PID collision, generate new unique IDs
                    if "UNIQUE constraint failed" in str(e):
                        self.process_id = os.getpid() * 1000 + random.randint(1, 999)  # nosec B311
                        self.name = f"worker-{int(time.time())}-{random.randint(100, 999)}"  # nosec B311

                    # Wait before retry
                    time.sleep(0.1 + (attempt * 0.1))
                    logger.warning(f"Worker registration attempt {attempt + 1} failed, retrying: {e}")

        LogEntry.objects.create(
            level="INFO",
            message=f"Worker {self.name} registered (PID: {self.process_id})",
            logger_name="worker",
            extra_data={"event_type": "worker_started", "worker_id": self.worker_record.id, "provider": "universal"},
        )

    def claim_work_batch(self):
        """Atomically claim multiple OrderItems for processing with retry logic."""
        max_attempts = 3
        for attempt in range(max_attempts):
            try:
                with transaction.atomic():
                    # Find available work for any provider (including retries)
                    available_items = (
                        OrderItem.objects.select_for_update()
                        .filter(status="pending")
                        .order_by("created_at")[: self.max_batch_size]
                    )

                    # Also look for failed items that can be retried
                    retry_items = (
                        OrderItem.objects.select_for_update()
                        .filter(status="failed")
                        .order_by("last_retry_at")[: self.max_batch_size]
                    )

                    # Check which failed items can be retried
                    retryable_items = []
                    for item in retry_items:
                        if item.can_be_retried():
                            retryable_items.append(item)

                    # Combine available items and retryable items
                    all_items = list(available_items) + retryable_items

                    claimed_items = []
                    for item in all_items[: self.max_batch_size]:
                        if self.can_process_item(item):
                            if item.status == "failed":
                                # Reset for retry
                                item.reset_for_retry()
                                logger.info(f"Worker {self.name} retrying item {item.id} (attempt {item.retry_count})")

                            item.status = "assigned"
                            item.assigned_worker = self.worker_record
                            item.save()
                            claimed_items.append(item)

                    if claimed_items:
                        # Update worker status
                        self.worker_record.status = "working"
                        self.worker_record.save()

                        logger.info(f"Worker {self.name} claimed {len(claimed_items)} items")

                    return claimed_items

            except Exception as e:
                if attempt == max_attempts - 1:
                    logger.error(f"Worker {self.name} failed to claim work after {max_attempts} attempts: {e}")
                    return []
                else:
                    # Wait before retry for database lock issues
                    wait_time = 0.1 + (attempt * 0.2)
                    logger.warning(f"Worker {self.name} claim attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)

    def can_process_item(self, order_item):
        """Check if this item can be processed given current constraints."""
        try:
            # Get machine definition for rate limiting
            machine_def = FactoryMachineDefinition.objects.get(name=order_item.order.factory_machine_name)

            # For now, allow processing - rate limiting can be enhanced later
            # TODO: Implement sophisticated rate limiting based on parameter_schema
            return True

        except FactoryMachineDefinition.DoesNotExist:
            logger.warning(f"Machine definition not found: {order_item.order.factory_machine_name}")
            return False
        except Exception as e:
            logger.error(f"Error checking processing constraints: {e}")
            return False

    def count_retryable_failed_items(self):
        """Count how many failed items can be retried."""
        failed_items = OrderItem.objects.filter(status="failed")
        retryable_count = 0
        for item in failed_items:
            if item.can_be_retried():
                retryable_count += 1
        return retryable_count

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
        order_item.status = "processing"
        order_item.started_at = timezone.now()
        order_item.save()

        # Log processing start
        LogEntry.objects.create(
            level="INFO",
            message=f"Worker {self.name} processing item {order_item.id}",
            logger_name="worker",
            order=order_item.order,
            order_item=order_item,
            extra_data={"event_type": "item_processing", "worker_id": self.worker_record.id},
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
                level="INFO",
                message=f"Worker {self.name} completed item {order_item.id} - {product_count} products created",
                logger_name="worker",
                order=order_item.order,
                order_item=order_item,
                extra_data={
                    "event_type": "item_completed",
                    "worker_id": self.worker_record.id,
                    "products_created": product_count,
                    "batch_complete": True,
                },
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

        completed_items = items.filter(status="completed").count()
        failed_items = items.filter(status="failed")
        exhausted_items = items.filter(status="exhausted").count()
        pending_items = items.filter(status__in=["pending", "assigned", "processing"]).count()

        # Separate retryable from non-retryable failed items
        retryable_failed_items = 0
        permanent_failed_items = 0
        for item in failed_items:
            if item.can_be_retried():
                retryable_failed_items += 1
            else:
                permanent_failed_items += 1

        # Final states: completed, permanently failed, exhausted
        # Retryable failed items are NOT considered final
        final_items = completed_items + permanent_failed_items + exhausted_items

        if completed_items == total_items:
            # All items completed successfully
            order.status = "completed"
            order.completed_at = timezone.now()
        elif retryable_failed_items > 0 or pending_items > 0:
            # Has retryable items or still processing - keep as processing
            order.status = "processing"
        elif final_items == total_items:
            # All items are in final state (no retryable failures)
            if completed_items == total_items:
                # All items succeeded - full completion
                order.status = "completed"
            elif completed_items > 0:
                # Some success, some failure - partial completion
                order.status = "partially_completed"
            else:
                # No successes - total failure
                order.status = "failed"
            order.completed_at = timezone.now()
        else:
            # Some progress made but not all final
            order.status = "processing"

        order.save()

    def handle_item_failure(self, order_item, error_message):
        """Handle failure of a single OrderItem with comprehensive error analysis."""
        # Get provider from order for better error analysis
        provider = order_item.order.provider if hasattr(order_item.order, "provider") else "unknown"

        # Use error handler to analyze and categorize the error
        error_info = self.error_handler.handle_error(
            error_message,
            order_item,
            context={
                "provider": provider,
                "operation": "worker_processing",
                "worker": self.name,
            },
        )

        # Update order item based on error analysis
        order_item.error_message = error_info["friendly_message"]["message"]
        order_item.error_category = error_info["category"]
        order_item.completed_at = timezone.now()

        if error_info["should_retry"] and order_item.retry_count < order_item.max_retries:
            # Mark as failed but retryable
            order_item.status = "failed"

            logger.info(
                f"Worker {self.name} marking item {order_item.id} for retry (attempt {order_item.retry_count + 1}/{order_item.max_retries}): {error_info['category']}"
            )

            # Log as INFO since it will be retried
            LogEntry.objects.create(
                level="INFO",
                message=f"Worker {self.name} item {order_item.id} will retry: {error_info['friendly_message']['title']}",
                logger_name="worker",
                order=order_item.order,
                order_item=order_item,
                extra_data={
                    "event_type": "item_retry_scheduled",
                    "worker_id": self.worker_record.id,
                    "error_category": error_info["category"],
                    "retry_delay": error_info["retry_delay"],
                    "technical_error": error_message,
                    "user_message": error_info["friendly_message"]["message"],
                    "retry_count": order_item.retry_count,
                    "max_retries": order_item.max_retries,
                },
            )
        else:
            # Permanent failure or max retries exhausted
            if order_item.retry_count >= order_item.max_retries:
                order_item.status = "exhausted"
                logger.error(f"Worker {self.name} item {order_item.id} exhausted retries: {error_info['category']}")
            else:
                order_item.status = "failed"
                logger.error(f"Worker {self.name} item {order_item.id} permanent failure: {error_info['category']}")

            # Log as ERROR since it won't be retried
            LogEntry.objects.create(
                level="ERROR",
                message=f"Worker {self.name} failed item {order_item.id} (final): {error_info['friendly_message']['title']}",
                logger_name="worker",
                order=order_item.order,
                order_item=order_item,
                extra_data={
                    "event_type": "item_failed_final",
                    "worker_id": self.worker_record.id,
                    "error_category": error_info["category"],
                    "technical_error": error_message,
                    "user_message": error_info["friendly_message"]["message"],
                    "retry_count": order_item.retry_count,
                    "max_retries": order_item.max_retries,
                },
            )

        order_item.save()

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
            level="INFO",
            message=f"Worker {self.name} exiting: {reason}",
            logger_name="worker",
            extra_data={
                "event_type": "worker_exit",
                "worker_id": self.worker_record.id if self.worker_record else None,
                "reason": reason,
            },
        )

        # Clean up worker record
        if self.worker_record:
            self.worker_record.delete()

        self.is_running = False

    def error_exit(self, error_message):
        """Exit due to error."""
        logger.error(f"Worker {self.name} error exit: {error_message}")

        LogEntry.objects.create(
            level="ERROR",
            message=f"Worker {self.name} error exit: {error_message}",
            logger_name="worker",
            extra_data={
                "event_type": "worker_error_exit",
                "worker_id": self.worker_record.id if self.worker_record else None,
                "error": error_message,
            },
        )

        # Mark any assigned work as pending for retry
        if self.worker_record:
            assigned_items = OrderItem.objects.filter(
                assigned_worker=self.worker_record, status__in=["assigned", "processing"]
            )
            assigned_items.update(status="pending", assigned_worker=None)

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

        logger.info("Spawned universal worker thread")

    except Exception as e:
        logger.error(f"Failed to spawn worker: {e}")


def run_smart_worker(max_batch_size=5):
    """Run a smart worker (used for management commands)."""
    worker = SmartWorker(max_batch_size=max_batch_size)
    worker.run()
