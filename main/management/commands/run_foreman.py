"""
Management command to run the foreman monitoring process.
Primarily for debugging and manual testing.
"""
from django.core.management.base import BaseCommand
from main.foreman import Foreman


class Command(BaseCommand):
    help = 'Run the foreman process for monitoring worker health'

    def add_arguments(self, parser):
        parser.add_argument(
            '--check-interval',
            type=int,
            default=60,
            help='Seconds between health checks (default: 60)'
        )

    def handle(self, *args, **options):
        check_interval = options['check_interval']
        
        self.stdout.write(
            f"Starting foreman with {check_interval}s check interval"
        )
        
        # Create and run foreman (this will block)
        foreman = Foreman(check_interval=check_interval)
        
        try:
            foreman.run()
        except KeyboardInterrupt:
            self.stdout.write("\nReceived interrupt signal")
            foreman.stop()
        
        self.stdout.write(
            self.style.SUCCESS("Foreman stopped")
        )