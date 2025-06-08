"""
Management command to monitor order processing and show current status.
Useful for debugging and monitoring production system health.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta

from main.models import Order, OrderItem, LogEntry


class Command(BaseCommand):
    help = "Monitor current order processing status and system health"

    def add_arguments(self, parser):
        parser.add_argument("--details", action="store_true", help="Show detailed information about each order")
        parser.add_argument("--pending-only", action="store_true", help="Only show pending/stuck orders")
        parser.add_argument("--recent-hours", type=int, default=24, help="Show orders from the last N hours (default: 24)")

    def handle(self, *args, **options):
        show_details = options["details"]
        pending_only = options["pending_only"]
        recent_hours = options["recent_hours"]

        # Calculate time window
        since_time = timezone.now() - timedelta(hours=recent_hours)

        self.stdout.write(self.style.HTTP_INFO(f"Order Processing Status (last {recent_hours} hours)"))
        self.stdout.write("=" * 60)

        # Get orders in time window
        if pending_only:
            orders = (
                Order.objects.filter(created_at__gte=since_time, orderitem__status__in=["pending", "processing"])
                .distinct()
                .order_by("-created_at")
            )
        else:
            orders = Order.objects.filter(created_at__gte=since_time).order_by("-created_at")

        if not orders:
            self.stdout.write("No orders found in the specified time window")
            return

        # Summary statistics
        total_orders = orders.count()
        total_items = OrderItem.objects.filter(order__in=orders).count()

        # Status counts
        status_counts = {}
        for status_choice in OrderItem.STATUS_CHOICES:
            status = status_choice[0]
            count = OrderItem.objects.filter(order__in=orders, status=status).count()
            status_counts[status] = count

        self.stdout.write("📊 Summary:")
        self.stdout.write(f"  Total Orders: {total_orders}")
        self.stdout.write(f"  Total Order Items: {total_items}")
        self.stdout.write("  Status Breakdown:")
        for status, count in status_counts.items():
            if count > 0:
                emoji = {
                    "pending": "⏳",
                    "queued": "📋",
                    "processing": "⚙️",
                    "completed": "✅",
                    "failed": "❌",
                    "cancelled": "🚫",
                }.get(status, "🔸")
                self.stdout.write(f"    {emoji} {status}: {count}")

        # Show problematic orders
        pending_items = OrderItem.objects.filter(order__in=orders, status="pending")
        failed_items = OrderItem.objects.filter(order__in=orders, status="failed")

        if pending_items.exists():
            self.stdout.write(f"\n⚠️  Pending Orders ({pending_items.count()}):")
            for item in pending_items.order_by("created_at"):
                age = timezone.now() - item.created_at
                self.stdout.write(
                    f"  - Item {item.id} (Order {item.order.id}): " f"pending for {age} - {item.order.factory_machine_name}"
                )

        if failed_items.exists():
            self.stdout.write(f"\n❌ Failed Orders ({failed_items.count()}):")
            for item in failed_items.order_by("-updated_at")[:5]:  # Show last 5 failures
                self.stdout.write(f"  - Item {item.id} (Order {item.order.id}): " f"{item.error_message[:100]}...")

        # Show detailed order information if requested
        if show_details:
            self.stdout.write("\n📋 Detailed Order Information:")
            for order in orders[:10]:  # Limit to 10 most recent
                items = OrderItem.objects.filter(order=order)
                self.stdout.write(f"\nOrder {order.id}: {order.title or '(no title)'}")
                self.stdout.write(f"  Created: {order.created_at}")
                self.stdout.write(f"  Machine: {order.factory_machine_name}")
                self.stdout.write(f"  Items: {items.count()}")

                for item in items:
                    status_emoji = {"pending": "⏳", "processing": "⚙️", "completed": "✅", "failed": "❌"}.get(
                        item.status, "🔸"
                    )

                    duration_info = ""
                    if item.processing_duration:
                        duration_info = f" ({item.processing_duration})"

                    self.stdout.write(f"    {status_emoji} Item {item.id}: {item.status}{duration_info}")

                    if item.status == "failed" and item.error_message:
                        self.stdout.write(f"      Error: {item.error_message[:100]}...")

        # Show recent log activity
        recent_logs = LogEntry.objects.filter(
            timestamp__gte=since_time, extra_data__event_type__in=["processing_started", "item_completed", "item_failed"]
        ).order_by("-timestamp")[:5]

        if recent_logs.exists():
            self.stdout.write("\n📝 Recent Processing Activity:")
            for log in recent_logs:
                event_type = log.extra_data.get("event_type", "unknown")
                emoji = {"processing_started": "🚀", "item_completed": "✅", "item_failed": "❌"}.get(event_type, "📝")

                self.stdout.write(f"  {emoji} {log.timestamp.strftime('%H:%M:%S')}: {log.message}")

        # Recommendations
        self.stdout.write("\n💡 Recommendations:")

        if status_counts.get("pending", 0) > 0:
            self.stdout.write("  - Run 'python manage.py process_pending_orders' to retry stuck orders")

        if status_counts.get("failed", 0) > 0:
            self.stdout.write("  - Run 'python manage.py process_pending_orders --retry-failed' to retry failed orders")

        if status_counts.get("completed", 0) > 0:
            self.stdout.write(f"  - Check /inventory/ to view {status_counts['completed']} generated products")
