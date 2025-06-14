from django.db import models
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver


class Project(models.Model):
    """
    Represents a project for organizing orders and products by theme or purpose.
    Core organizational feature for managing collections of products.
    """

    name = models.CharField(max_length=200, help_text="Project name")
    description = models.TextField(blank=True, help_text="Project description")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    STATUS_CHOICES = [("active", "Active"), ("archived", "Archived"), ("completed", "Completed")]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="active")

    # For hero display
    featured_products = models.ManyToManyField(
        "Product",
        blank=True,
        related_name="featured_in_projects",
        help_text="Featured products to display on project overview",
    )

    # Denormalized fields for performance
    product_count = models.PositiveIntegerField(default=0, help_text="Total number of products in this project")
    order_count = models.PositiveIntegerField(default=0, help_text="Total number of orders in this project")

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["-updated_at"]),
        ]

    def __str__(self):
        return self.name

    def get_products_queryset(self):
        """Get a queryset of all products from this project."""
        from .products import Product

        order_ids = self.order_set.values_list("id", flat=True)
        return Product.objects.filter(order_item__order__id__in=order_ids)

    def get_recent_products(self, limit=4):
        """Get recent products from this project for display."""
        return self.get_products_queryset().order_by("-created_at")[:limit]

    @property
    def recent_products_for_display(self):
        """Get recent products for template display (4 items)."""
        return self.get_recent_products(4)

    @property
    def recent_products_preview(self):
        """Get recent products for preview display (3 items)."""
        return self.get_recent_products(3)

    def update_counts(self):
        """Update denormalized count fields."""
        self.order_count = self.order_set.count()
        self.product_count = self.get_products_queryset().count()
        self.save(update_fields=["order_count", "product_count"])


# Signals to maintain denormalized counts
@receiver([post_save, post_delete], sender="main.Order")
def update_project_counts_on_order_change(sender, instance, **kwargs):
    """Update project counts when orders are created/deleted."""
    if instance.project:
        instance.project.update_counts()


@receiver([post_save, post_delete], sender="main.Product")
def update_project_counts_on_product_change(sender, instance, **kwargs):
    """Update project counts when products are created/deleted."""
    if hasattr(instance, "order_item") and instance.order_item and instance.order_item.order.project:
        instance.order_item.order.project.update_counts()
