"""
Background task processing for AI generation.
Handles automatic order processing without requiring manual commands.
"""
import logging
from django.utils import timezone
from .management.commands.simple_process import Command as SimpleProcessCommand

logger = logging.getLogger(__name__)


def process_order_items_async(order_items):
    """
    Process a list of order items in the background.
    This function runs in a separate thread to avoid blocking the web request.
    """
    try:
        logger.info(f"Starting background processing of {len(order_items)} order items")
        
        # Create an instance of our existing processing command
        processor = SimpleProcessCommand()
        
        # Process each order item
        for item in order_items:
            try:
                logger.info(f"Processing order item {item.id}")
                
                # Update status to processing
                item.status = 'processing'
                item.started_at = timezone.now()
                item.save()
                
                # Get machine info
                machine_name = item.order.factory_machine_name
                provider = item.order.provider
                
                if provider == 'fal.ai':
                    result = processor.process_fal_item(item, machine_name)
                elif provider == 'replicate':
                    result = processor.process_replicate_item(item, machine_name)
                else:
                    raise ValueError(f"Unknown provider: {provider}")
                
                if result:
                    item.status = 'completed'
                    item.product = result
                    logger.info(f"✅ Completed order item {item.id}")
                else:
                    item.status = 'failed'
                    item.error_message = 'Generation failed'
                    logger.error(f"❌ Failed order item {item.id}")
                
                item.completed_at = timezone.now()
                item.save()
                
                # Update order status
                processor.update_order_status(item.order)
                
            except Exception as e:
                item.status = 'failed'
                item.error_message = str(e)
                item.completed_at = timezone.now()
                item.save()
                processor.update_order_status(item.order)
                logger.error(f"❌ Error processing order item {item.id}: {e}")
        
        logger.info(f"Completed background processing of {len(order_items)} order items")
        
    except Exception as e:
        logger.error(f"Error in background processing: {e}")


def process_single_order_item(order_item_id):
    """
    Process a single order item by ID.
    Useful for retry mechanisms or individual processing.
    """
    try:
        from .models import OrderItem
        order_item = OrderItem.objects.get(id=order_item_id)
        process_order_items_async([order_item])
    except Exception as e:
        logger.error(f"Error processing single order item {order_item_id}: {e}")


def process_all_pending_orders():
    """
    Process all pending orders in the system.
    Can be called periodically or on demand.
    """
    try:
        from .models import OrderItem
        pending_items = list(OrderItem.objects.filter(status='pending'))
        
        if pending_items:
            logger.info(f"Processing {len(pending_items)} pending order items")
            process_order_items_async(pending_items)
        else:
            logger.info("No pending order items to process")
            
    except Exception as e:
        logger.error(f"Error processing all pending orders: {e}")


# Optional: Function to be called by external schedulers or cron jobs
def scheduled_order_processing():
    """
    Entry point for scheduled/cron-based order processing.
    This ensures orders are processed even if background threads fail.
    """
    logger.info("Running scheduled order processing check")
    process_all_pending_orders()