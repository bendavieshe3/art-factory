from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from .products import Product


class Order(models.Model):
    """
    Represents a user request for generating products.
    Contains base parameters and production line specification.
    """
    
    # Order identification
    title = models.CharField(max_length=200, blank=True, help_text="Optional order title")
    description = models.TextField(blank=True, help_text="Order description or notes")
    
    # Generation request details
    prompt = models.TextField(help_text="Base prompt for generation")
    base_parameters = models.JSONField(default=dict, help_text="Base parameters for all items")
    
    # Factory specification
    factory_machine_name = models.CharField(max_length=100, help_text="e.g., 'fal.ai/flux/dev'")
    provider = models.CharField(max_length=50, help_text="e.g., 'fal.ai', 'replicate'")
    
    # Order status
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Batch generation settings
    quantity = models.PositiveIntegerField(default=1, help_text="Number of products to generate")
    expand_parameters = models.BooleanField(default=False, help_text="Whether to expand smart tokens")
    
    # Organization
    project_name = models.CharField(max_length=100, blank=True, help_text="Project organization")
    tags = models.JSONField(default=list, help_text="List of tags")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['provider']),
            models.Index(fields=['project_name']),
        ]
    
    def __str__(self):
        return f"Order {self.id}: {self.title or self.prompt[:50]}... ({self.status})"
    
    @property
    def completion_percentage(self):
        """Calculate completion percentage based on order items."""
        items = self.orderitem_set.all()
        if not items:
            return 0
        completed_items = items.filter(status='completed').count()
        return int((completed_items / items.count()) * 100)


class OrderItem(models.Model):
    """
    Individual product creation task derived from an order.
    Each item represents one product to be generated.
    """
    
    # Relationship to order
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    
    # Item-specific parameters
    prompt = models.TextField(help_text="Processed prompt for this specific item")
    parameters = models.JSONField(default=dict, help_text="Final parameters for generation")
    variation_seed = models.BigIntegerField(null=True, blank=True, help_text="Variation seed")
    
    # Generation tracking
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('queued', 'Queued'),
        ('processing', 'Processing'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Provider tracking
    provider_request_id = models.CharField(max_length=200, blank=True, help_text="Provider's request ID")
    error_message = models.TextField(blank=True, help_text="Error details if failed")
    
    # Result
    product = models.ForeignKey(Product, on_delete=models.CASCADE, null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['order', 'status']),
            models.Index(fields=['provider_request_id']),
        ]
    
    def __str__(self):
        return f"Item {self.id} for Order {self.order.id} ({self.status})"
    
    @property
    def processing_duration(self):
        """Calculate how long this item has been/was processing."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            from django.utils import timezone
            return timezone.now() - self.started_at
        return None


@receiver(post_save, sender=OrderItem)
def trigger_order_item_processing(sender, instance, created, **kwargs):
    """
    Automatically trigger processing when OrderItem is created.
    This ensures AI generation happens immediately without manual intervention.
    """
    if created and instance.status == 'pending':
        # Import here to avoid circular imports
        from ..tasks import process_order_items_async
        import threading
        import logging
        
        logger = logging.getLogger(__name__)
        logger.info(f"Auto-triggering processing for OrderItem {instance.id}")
        
        try:
            # Process in background thread
            thread = threading.Thread(
                target=process_order_items_async,
                args=([instance],)
            )
            thread.daemon = True
            thread.start()
        except Exception as e:
            logger.error(f"Failed to trigger background processing for OrderItem {instance.id}: {e}")
            # Don't raise the exception - we don't want to break order creation