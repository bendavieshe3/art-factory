from django.contrib import admin

from .models import FactoryMachineDefinition, FactoryMachineInstance, LogEntry, Order, OrderItem, Product


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["title", "product_type", "provider", "model_name", "is_favorite", "created_at"]
    list_filter = ["product_type", "provider", "is_favorite", "created_at"]
    search_fields = ["title", "prompt", "provider", "model_name"]
    readonly_fields = ["created_at", "updated_at", "file_url"]
    fieldsets = (
        ("Basic Information", {"fields": ("title", "description", "product_type", "is_favorite")}),
        ("File Information", {"fields": ("file_path", "file_url", "file_size", "file_format", "width", "height", "duration")}),
        ("Generation Details", {"fields": ("prompt", "parameters", "seed", "provider", "model_name", "provider_id")}),
        ("Organization", {"fields": ("tags",)}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "title", "status", "provider", "quantity", "completion_percentage", "created_at"]
    list_filter = ["status", "provider", "created_at"]
    search_fields = ["title", "prompt", "description"]
    readonly_fields = ["created_at", "updated_at", "completion_percentage"]
    fieldsets = (
        ("Basic Information", {"fields": ("title", "description", "status")}),
        ("Generation Request", {"fields": ("prompt", "base_parameters", "factory_machine_name", "provider")}),
        ("Batch Settings", {"fields": ("quantity", "expand_parameters")}),
        ("Organization", {"fields": ("project_name", "tags")}),
        (
            "Status",
            {"fields": ("completion_percentage", "created_at", "updated_at", "completed_at"), "classes": ("collapse",)},
        ),
    )


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["id", "order", "status", "provider_request_id", "product", "created_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["order__title", "prompt", "provider_request_id"]
    readonly_fields = ["created_at", "updated_at", "processing_duration"]
    raw_id_fields = ["order", "product"]


@admin.register(FactoryMachineDefinition)
class FactoryMachineDefinitionAdmin(admin.ModelAdmin):
    list_display = ["display_name", "provider", "modality", "is_active", "max_concurrent_jobs"]
    list_filter = ["provider", "modality", "is_active"]
    search_fields = ["name", "display_name", "description"]
    readonly_fields = ["created_at", "updated_at"]
    fieldsets = (
        ("Basic Information", {"fields": ("name", "display_name", "description", "is_active")}),
        ("Provider Details", {"fields": ("provider", "model_family", "modality")}),
        ("Parameters", {"fields": ("parameter_schema", "default_parameters")}),
        ("Operational Settings", {"fields": ("max_concurrent_jobs", "estimated_duration", "cost_per_operation")}),
        ("Timestamps", {"fields": ("created_at", "updated_at"), "classes": ("collapse",)}),
    )


@admin.register(FactoryMachineInstance)
class FactoryMachineInstanceAdmin(admin.ModelAdmin):
    list_display = ["instance_id", "machine_definition", "status", "success_rate", "total_operations", "last_operation_at"]
    list_filter = ["status", "machine_definition__provider"]
    search_fields = ["instance_id", "machine_definition__name"]
    readonly_fields = ["created_at", "updated_at", "success_rate", "is_available"]
    raw_id_fields = ["current_order_item"]


@admin.register(LogEntry)
class LogEntryAdmin(admin.ModelAdmin):
    list_display = ["timestamp", "level", "logger_name", "message_preview", "module", "function"]
    list_filter = ["level", "logger_name", "timestamp"]
    search_fields = ["message", "module", "function"]
    readonly_fields = ["timestamp"]
    raw_id_fields = ["order", "order_item", "machine_instance"]

    def message_preview(self, obj):
        return obj.message[:100] + "..." if len(obj.message) > 100 else obj.message

    message_preview.short_description = "Message"
