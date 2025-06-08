"""
Management command to process pending orders with retry logic.
Handles stuck orders that failed initial processing.
"""

import logging
import time
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from main.models import LogEntry, OrderItem
from main.tasks import process_order_items_async

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = "Process pending orders with retry logic for stuck/failed orders"

    def add_arguments(self, parser):
        parser.add_argument("--max-age", type=int, default=5, help="Maximum age in minutes for orders to retry (default: 5)")
        parser.add_argument(
            "--batch-size", type=int, default=5, help="Maximum number of orders to process at once (default: 5)"
        )
        parser.add_argument("--retry-failed", action="store_true", help="Also retry failed orders (not just pending)")
        parser.add_argument("--dry-run", action="store_true", help="Show what would be processed without actually processing")

    def handle(self, *args, **options):
        max_age_minutes = options["max_age"]
        batch_size = options["batch_size"]
        retry_failed = options["retry_failed"]
        dry_run = options["dry_run"]

        # Calculate cutoff time for "stuck" orders
        cutoff_time = timezone.now() - timedelta(minutes=max_age_minutes)

        self.stdout.write(f"Processing pending orders older than {max_age_minutes} minutes...")

        # Find pending orders that are stuck
        query_filter = {"status": "pending", "created_at__lt": cutoff_time}
        pending_items = OrderItem.objects.filter(**query_filter).order_by("created_at")

        # Optionally include failed orders
        if retry_failed:
            failed_items = OrderItem.objects.filter(status="failed", updated_at__lt=cutoff_time).order_by("updated_at")

            # Combine querysets
            from django.db.models import Q

            all_items = OrderItem.objects.filter(
                Q(status="pending", created_at__lt=cutoff_time) | Q(status="failed", updated_at__lt=cutoff_time)
            ).order_by("created_at")[:batch_size]
        else:
            all_items = pending_items[:batch_size]

        if not all_items:
            self.stdout.write(self.style.SUCCESS("No stuck orders found to process"))
            return

        self.stdout.write(f"Found {len(all_items)} stuck orders to process:")

        for item in all_items:
            age = timezone.now() - (item.updated_at if item.status == "failed" else item.created_at)
            self.stdout.write(
                f"  - Order Item {item.id} (Order {item.order.id}): "
                f"{item.status} for {age} - Machine: {item.order.factory_machine_name}"
            )

        if dry_run:
            self.stdout.write(self.style.WARNING("DRY RUN: No actual processing performed"))
            return

        # Log the retry attempt
        LogEntry.objects.create(
            level="INFO",
            message=f"Retrying {len(all_items)} stuck orders (max age: {max_age_minutes}m)",
            logger_name="management.process_pending_orders",
            extra_data={"event_type": "retry_processing", "item_count": len(all_items), "max_age_minutes": max_age_minutes},
        )

        # Reset status to pending for failed items being retried
        if retry_failed:
            failed_items_to_retry = [item for item in all_items if item.status == "failed"]
            for item in failed_items_to_retry:
                item.status = "pending"
                item.error_message = ""
                item.save()
                self.stdout.write(f"Reset failed order item {item.id} to pending for retry")

        # Process the items
        try:
            self.stdout.write("Starting processing...")
            process_order_items_async(list(all_items))

            # Wait a moment for processing to start
            time.sleep(2)

            # Check results
            processed_count = 0
            for item in all_items:
                item.refresh_from_db()
                if item.status in ["completed", "processing"]:
                    processed_count += 1

            self.stdout.write(
                self.style.SUCCESS(
                    f"Processing initiated: {processed_count}/{len(all_items)} orders " f"are now processing or completed"
                )
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during processing: {e}"))
            logger.error(f"Error in process_pending_orders command: {e}")

            # Log the error
            LogEntry.objects.create(
                level="ERROR",
                message=f"Failed to retry stuck orders: {str(e)}",
                logger_name="management.process_pending_orders",
                extra_data={"event_type": "retry_error", "error": str(e)},
            )
