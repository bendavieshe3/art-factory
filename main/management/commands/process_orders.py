import asyncio
from django.core.management.base import BaseCommand
from main.factory_machines import process_pending_orders_sync, execute_order_item_sync
from main.models import OrderItem


class Command(BaseCommand):
    help = 'Process pending order items and execute AI generation'

    def add_arguments(self, parser):
        parser.add_argument(
            '--order-item-id',
            type=int,
            help='Process a specific order item by ID',
        )
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Run continuously, processing orders as they come in',
        )

    def handle(self, *args, **options):
        if options['order_item_id']:
            # Process specific order item
            self.stdout.write(f'Processing order item {options["order_item_id"]}...')
            result = execute_order_item_sync(options['order_item_id'])
            
            if result.success:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Order item {options["order_item_id"]} completed successfully')
                )
                if result.product:
                    self.stdout.write(f'   Product created: {result.product.id}')
            else:
                self.stdout.write(
                    self.style.ERROR(f'❌ Order item {options["order_item_id"]} failed: {result.error}')
                )
        
        elif options['continuous']:
            # Continuous processing mode
            self.stdout.write('Starting continuous order processing...')
            self.stdout.write('Press Ctrl+C to stop')
            
            try:
                while True:
                    pending_count = OrderItem.objects.filter(status='pending').count()
                    if pending_count > 0:
                        self.stdout.write(f'Processing {pending_count} pending orders...')
                        process_pending_orders_sync()
                    
                    # Wait before checking again
                    import time
                    time.sleep(5)
                    
            except KeyboardInterrupt:
                self.stdout.write('\n' + self.style.SUCCESS('Order processing stopped'))
        
        else:
            # Process all pending orders once
            pending_count = OrderItem.objects.filter(status='pending').count()
            
            if pending_count == 0:
                self.stdout.write(self.style.SUCCESS('No pending orders to process'))
                return
            
            self.stdout.write(f'Processing {pending_count} pending order items...')
            
            try:
                process_pending_orders_sync()
                
                # Show results
                completed = OrderItem.objects.filter(status='completed').count()
                failed = OrderItem.objects.filter(status='failed').count()
                still_pending = OrderItem.objects.filter(status='pending').count()
                
                self.stdout.write('\nProcessing Results:')
                self.stdout.write(f'  ✅ Completed: {completed}')
                self.stdout.write(f'  ❌ Failed: {failed}')
                self.stdout.write(f'  ⏳ Still Pending: {still_pending}')
                
                if failed > 0:
                    self.stdout.write('\nFailed Orders:')
                    for item in OrderItem.objects.filter(status='failed'):
                        self.stdout.write(f'  Order Item {item.id}: {item.error_message}')
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error processing orders: {e}')
                )