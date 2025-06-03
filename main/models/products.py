from django.db import models
from django.core.files.storage import default_storage
import os


class Product(models.Model):
    """
    Represents a generated media file (image, video, audio) with metadata.
    Core entity storing all generated products from AI providers.
    """
    
    # Product identification
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    
    # File information
    file_path = models.CharField(max_length=500)
    file_size = models.PositiveIntegerField(help_text="File size in bytes")
    file_format = models.CharField(max_length=20, help_text="e.g., 'jpg', 'png', 'mp4'")
    
    # Product type and dimensions
    PRODUCT_TYPES = [
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
    ]
    product_type = models.CharField(max_length=10, choices=PRODUCT_TYPES, default='image')
    width = models.PositiveIntegerField(null=True, blank=True)
    height = models.PositiveIntegerField(null=True, blank=True)
    duration = models.DurationField(null=True, blank=True, help_text="For video/audio")
    
    # Generation metadata
    prompt = models.TextField(help_text="The prompt used to generate this product")
    parameters = models.JSONField(default=dict, help_text="Full generation parameters as JSON")
    seed = models.BigIntegerField(null=True, blank=True, help_text="Random seed used")
    
    # Provider information
    provider = models.CharField(max_length=50, help_text="e.g., 'fal.ai', 'replicate'")
    model_name = models.CharField(max_length=100, help_text="e.g., 'flux/dev', 'sdxl'")
    provider_id = models.CharField(max_length=200, blank=True, help_text="Provider's internal ID")
    
    # Organization
    tags = models.JSONField(default=list, help_text="List of tags for organization")
    is_favorite = models.BooleanField(default=False)
    
    # Relationship to OrderItem (for batch generation support)
    order_item = models.ForeignKey('OrderItem', on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['created_at']),
            models.Index(fields=['product_type']),
            models.Index(fields=['provider']),
            models.Index(fields=['is_favorite']),
        ]
    
    def __str__(self):
        return f"{self.title or 'Product'} ({self.product_type}) - {self.created_at.strftime('%Y-%m-%d %H:%M')}"
    
    @property
    def file_url(self):
        """Return the URL to access this product's file."""
        if self.file_path and default_storage.exists(self.file_path):
            return default_storage.url(self.file_path)
        return None
    
    @property
    def file_name(self):
        """Extract filename from file_path."""
        return os.path.basename(self.file_path) if self.file_path else None
    
    def delete(self, *args, **kwargs):
        """Override delete to also remove the physical file."""
        if self.file_path and default_storage.exists(self.file_path):
            default_storage.delete(self.file_path)
        super().delete(*args, **kwargs)