from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

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
    negative_prompt = models.TextField(blank=True, default="", help_text="What to avoid in the generated image")
    base_parameters = models.JSONField(default=dict, help_text="Base parameters for all items")

    # Factory specification
    factory_machine_name = models.CharField(max_length=100, help_text="e.g., 'fal.ai/flux/dev'")
    provider = models.CharField(max_length=50, help_text="e.g., 'fal.ai', 'replicate'")

    # Order status
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("partially_completed", "Partially Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Batch generation settings
    quantity = models.PositiveIntegerField(default=1, help_text="Number of products to generate")
    expand_parameters = models.BooleanField(default=False, help_text="Whether to expand smart tokens")

    # Organization
    project = models.ForeignKey("Project", on_delete=models.SET_NULL, null=True, blank=True, help_text="Associated project")
    project_name = models.CharField(max_length=100, blank=True, help_text="Legacy project name field")
    tags = models.JSONField(default=list, help_text="List of tags")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["provider"]),
            models.Index(fields=["project"]),
            models.Index(fields=["project_name"]),
        ]

    def __str__(self):
        return f"Order {self.id}: {self.title or self.prompt[:50]}... ({self.status})"

    @property
    def completion_percentage(self):
        """Calculate completion percentage based on order items."""
        items = self.orderitem_set.all()
        if not items:
            return 0
        completed_items = items.filter(status="completed").count()
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
    negative_prompt = models.TextField(blank=True, default="", help_text="What to avoid in the generated image")
    parameters = models.JSONField(default=dict, help_text="Final parameters for generation")
    variation_seed = models.BigIntegerField(null=True, blank=True, help_text="Variation seed")

    # Generation tracking
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("assigned", "Assigned to Worker"),
        ("queued", "Queued"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("exhausted", "Failed - Max Retries Exhausted"),
        ("stalled", "Stalled - Manual Retry Required"),
        ("cancelled", "Cancelled"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Provider tracking
    provider_request_id = models.CharField(max_length=200, blank=True, help_text="Provider's request ID")
    error_message = models.TextField(blank=True, help_text="User-friendly error message")
    error_category = models.CharField(max_length=50, blank=True, help_text="Error category for retry logic")

    # Retry tracking
    retry_count = models.PositiveIntegerField(default=0, help_text="Number of retry attempts")
    max_retries = models.PositiveIntegerField(default=3, help_text="Maximum retry attempts for transient failures")
    last_retry_at = models.DateTimeField(null=True, blank=True, help_text="Timestamp of last retry attempt")

    # Worker assignment
    assigned_worker = models.ForeignKey("Worker", on_delete=models.SET_NULL, null=True, blank=True)

    # Result - Changed to support multiple products per OrderItem for batch generation
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True, blank=True)

    # Batch generation fields
    total_quantity = models.PositiveIntegerField(default=1, help_text="Total number of products to generate")
    batch_size = models.PositiveIntegerField(default=1, help_text="Number of products per API call")
    batches_completed = models.PositiveIntegerField(default=0, help_text="Number of completed batches")

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["order", "created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["order", "status"]),
            models.Index(fields=["provider_request_id"]),
        ]

    def __str__(self):
        return f"Item {self.id} for Order {self.order.id} ({self.status})"

    def can_be_assigned(self):
        """Check if this order item can be assigned to a worker."""
        return self.status == "pending" and not self.assigned_worker

    def can_be_retried(self):
        """Check if this order item can be retried after failure."""
        return self.status == "failed" and self.retry_count < self.max_retries and self.is_transient_failure()

    def is_transient_failure(self):
        """Determine if the failure is transient and worth retrying."""
        # Use error category if available (new error handling system)
        if self.error_category:
            from ..error_handling import ErrorCategory

            retryable_categories = [
                ErrorCategory.TRANSIENT,
                ErrorCategory.RATE_LIMITED,
                ErrorCategory.PROVIDER_OUTAGE,
                ErrorCategory.NETWORK,
                ErrorCategory.FILE_SYSTEM,
            ]
            return self.error_category in retryable_categories

        # Fallback to legacy pattern matching for backward compatibility
        if not self.error_message:
            return False

        transient_patterns = [
            "Server disconnected without sending a response",
            "Connection timeout",
            "Network is unreachable",
            "Connection reset by peer",
            "Temporary failure",
            "Service unavailable",
            "Rate limit exceeded",
            "Internal server error",
            "502 Bad Gateway",
            "503 Service Unavailable",
            "504 Gateway Timeout",
        ]

        error_lower = self.error_message.lower()
        return any(pattern.lower() in error_lower for pattern in transient_patterns)

    def reset_for_retry(self):
        """Reset order item for retry attempt."""
        self.status = "pending"
        self.assigned_worker = None
        self.retry_count += 1
        self.last_retry_at = timezone.now()
        self.provider_request_id = ""
        # Keep error_message for tracking but clear other fields
        self.save()

    @property
    def processing_duration(self):
        """Calculate how long this item has been/was processing."""
        if self.started_at and self.completed_at:
            return self.completed_at - self.started_at
        elif self.started_at:
            from django.utils import timezone

            return timezone.now() - self.started_at
        return None


class Worker(models.Model):
    """
    Represents an active worker process for processing OrderItems.
    Workers are autonomous and self-managing.
    """

    # Worker identification
    name = models.CharField(max_length=100, help_text="Unique worker name")
    process_id = models.IntegerField(unique=True, help_text="OS process ID")

    # Worker status
    STATUS_CHOICES = [
        ("starting", "Starting"),
        ("working", "Working"),
        ("exiting", "Exiting"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="starting")

    # Processing capabilities
    provider = models.CharField(max_length=50, help_text="Provider this worker handles (fal.ai, replicate)")
    max_batch_size = models.IntegerField(default=5, help_text="Maximum items to process in one batch")

    # Monitoring and metrics
    spawned_at = models.DateTimeField(auto_now_add=True)
    last_heartbeat = models.DateTimeField(auto_now=True)
    items_processed = models.IntegerField(default=0)
    items_failed = models.IntegerField(default=0)

    # Additional context
    extra_data = models.JSONField(default=dict, help_text="Additional worker context")

    class Meta:
        ordering = ["-spawned_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["provider"]),
            models.Index(fields=["process_id"]),
            models.Index(fields=["last_heartbeat"]),
        ]

    def __str__(self):
        return f"Worker {self.name} (PID: {self.process_id})"

    def update_heartbeat(self):
        """Update heartbeat timestamp to indicate worker is alive."""
        self.last_heartbeat = timezone.now()
        self.save(update_fields=["last_heartbeat"])

    def is_stalled(self, threshold_minutes=3):
        """Check if worker hasn't updated heartbeat within threshold."""
        from datetime import timedelta

        from django.utils import timezone

        cutoff = timezone.now() - timedelta(minutes=threshold_minutes)
        return self.last_heartbeat < cutoff


@receiver(post_save, sender=OrderItem)
def trigger_worker_spawn_on_order_creation(sender, instance, created, **kwargs):
    """
    Automatically spawn worker when OrderItem is created.
    This ensures immediate responsiveness for user orders.
    """
    # Check if auto-spawning is disabled (e.g., during tests)
    from django.conf import settings

    if getattr(settings, "DISABLE_AUTO_WORKER_SPAWN", False):
        return

    if created and instance.status == "pending":
        # Import here to avoid circular imports
        import logging

        from ..workers import spawn_worker_automatically

        logger = logging.getLogger(__name__)
        logger.info(f"Auto-spawning worker for OrderItem {instance.id}")

        try:
            # Spawn worker automatically for immediate processing
            spawn_worker_automatically()
        except Exception as e:
            logger.error(f"Failed to spawn worker for OrderItem {instance.id}: {e}")
            # Don't raise the exception - we don't want to break order creation
