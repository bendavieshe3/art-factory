from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.paginator import Paginator
import json

from .models import Product, Order, OrderItem, FactoryMachineDefinition, FactoryMachineInstance, LogEntry
from .error_handling import ErrorHandler, UserFriendlyMessages, ErrorCategory


def order_view(request):
    """Main order placement page - also serves as home page."""
    # Get available factory machines
    factory_machines = FactoryMachineDefinition.objects.filter(is_active=True).order_by("provider", "display_name")

    context = {
        "factory_machines": factory_machines,
        "page_title": "Place Order",
    }
    return render(request, "main/order.html", context)


def inventory_view(request):
    """Product gallery and inventory management."""
    products = Product.objects.all().order_by("-created_at")

    # Pagination
    paginator = Paginator(products, 20)  # 20 products per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "products": page_obj,
        "page_title": "Inventory",
    }
    return render(request, "main/inventory.html", context)


def production_view(request):
    """Production monitoring and status."""
    # Get recent orders and their status
    recent_orders = Order.objects.all().order_by("-created_at")[:10]

    # Get factory machine instances
    machine_instances = FactoryMachineInstance.objects.all().order_by("machine_definition__display_name")

    # Get recent logs
    recent_logs = LogEntry.objects.all().order_by("-timestamp")[:50]

    context = {
        "recent_orders": recent_orders,
        "machine_instances": machine_instances,
        "recent_logs": recent_logs,
        "page_title": "Production",
    }
    return render(request, "main/production.html", context)


def settings_view(request):
    """Application settings and configuration."""
    context = {
        "page_title": "Settings",
    }
    return render(request, "main/settings.html", context)


def product_detail(request, product_id):
    """Individual product detail view."""
    product = get_object_or_404(Product, id=product_id)
    context = {
        "product": product,
        "page_title": f"Product {product.id}",
    }
    return render(request, "main/product_detail.html", context)


def product_delete(request, product_id):
    """Delete a product."""
    if request.method == "POST":
        product = get_object_or_404(Product, id=product_id)
        product_title = product.title or f"Product {product.id}"

        # Check if this is an AJAX request
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        try:
            product.delete()
            message = f'"{product_title}" has been deleted.'

            if is_ajax:
                return JsonResponse({"success": True, "message": message})
            else:
                messages.success(request, message)

        except Exception as e:
            error_message = f'Failed to delete "{product_title}". Please try again.'

            if is_ajax:
                return JsonResponse({"success": False, "message": error_message, "error": str(e)})
            else:
                messages.error(request, error_message)

    return redirect("main:inventory")


