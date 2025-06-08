import json

from django.core.exceptions import ValidationError
from django.db import models


class FactoryMachineDefinition(models.Model):
    """
    Stores metadata about different types of factory machines.
    Defines the available AI models and their capabilities.
    """

    # Machine identification
    name = models.CharField(max_length=100, unique=True, help_text="e.g., 'fal.ai/flux/dev'")
    display_name = models.CharField(max_length=150, help_text="Human-readable name")
    description = models.TextField(help_text="Description of what this machine does")

    # Provider information
    provider = models.CharField(max_length=50, help_text="e.g., 'fal.ai', 'replicate'")
    model_family = models.CharField(max_length=50, help_text="e.g., 'flux', 'sdxl', 'stable-diffusion'")

    # Capabilities
    MODALITY_CHOICES = [
        ("text-to-image", "Text to Image"),
        ("image-to-image", "Image to Image"),
        ("text-to-video", "Text to Video"),
        ("text-to-audio", "Text to Audio"),
        ("image-to-video", "Image to Video"),
    ]
    modality = models.CharField(max_length=20, choices=MODALITY_CHOICES)

    # Parameter specification
    parameter_schema = models.JSONField(default=dict, help_text="JSON schema defining available parameters")
    default_parameters = models.JSONField(default=dict, help_text="Default parameter values")

    # Operational settings
    is_active = models.BooleanField(default=True, help_text="Whether this machine is available")
    max_concurrent_jobs = models.PositiveIntegerField(default=1, help_text="Max simultaneous operations")
    estimated_duration = models.DurationField(null=True, blank=True, help_text="Typical processing time")

    # Cost information
    cost_per_operation = models.DecimalField(
        max_digits=10, decimal_places=4, null=True, blank=True, help_text="Estimated cost per generation"
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["provider", "model_family", "name"]
        indexes = [
            models.Index(fields=["provider"]),
            models.Index(fields=["modality"]),
            models.Index(fields=["is_active"]),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.provider})"

    def clean(self):
        """Validate parameter schema is valid JSON."""
        if self.parameter_schema:
            try:
                if isinstance(self.parameter_schema, str):
                    json.loads(self.parameter_schema)
            except json.JSONDecodeError:
                raise ValidationError("Parameter schema must be valid JSON")


class FactoryMachineInstance(models.Model):
    """
    Represents active instances of factory machines and their current status.
    Tracks the operational state of machines.
    """

    # Machine reference
    machine_definition = models.ForeignKey(FactoryMachineDefinition, on_delete=models.CASCADE)

    # Instance identification
    instance_id = models.CharField(max_length=100, unique=True, help_text="Unique instance identifier")

    # Current status
    STATUS_CHOICES = [
        ("idle", "Idle"),
        ("busy", "Busy"),
        ("error", "Error"),
        ("maintenance", "Maintenance"),
        ("offline", "Offline"),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="idle")

    # Current operation
    current_operation = models.JSONField(null=True, blank=True, help_text="Details of current operation if busy")
    current_order_item = models.ForeignKey(
        "OrderItem", on_delete=models.SET_NULL, null=True, blank=True, help_text="Currently processing order item"
    )

    # Performance metrics
    total_operations = models.PositiveIntegerField(default=0)
    successful_operations = models.PositiveIntegerField(default=0)
    failed_operations = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_operation_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["machine_definition", "instance_id"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["machine_definition", "status"]),
        ]

    def __str__(self):
        return f"{self.machine_definition.display_name} Instance {self.instance_id} ({self.status})"

    @property
    def success_rate(self):
        """Calculate success rate percentage."""
        if self.total_operations == 0:
            return 0
        return (self.successful_operations / self.total_operations) * 100

    @property
    def is_available(self):
        """Check if this instance is available for new operations."""
        return self.status == "idle" and self.machine_definition.is_active


class LogEntry(models.Model):
    """
    Stores application logs for monitoring and debugging purposes.
    Provides centralized logging for the factory system.
    """

    # Log level
    LEVEL_CHOICES = [
        ("DEBUG", "Debug"),
        ("INFO", "Info"),
        ("WARNING", "Warning"),
        ("ERROR", "Error"),
        ("CRITICAL", "Critical"),
    ]
    level = models.CharField(max_length=10, choices=LEVEL_CHOICES)

    # Log content
    message = models.TextField()
    logger_name = models.CharField(max_length=100, help_text="Name of the logger")

    # Context information
    module = models.CharField(max_length=100, blank=True, help_text="Python module name")
    function = models.CharField(max_length=100, blank=True, help_text="Function name")
    line_number = models.PositiveIntegerField(null=True, blank=True)

    # Related objects
    order = models.ForeignKey("Order", on_delete=models.CASCADE, null=True, blank=True)
    order_item = models.ForeignKey("OrderItem", on_delete=models.CASCADE, null=True, blank=True)
    machine_instance = models.ForeignKey(FactoryMachineInstance, on_delete=models.CASCADE, null=True, blank=True)

    # Additional data
    extra_data = models.JSONField(default=dict, help_text="Additional log context")

    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["level"]),
            models.Index(fields=["timestamp"]),
            models.Index(fields=["logger_name"]),
        ]

    def __str__(self):
        return f"[{self.level}] {self.message[:100]}... ({self.timestamp.strftime('%Y-%m-%d %H:%M:%S')})"
