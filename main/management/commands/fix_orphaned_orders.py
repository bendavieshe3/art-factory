"""
Management command to fix orphaned orders that have no OrderItems.
"""
from django.core.management.base import BaseCommand
from django.utils import timezone

from main.models import Order, OrderItem, FactoryMachineDefinition


class Command(BaseCommand):
    help = 'Fix orphaned orders by creating missing OrderItems'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.HTTP_INFO("Fixing Orphaned Orders")
        )
        self.stdout.write("=" * 50)
        
        # Find orders with no items
        orphaned_orders = []
        for order in Order.objects.filter(status='pending'):
            item_count = OrderItem.objects.filter(order=order).count()
            if item_count == 0 and order.quantity > 0:
                orphaned_orders.append(order)
        
        if not orphaned_orders:
            self.stdout.write(
                self.style.SUCCESS("✅ No orphaned orders found")
            )
            return
        
        self.stdout.write(
            f"\n🔍 Found {len(orphaned_orders)} orphaned orders"
        )
        
        for order in orphaned_orders:
            self.stdout.write(
                f"\n📋 Order {order.id}: {order.title}"
            )
            self.stdout.write(f"   Provider: {order.provider}")
            self.stdout.write(f"   Machine: {order.factory_machine_name}")
            self.stdout.write(f"   Quantity: {order.quantity}")
            self.stdout.write(f"   Created: {order.created_at}")
            
            if not dry_run:
                # Get machine definition
                try:
                    machine_def = FactoryMachineDefinition.objects.get(
                        name=order.factory_machine_name
                    )
                    
                    # Merge parameters
                    merged_params = {}
                    if machine_def.default_parameters:
                        merged_params.update(machine_def.default_parameters)
                    if order.base_parameters:
                        merged_params.update(order.base_parameters)
                    
                    # Create missing OrderItems
                    created_items = []
                    for i in range(order.quantity):
                        item = OrderItem.objects.create(
                            order=order,
                            prompt=order.prompt,
                            parameters=merged_params,
                            status='pending'
                        )
                        created_items.append(item)
                    
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"   ✅ Created {len(created_items)} OrderItems"
                        )
                    )
                    
                    # Update order status if it's still pending
                    if order.status == 'pending' and created_items:
                        order.status = 'processing'
                        order.save()
                        self.stdout.write(
                            "   📊 Updated order status to processing"
                        )
                    
                except FactoryMachineDefinition.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(
                            f"   ❌ Machine definition not found: {order.factory_machine_name}"
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"   ❌ Error creating items: {e}"
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f"   🔸 Would create {order.quantity} OrderItems (dry run)"
                    )
                )
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  Dry run complete - no changes made"
                )
            )
            self.stdout.write(
                "Run without --dry-run to fix these orders"
            )