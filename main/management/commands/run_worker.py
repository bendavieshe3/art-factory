"""
Management command to run a single smart worker.
Primarily for debugging and manual testing.
"""

from django.core.management.base import BaseCommand

from main.workers import run_smart_worker


class Command(BaseCommand):
    help = "Run a single smart worker for processing OrderItems"

    def add_arguments(self, parser):
        parser.add_argument("--batch-size", type=int, default=5, help="Maximum items to process in one batch (default: 5)")

    def handle(self, *args, **options):
        batch_size = options["batch_size"]

        self.stdout.write(f"Starting universal smart worker with batch size {batch_size}")

        # Run the worker (this will block until worker exits)
        run_smart_worker(max_batch_size=batch_size)

        self.stdout.write(self.style.SUCCESS("Worker completed and exited"))