def product_download(request, product_id):
    """Download a product file."""
    product = get_object_or_404(Product, id=product_id)

    if not product.file:
        messages.error(request, "No file available for download.")
        return redirect("main:inventory")

    # Prepare the file response
    file_path = product.file.path
    file_name = f"{product.provider}_{product.id}_{product.created_at.strftime('%Y%m%d_%H%M%S')}.png"

    try:
        with open(file_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/octet-stream")
            response["Content-Disposition"] = f'attachment; filename="{file_name}"'
            return response
    except FileNotFoundError:
        messages.error(request, "File not found.")
        return redirect("main:inventory")


def bulk_delete_products(request):
    """Delete multiple products at once."""
    if request.method == "POST":
        product_ids = request.POST.getlist("product_ids")

        # Check if this is an AJAX request
        is_ajax = request.headers.get("X-Requested-With") == "XMLHttpRequest"

        if product_ids:
            try:
                # Count products before deletion to get accurate count
                products_to_delete = Product.objects.filter(id__in=product_ids)
                product_count = products_to_delete.count()

                if product_count > 0:
                    # Delete products (this will cascade delete related OrderItems)
                    products_to_delete.delete()

                    message = f"Successfully deleted {product_count} product(s)."

                    if is_ajax:
                        return JsonResponse({"success": True, "message": message, "deleted_count": product_count})
                    else:
                        messages.success(request, message)
                else:
                    message = "No products were found to delete."

                    if is_ajax:
                        return JsonResponse({"success": False, "message": message})
                    else:
                        messages.warning(request, message)

            except Exception as e:
                error_message = "An error occurred while deleting products. Please try again."

                if is_ajax:
                    return JsonResponse({"success": False, "message": error_message, "error": str(e)})
                else:
                    messages.error(request, error_message)
        else:
            message = "No products selected for deletion."

            if is_ajax:
                return JsonResponse({"success": False, "message": message})
            else:
                messages.error(request, message)

    # For non-AJAX requests, redirect back to inventory
    return redirect("main:inventory")


# API Views
def recent_orders_api(request):
    """API endpoint for recent orders with status."""
    try:
        # Get last 10 orders with their items
        orders = Order.objects.select_related().prefetch_related("orderitem_set").order_by("-created_at")[:10]

        orders_data = []
        for order in orders:
            # Calculate order status based on items
            items = order.orderitem_set.all()
            total_items = items.count()

            if total_items == 0:
                status = "pending"
                progress = 0
            else:
                completed_items = items.filter(status="completed").count()
                failed_items = items.filter(status="failed").count()
                processing_items = items.filter(status__in=["assigned", "processing"]).count()
                pending_items = items.filter(status="pending").count()

                if completed_items == total_items:
                    status = "completed"
                    progress = 100
                elif failed_items == total_items:
                    status = "failed"
                    progress = 100
                elif failed_items > 0 and (completed_items + failed_items) == total_items:
                    status = "partial"
                    progress = 100
                elif processing_items > 0 or pending_items < total_items:
                    status = "processing"
                    progress = int((completed_items / total_items) * 100) if total_items > 0 else 0
                else:
                    status = "pending"
                    progress = 0

            orders_data.append(
                {
                    "id": order.id,
                    "title": order.title or f"Order {order.id}",
                    "factory_machine_name": order.factory_machine_name,
                    "provider": order.provider,
                    "status": status,
                    "progress": progress,
                    "total_items": total_items,
                    "completed_items": items.filter(status="completed").count() if total_items > 0 else 0,
                    "failed_items": items.filter(status="failed").count() if total_items > 0 else 0,
                    "created_at": order.created_at.isoformat(),
                    "prompt": order.prompt[:100] + "..." if len(order.prompt) > 100 else order.prompt,
                }
            )

        return JsonResponse({"orders": orders_data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def recent_products_api(request):
    """API endpoint for recent products."""
    try:
        # Get last 8 products for the strip display
        products = Product.objects.order_by("-created_at")[:8]

        products_data = []
        for product in products:
            products_data.append(
                {
                    "id": product.id,
                    "title": product.title or f"Product {product.id}",
                    "file_url": product.file_url,
                    "provider": product.provider,
                    "model_name": product.model_name,
                    "created_at": product.created_at.isoformat(),
                    "width": product.width,
                    "height": product.height,
                }
            )

        return JsonResponse({"products": products_data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def order_status_api(request, order_id):
    """API endpoint for polling specific order status."""
    try:
        order = get_object_or_404(Order, id=order_id)
        items = order.orderitem_set.all()

        # Calculate detailed status
        total_items = items.count()
        status_counts = {
            "pending": items.filter(status="pending").count(),
            "assigned": items.filter(status="assigned").count(),
            "processing": items.filter(status="processing").count(),
            "completed": items.filter(status="completed").count(),
            "failed": items.filter(status="failed").count(),
        }

        # Determine overall status
        if status_counts["completed"] == total_items:
            overall_status = "completed"
        elif status_counts["failed"] == total_items:
            overall_status = "failed"
        elif status_counts["failed"] > 0 and (status_counts["completed"] + status_counts["failed"]) == total_items:
            overall_status = "partial"
        elif status_counts["processing"] > 0 or status_counts["assigned"] > 0:
            overall_status = "processing"
        else:
            overall_status = "pending"

        # Calculate progress
        completed_or_failed = status_counts["completed"] + status_counts["failed"]
        progress = int((completed_or_failed / total_items) * 100) if total_items > 0 else 0

        # Get latest completed product for preview
        latest_product = None
        latest_item = items.filter(status="completed", product__isnull=False).order_by("-completed_at").first()
        if latest_item and latest_item.product:
            latest_product = {
                "id": latest_item.product.id,
                "file_url": latest_item.product.file_url,
                "created_at": latest_item.product.created_at.isoformat(),
            }

        # Get any error messages with user-friendly formatting
        error_items = items.filter(status="failed").exclude(error_message="")
        error_messages = []
        for item in error_items[:3]:  # Show up to 3 errors
            # Try to get a more user-friendly message if available
            if item.error_message:
                error_messages.append(item.error_message)
            else:
                error_messages.append("An unexpected error occurred during generation.")

        return JsonResponse(
            {
                "order_id": order.id,
                "status": overall_status,
                "progress": progress,
                "total_items": total_items,
                "status_counts": status_counts,
                "latest_product": latest_product,
                "error_messages": error_messages,
                "updated_at": order.updated_at.isoformat(),
            }
        )

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def factory_machines_api(request):
    """API endpoint to get available factory machines."""
    machines = FactoryMachineDefinition.objects.filter(is_active=True).values(
        "id", "name", "display_name", "description", "provider", "modality", "parameter_schema", "default_parameters"
    )
    return JsonResponse({"machines": list(machines)})


@csrf_exempt
def place_order_api(request):
    """API endpoint to place a new order with comprehensive error handling."""
    if request.method != "POST":
        return JsonResponse({"error": "Only POST method allowed"}, status=405)

    try:
        # Parse request data
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid JSON format",
                    "user_message": "The request data was not formatted correctly. Please try again.",
                },
                status=400,
            )

        # Validate required fields
        required_fields = ["machine_id", "prompt"]
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            return JsonResponse(
                {
                    "success": False,
                    "error": f"Missing required fields: {', '.join(missing_fields)}",
                    "user_message": "Please fill in all required fields and try again.",
                },
                status=400,
            )

        # Get the factory machine
        try:
            machine = get_object_or_404(FactoryMachineDefinition, id=data.get("machine_id"))
        except:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid machine_id",
                    "user_message": "The selected AI model is not available. Please refresh the page and try again.",
                },
                status=400,
            )

        # Validate prompt length
        prompt = data.get("prompt", "").strip()
        if len(prompt) < 3:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Prompt too short",
                    "user_message": "Your prompt must be at least 3 characters long.",
                },
                status=400,
            )
        elif len(prompt) > 2000:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Prompt too long",
                    "user_message": "Your prompt must be less than 2000 characters.",
                },
                status=400,
            )

        # Get generation parameters with validation
        generation_count = max(1, min(data.get("generation_count", 1), 10))  # Limit to 10 generations
        batch_size = max(1, min(data.get("batch_size", 4), 4))  # Limit to 4 per batch
        total_products = generation_count * batch_size

        # Validate total products limit
        if total_products > 20:
            return JsonResponse(
                {
                    "success": False,
                    "error": "Too many products requested",
                    "user_message": "You can generate a maximum of 20 images in a single order. Please reduce your quantities.",
                },
                status=400,
            )

        # Create the order
        order = Order.objects.create(
            title=data.get("title", ""),
            prompt=prompt,
            negative_prompt=data.get("negative_prompt", ""),
            base_parameters=data.get("parameters", {}),
            factory_machine_name=machine.name,
            provider=machine.provider,
            quantity=total_products,  # Store total products for compatibility
            project_name=data.get("project_name", ""),
        )

        # Merge machine defaults with user parameters (user parameters take precedence)
        merged_parameters = machine.default_parameters.copy()
        merged_parameters.update(order.base_parameters)

        # Set batch parameter based on provider
        if machine.provider == "fal.ai":
            batch_param = "num_images"
        else:  # replicate
            batch_param = "num_outputs"

        # Create order items - one for each generation
        for generation in range(generation_count):
            # Set batch parameter in the item's parameters
            item_parameters = merged_parameters.copy()
            item_parameters[batch_param] = batch_size

            OrderItem.objects.create(
                order=order,
                prompt=order.prompt,
                negative_prompt=order.negative_prompt,
                parameters=item_parameters,
                total_quantity=batch_size,
                batch_size=batch_size,
                status="pending",
            )

        return JsonResponse(
            {
                "success": True,
                "order_id": order.id,
                "message": f"Order placed successfully! {generation_count} generations will create {total_products} images.",
                "total_products": total_products,
                "generation_count": generation_count,
                "batch_size": batch_size,
            }
        )

    except Exception as e:
        # Use error handler for unexpected errors
        error_handler = ErrorHandler()
        friendly_message = UserFriendlyMessages.get_friendly_message(ErrorCategory.UNKNOWN, str(e))

        return JsonResponse(
            {
                "success": False,
                "error": str(e),
                "user_message": friendly_message["message"],
                "action": friendly_message["action"],
            },
            status=500,
        )


def order_detail_api(request, order_id):
    """API endpoint to get order details including negative prompt."""
    try:
        order = get_object_or_404(Order, id=order_id)
        order_items = order.orderitem_set.all()

        order_data = {
            "id": order.id,
            "title": order.title,
            "prompt": order.prompt,
            "negative_prompt": order.negative_prompt,
            "status": order.status,
            "created_at": order.created_at.isoformat(),
            "items": [],
        }

        for item in order_items:
            order_data["items"].append(
                {
                    "id": item.id,
                    "prompt": item.prompt,
                    "negative_prompt": item.negative_prompt,
                    "status": item.status,
                    "parameters": item.parameters,
                }
            )

        return JsonResponse(order_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


def product_detail_api(request, product_id):
    """API endpoint to get product details including negative prompt."""
    try:
        product = get_object_or_404(Product, id=product_id)

        product_data = {
            "id": product.id,
            "title": product.title,
            "prompt": product.prompt,
            "negative_prompt": product.negative_prompt,
            "provider": product.provider,
            "model_name": product.model_name,
            "parameters": product.parameters,
            "file_url": product.file_url,
            "created_at": product.created_at.isoformat(),
        }

        return JsonResponse(product_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)
