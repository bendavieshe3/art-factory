"""
Management command to show current worker and system status.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from main.models import Worker, OrderItem


class Command(BaseCommand):
    help = "Show current worker and system status"

    def add_arguments(self, parser):
        parser.add_argument("--detailed", action="store_true", help="Show detailed information about each worker")

    def handle(self, *args, **options):
        detailed = options["detailed"]

        self.stdout.write(self.style.HTTP_INFO("Worker System Status"))
        self.stdout.write("=" * 50)

        # Show workers
        workers = Worker.objects.all().order_by("-spawned_at")

        if workers:
            self.stdout.write(f"\n📋 Active Workers ({workers.count()}):")
            for worker in workers:
                age = timezone.now() - worker.spawned_at
                last_heartbeat_age = timezone.now() - worker.last_heartbeat

                status_emoji = {"starting": "🔄", "working": "⚙️", "exiting": "🔚"}.get(worker.status, "❓")

                # Check if worker is stalled
                is_stalled = worker.is_stalled()
                stall_indicator = " ⚠️ STALLED" if is_stalled else ""

                self.stdout.write(f"  {status_emoji} {worker.name} (PID: {worker.process_id}){stall_indicator}")

                if detailed:
                    self.stdout.write(f"    Provider: {worker.provider}")
                    self.stdout.write(f"    Status: {worker.status}")
                    self.stdout.write(f"    Age: {age}")
                    self.stdout.write(f"    Last heartbeat: {last_heartbeat_age} ago")
                    self.stdout.write(f"    Processed: {worker.items_processed}, Failed: {worker.items_failed}")

                    # Show assigned work
                    assigned_items = OrderItem.objects.filter(assigned_worker=worker)
                    if assigned_items.exists():
                        self.stdout.write(f"    Assigned items: {assigned_items.count()}")
                    self.stdout.write("")
        else:
            self.stdout.write("\n🔇 No active workers")

        # Show work queue status
        self.stdout.write(f"\n📊 Work Queue Status:")

        status_counts = {}
        for status_choice in OrderItem.STATUS_CHOICES:
            status = status_choice[0]
            count = OrderItem.objects.filter(status=status).count()
            if count > 0:
                status_counts[status] = count

        if status_counts:
            for status, count in status_counts.items():
                emoji = {
                    "pending": "⏳",
                    "assigned": "📋",
                    "processing": "⚙️",
                    "completed": "✅",
                    "failed": "❌",
                    "stalled": "🚨",
                    "cancelled": "🚫",
                }.get(status, "🔸")

                self.stdout.write(f"  {emoji} {status}: {count}")
        else:
            self.stdout.write("  📭 No work items in queue")

        # Show recent activity
        recent_items = OrderItem.objects.exclude(status="pending").order_by("-updated_at")[:5]

        if recent_items.exists():
            self.stdout.write(f"\n🕒 Recent Activity:")
            for item in recent_items:
                age = timezone.now() - item.updated_at
                status_emoji = {"assigned": "📋", "processing": "⚙️", "completed": "✅", "failed": "❌", "stalled": "🚨"}.get(
                    item.status, "🔸"
                )

                worker_info = f" (Worker: {item.assigned_worker.name})" if item.assigned_worker else ""

                self.stdout.write(f"  {status_emoji} Item {item.id}: {item.status}{worker_info} - {age} ago")

        # Show recommendations
        self.stdout.write(f"\n💡 System Health:")

        pending_count = status_counts.get("pending", 0)
        active_workers = workers.count()
        stalled_workers = [w for w in workers if w.is_stalled()]

        if pending_count > 0 and active_workers == 0:
            self.stdout.write("  ⚠️  Pending work but no active workers - consider spawning worker")
            self.stdout.write("      Run: python manage.py run_worker")

        if stalled_workers:
            self.stdout.write(f"  🚨 {len(stalled_workers)} stalled workers detected")
            self.stdout.write("      Foreman should clean these up automatically")

        if pending_count == 0 and active_workers == 0:
            self.stdout.write("  ✅ System is idle - no work or workers")

        if pending_count > 0 and active_workers > 0:
            self.stdout.write(f"  ⚙️  System is active - {active_workers} workers processing {pending_count} items")
