"""
Debug command to investigate order failures and system status.
"""

from django.core.management.base import BaseCommand
from main.models import Order, Product, LogEntry, FactoryMachineDefinition


class Command(BaseCommand):
    help = "Debug orders and investigate failures"

    def add_arguments(self, parser):
        parser.add_argument(
            "--order-id",
            type=int,
            help="Specific order ID to debug",
        )
        parser.add_argument(
            "--recent",
            type=int,
            default=5,
            help="Number of recent orders to check (default: 5)",
        )
        parser.add_argument(
            "--failed-only",
            action="store_true",
            help="Show only failed orders",
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("🔍 Art Factory Debug Tool"))
        self.stdout.write("=" * 50)

        if options["order_id"]:
            self.debug_specific_order(options["order_id"])
        else:
            self.debug_recent_orders(options["recent"], options["failed_only"])

        self.show_system_status()

    def debug_specific_order(self, order_id):
        """Debug a specific order."""
        try:
            order = Order.objects.get(id=order_id)
            self.stdout.write(f"\n📋 ORDER {order_id} DETAILS")
            self.stdout.write("-" * 30)

            self.stdout.write(f"Title: {order.title or '(No title)'}")
            self.stdout.write(f"Status: {self.colorize_status(order.status)}")
            self.stdout.write(f"Provider: {order.provider}")
            self.stdout.write(f"Machine: {order.factory_machine_name}")
            self.stdout.write(f"Prompt: {order.prompt[:100]}...")
            self.stdout.write(f"Quantity: {order.quantity}")
            self.stdout.write(f"Created: {order.created_at}")

            if order.completed_at:
                duration = order.completed_at - order.created_at
                self.stdout.write(f"Duration: {duration}")

            # Show order items
            items = order.orderitem_set.all()
            self.stdout.write(f"\n📦 ORDER ITEMS ({items.count()})")
            for item in items:
                self.stdout.write(f"  Item {item.id}: {self.colorize_status(item.status)}")
                if item.error_message:
                    self.stdout.write(f"    ❌ Error: {item.error_message}")
                if item.product:
                    self.stdout.write(f"    ✅ Product: {item.product.file_path}")
                if item.started_at and item.completed_at:
                    duration = item.completed_at - item.started_at
                    self.stdout.write(f"    ⏱️  Processing time: {duration}")

        except Order.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ Order {order_id} not found"))

    def debug_recent_orders(self, count, failed_only):
        """Debug recent orders."""
        self.stdout.write(f"\n📊 RECENT ORDERS (last {count})")
        self.stdout.write("-" * 30)

        orders = Order.objects.all().order_by("-created_at")[:count]
        if failed_only:
            orders = Order.objects.filter(status="failed").order_by("-created_at")[:count]

        for order in orders:
            items_status = []
            for item in order.orderitem_set.all():
                items_status.append(item.status)

            self.stdout.write(
                f"Order {order.id}: {self.colorize_status(order.status)} "
                f"({order.provider}) - {order.created_at.strftime('%m/%d %H:%M')}"
            )
            if order.status == "failed":
                # Show error details for failed orders
                failed_items = order.orderitem_set.filter(status="failed")
                for item in failed_items:
                    if item.error_message:
                        self.stdout.write(f"  ❌ {item.error_message[:100]}...")

    def show_system_status(self):
        """Show overall system status."""
        self.stdout.write("\n🏭 SYSTEM STATUS")
        self.stdout.write("-" * 30)

        # Order statistics
        total_orders = Order.objects.count()
        pending_orders = Order.objects.filter(status="pending").count()
        processing_orders = Order.objects.filter(status="processing").count()
        completed_orders = Order.objects.filter(status="completed").count()
        failed_orders = Order.objects.filter(status="failed").count()

        self.stdout.write(f"📈 Orders: {total_orders} total")
        self.stdout.write(f"  ⏳ Pending: {pending_orders}")
        self.stdout.write(f"  ⚙️  Processing: {processing_orders}")
        self.stdout.write(f"  ✅ Completed: {completed_orders}")
        self.stdout.write(f"  ❌ Failed: {failed_orders}")

        # Product statistics
        total_products = Product.objects.count()
        self.stdout.write(f"🖼️  Products generated: {total_products}")

        # Factory machines
        self.stdout.write("\n🤖 FACTORY MACHINES")
        active_machines = FactoryMachineDefinition.objects.filter(is_active=True)
        inactive_machines = FactoryMachineDefinition.objects.filter(is_active=False)

        for machine in active_machines:
            self.stdout.write(f"  ✅ {machine.display_name} ({machine.provider})")

        for machine in inactive_machines:
            self.stdout.write(f"  ❌ {machine.display_name} ({machine.provider}) - DISABLED")

        # Recent log entries
        self.stdout.write("\n📝 RECENT LOG ENTRIES")
        recent_logs = LogEntry.objects.all().order_by("-timestamp")[:5]
        if recent_logs:
            for log in recent_logs:
                level_color = self.style.ERROR if log.level == "ERROR" else self.style.WARNING
                self.stdout.write(f"  {log.timestamp.strftime('%m/%d %H:%M')} " f"{level_color(log.level)}: {log.message}")
        else:
            self.stdout.write("  (No log entries found)")

    def colorize_status(self, status):
        """Add color to status messages."""
        if status == "completed":
            return self.style.SUCCESS(status)
        elif status == "failed":
            return self.style.ERROR(status)
        elif status in ["pending", "processing"]:
            return self.style.WARNING(status)
        else:
            return status
