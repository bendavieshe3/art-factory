"""
Management command to help set up cron jobs for production order processing.
Provides recommended crontab entries for asynchronous order retry.
"""

import os

from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Show recommended cron job setup for production order processing"

    def add_arguments(self, parser):
        parser.add_argument("--install", action="store_true", help="Show installation commands for crontab setup")

    def handle(self, *args, **options):
        show_install = options["install"]

        project_dir = settings.BASE_DIR
        python_path = os.path.join(project_dir, "venv", "bin", "python")
        manage_py = os.path.join(project_dir, "manage.py")

        self.stdout.write(self.style.HTTP_INFO("Recommended Cron Jobs for Production Order Processing"))
        self.stdout.write("=" * 70)

        cron_entries = [
            {
                "schedule": "*/5 * * * *",
                "command": f"cd {project_dir} && {python_path} {manage_py} process_pending_orders --max-age 5",
                "description": "Process stuck orders every 5 minutes (orders older than 5 minutes)",
            },
            {
                "schedule": "*/15 * * * *",
                "command": f"cd {project_dir} && {python_path} {manage_py} process_pending_orders --retry-failed --max-age 30",
                "description": "Retry failed orders every 15 minutes (failures older than 30 minutes)",
            },
            {
                "schedule": "0 */6 * * *",
                "command": f"cd {project_dir} && {python_path} {manage_py} monitor_orders --pending-only > /tmp/art_factory_monitor.log",
                "description": "Monitor system health every 6 hours and log issues",
            },
        ]

        self.stdout.write("Recommended crontab entries:")
        self.stdout.write("")

        for entry in cron_entries:
            self.stdout.write(f"# {entry['description']}")
            self.stdout.write(f"{entry['schedule']} {entry['command']}")
            self.stdout.write("")

        if show_install:
            self.stdout.write(self.style.SUCCESS("Installation Instructions:"))
            self.stdout.write("")
            self.stdout.write("1. Open crontab for editing:")
            self.stdout.write("   crontab -e")
            self.stdout.write("")
            self.stdout.write("2. Add the above entries to your crontab")
            self.stdout.write("")
            self.stdout.write("3. Verify crontab installation:")
            self.stdout.write("   crontab -l")
            self.stdout.write("")
            self.stdout.write("4. Test commands manually first:")
            for entry in cron_entries[:2]:  # Show first 2 for testing
                self.stdout.write(f"   {entry['command']}")
            self.stdout.write("")

        self.stdout.write(self.style.WARNING("Important Notes:"))
        self.stdout.write("")
        self.stdout.write("• Ensure virtual environment is activated in cron jobs")
        self.stdout.write("• Test commands manually before adding to crontab")
        self.stdout.write("• Monitor logs for any cron job failures")
        self.stdout.write("• Adjust timing based on your API rate limits")
        self.stdout.write("")

        self.stdout.write(self.style.SUCCESS("Alternative: Docker/Systemd Timer"))
        self.stdout.write("")
        self.stdout.write("For containerized deployments, consider using:")
        self.stdout.write("• Docker Compose with separate worker container")
        self.stdout.write("• Systemd timers instead of cron")
        self.stdout.write("• Kubernetes CronJobs for cloud deployments")
        self.stdout.write("")

        # Show current environment info
        self.stdout.write(self.style.HTTP_INFO("Current Environment:"))
        self.stdout.write(f"• Project Directory: {project_dir}")
        self.stdout.write(f"• Python Path: {python_path}")
        self.stdout.write(f"• Manage.py: {manage_py}")
        self.stdout.write(f"• Virtual Environment: {'✅ Found' if os.path.exists(python_path) else '❌ Not Found'}")
