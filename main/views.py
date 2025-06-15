import json

from django.contrib import messages
from django.core.paginator import Paginator
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_exempt

from .error_handling import ErrorCategory, ErrorHandler, UserFriendlyMessages
from .models import FactoryMachineDefinition, FactoryMachineInstance, LogEntry, Order, OrderItem, Product, Project
from .utils.project_context import (
    clear_project_context,
    ensure_project_context,
    get_project_aware_context,
    set_project_context,
)


def order_view(request):
    """Main order placement page - also serves as home page."""
    # Get available factory machines
    factory_machines = FactoryMachineDefinition.objects.filter(is_active=True).order_by("provider", "display_name")

    # Get current project from session context (with URL parameter override support)
    current_project = ensure_project_context(request)

    context = get_project_aware_context(
        request,
        factory_machines=factory_machines,
        page_title="Order",
        project_specifier="for",
        inventory_url=reverse("main:inventory"),
        production_url=reverse("main:production"),
    )
    return render(request, "main/order.html", context)


def inventory_view(request):
    """Product gallery and inventory management."""
    products = Product.objects.all().order_by("-created_at")

    # Use session-based project context for filtering
    current_project = ensure_project_context(request)
    if current_project:
        products = current_project.get_products_queryset().order_by("-created_at")

    # Pagination
    paginator = Paginator(products, 20)  # 20 products per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Serialize products for JavaScript
    products_json = []
    for product in page_obj:
        products_json.append(
            {
                "id": product.id,
                "title": product.title,
                "prompt": product.prompt,
                "file_url": product.file_url,
                "provider": product.provider,
                "model_name": product.model_name,
                "created_at": product.created_at.isoformat(),
                "width": product.width,
                "height": product.height,
                "product_type": getattr(product, "product_type", "image"),
            }
        )

    context = get_project_aware_context(
        request,
        page_obj=page_obj,
        products=page_obj,
        products_json=json.dumps(products_json),
        page_title="Inventory",
        project_specifier="of",
    )
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

    if not product.file_path:
        messages.error(request, "No file available for download.")
        return redirect("main:inventory")

    # Prepare the file response
    file_path = product.file_path
    file_extension = product.file_format or "png"
    file_name = f"{product.provider}_{product.id}_{product.created_at.strftime('%Y%m%d_%H%M%S')}.{file_extension}"

    try:
        # Use Django's default storage to handle the file
        from django.core.files.storage import default_storage

        if not default_storage.exists(file_path):
            messages.error(request, "File not found.")
            return redirect("main:inventory")

        with default_storage.open(file_path, "rb") as f:
            response = HttpResponse(f.read(), content_type="application/octet-stream")
            response["Content-Disposition"] = f'attachment; filename="{file_name}"'
            return response
    except Exception as e:
        messages.error(request, f"Error downloading file: {str(e)}")
        return redirect("main:inventory")


def bulk_download_products(request):
    """Download multiple products as a zip file."""
    if request.method != "POST":
        return JsonResponse({"success": False, "error": "Invalid request method"})

    import zipfile
    import tempfile
    from django.core.files.storage import default_storage

    try:
        product_ids = request.POST.getlist("product_ids")
        if not product_ids:
            return JsonResponse({"success": False, "error": "No products selected"})

        products = Product.objects.filter(id__in=product_ids)

        # Create a temporary zip file
        temp_zip = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")

        with zipfile.ZipFile(temp_zip.name, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for product in products:
                if product.file_path and default_storage.exists(product.file_path):
                    # Create a unique filename for the zip
                    file_extension = product.file_format or "png"
                    filename = (
                        f"{product.provider}_{product.id}_{product.created_at.strftime('%Y%m%d_%H%M%S')}.{file_extension}"
                    )

                    # Add file to zip
                    with default_storage.open(product.file_path, "rb") as f:
                        zip_file.writestr(filename, f.read())

        # Prepare response with zip file
        with open(temp_zip.name, "rb") as zip_data:
            response = HttpResponse(zip_data.read(), content_type="application/zip")
            response["Content-Disposition"] = f'attachment; filename="products_{len(products)}_files.zip"'

        # Clean up temp file
        import os

        os.unlink(temp_zip.name)

        return response

    except Exception as e:
        return JsonResponse({"success": False, "error": str(e)})


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
    """API endpoint for recent orders with status and project filtering support."""
    try:
        # Check for explicit project parameter, otherwise use session context
        project_id = request.GET.get("project")
        limit = int(request.GET.get("limit", 10))

        # Build base queryset
        orders_queryset = Order.objects.select_related().prefetch_related("orderitem_set")

        if project_id:
            # Explicit project parameter provided
            try:
                project = Project.objects.get(id=project_id, status="active")
                orders_queryset = orders_queryset.filter(project=project)
            except (Project.DoesNotExist, ValueError):
                # Invalid project ID, fall back to global orders (no additional filtering)
                pass
        else:
            # Use session-based project context
            current_project = ensure_project_context(request)
            if current_project:
                orders_queryset = orders_queryset.filter(project=current_project)

        # Get the orders with limit
        orders = orders_queryset.order_by("-created_at")[:limit]

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
    """API endpoint for recent products with project filtering support."""
    try:
        # Check for explicit project parameter, otherwise use session context
        project_id = request.GET.get("project")
        limit = int(request.GET.get("limit", 8))

        if project_id:
            # Explicit project parameter provided
            try:
                project = Project.objects.get(id=project_id, status="active")
                products = project.get_recent_products(limit)
            except (Project.DoesNotExist, ValueError):
                # Invalid project ID, fall back to global products
                products = Product.objects.order_by("-created_at")[:limit]
        else:
            # Use session-based project context
            current_project = ensure_project_context(request)
            if current_project:
                products = current_project.get_recent_products(limit)
            else:
                products = Product.objects.order_by("-created_at")[:limit]

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
            machine_id = int(data.get("machine_id"))
            machine = get_object_or_404(FactoryMachineDefinition, id=machine_id)
        except (ValueError, TypeError):
            return JsonResponse(
                {
                    "success": False,
                    "error": "Invalid machine_id format",
                    "user_message": "The selected AI model ID is invalid. Please refresh the page and try again.",
                },
                status=400,
            )
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
        try:
            generation_count = max(1, min(int(data.get("generation_count", 1)), 10))  # Limit to 10 generations
        except (ValueError, TypeError):
            generation_count = 1

        try:
            batch_size = max(1, min(int(data.get("batch_size", 4)), 4))  # Limit to 4 per batch
        except (ValueError, TypeError):
            batch_size = 4
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

        # Get project from session context (with fallback to explicit project_id for API compatibility)
        project = None
        project_id_str = data.get("project_id")
        if project_id_str:
            # Explicit project_id provided (for API backward compatibility)
            try:
                project_id = int(project_id_str)
                project = Project.objects.get(id=project_id, status="active")
            except (ValueError, TypeError, Project.DoesNotExist):
                pass
        else:
            # Use session-based project context
            project = ensure_project_context(request)

        # Create the order
        order = Order.objects.create(
            title=data.get("title", ""),
            prompt=prompt,
            negative_prompt=data.get("negative_prompt", ""),
            base_parameters=data.get("parameters", {}),
            factory_machine_name=machine.name,
            provider=machine.provider,
            quantity=total_products,  # Store total products for compatibility
            project=project,
            project_name=project.name if project else "",
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

        # Get file size if possible
        file_size = None
        if hasattr(product, "file_size") and product.file_size:
            file_size = product.file_size
        elif product.file_path:
            try:
                from django.core.files.storage import default_storage

                if default_storage.exists(product.file_path):
                    file_size = default_storage.size(product.file_path)
            except Exception:
                # Ignore file size errors - not critical for API response
                pass

        # Get order information if available
        order_id = None
        order_item = None
        factory_machine_definition = None

        try:
            # Get the order item associated with this product
            order_item = product.orderitem_set.first()
            if order_item:
                order_id = order_item.order.id
                factory_machine_definition = order_item.order.factory_machine_name
        except Exception:
            # Ignore order relationship errors - not critical for API response
            pass

        product_data = {
            "id": product.id,
            "title": product.title,
            "prompt": product.prompt,
            "negative_prompt": product.negative_prompt,
            "provider": product.provider,
            "model_name": product.model_name,
            "parameters": product.parameters,
            "file_url": product.file_url,
            "file_path": product.file_path,
            "file_size": file_size,
            "file_format": getattr(product, "file_format", None),
            "width": product.width,
            "height": product.height,
            "created_at": product.created_at.isoformat(),
            "updated_at": product.updated_at.isoformat() if hasattr(product, "updated_at") else None,
            "order_id": order_id,
            "factory_machine_definition": factory_machine_definition,
            "is_favorite": getattr(product, "is_favorite", False),
            "product_type": getattr(product, "product_type", "image"),
            "filename": getattr(product, "filename", None),
        }

        return JsonResponse(product_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=400)


# Project Management Views
def projects_view(request):
    """Projects overview page - serves as the new home page."""
    # Get active projects ordered by most recent
    projects = Project.objects.filter(status="active").order_by("-updated_at")

    # Get recent projects for quick access (last 6)
    recent_projects = projects[:6]

    context = {
        "projects": projects,
        "recent_projects": recent_projects,
        "page_title": "Projects",
    }
    return render(request, "main/projects.html", context)


def all_projects_view(request):
    """All projects page with search and filtering."""
    projects = Project.objects.all().order_by("-updated_at")

    # Search functionality
    search_query = request.GET.get("search", "")
    if search_query:
        projects = projects.filter(name__icontains=search_query) | projects.filter(description__icontains=search_query)

    # Status filter
    status_filter = request.GET.get("status", "")
    if status_filter:
        projects = projects.filter(status=status_filter)

    # Pagination
    paginator = Paginator(projects, 12)  # 12 projects per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "page_obj": page_obj,
        "projects": page_obj,
        "search_query": search_query,
        "status_filter": status_filter,
        "status_choices": Project.STATUS_CHOICES,
        "page_title": "All Projects",
    }
    return render(request, "main/all_projects.html", context)


def project_detail_view(request, project_id):
    """Project detail page showing orders and products."""
    project = get_object_or_404(Project, id=project_id)

    # Set this project as the current session context
    set_project_context(request, project)

    # Get project orders
    orders = project.order_set.all().order_by("-created_at")

    # Get project products
    products = project.get_products_queryset().order_by("-created_at")

    # Pagination for products
    paginator = Paginator(products, 20)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # Serialize products for JavaScript
    products_json = []
    for product in page_obj:
        products_json.append(
            {
                "id": product.id,
                "title": product.title,
                "prompt": product.prompt,
                "file_url": product.file_url,
                "provider": product.provider,
                "model_name": product.model_name,
                "created_at": product.created_at.isoformat(),
                "width": product.width,
                "height": product.height,
                "product_type": getattr(product, "product_type", "image"),
            }
        )

    # Build project actions HTML for header
    project_actions = f"""
        <a href="{reverse('main:projects')}" class="btn btn-outline-secondary me-2">
            <i class="bi bi-arrow-left"></i> Back to Projects
        </a>
        <a href="{reverse('main:order')}?project={project.id}" class="btn btn-primary me-2">
            <i class="bi bi-plus-circle"></i> New Order
        </a>
        <div class="btn-group" role="group">
            <button type="button" class="btn btn-outline-secondary dropdown-toggle" data-bs-toggle="dropdown">
                <i class="bi bi-gear"></i> Manage
            </button>
            <ul class="dropdown-menu">
                <li>
                    <button type="button" class="dropdown-item" data-bs-toggle="modal"
                            data-bs-target="#editProjectModal">
                        <i class="bi bi-pencil"></i> Edit Project
                    </button>
                </li>
                <li><hr class="dropdown-divider"></li>
                <li>
                    <button type="button" class="dropdown-item text-danger" data-bs-toggle="modal"
                            data-bs-target="#deleteProjectModal">
                        <i class="bi bi-trash"></i> Delete Project
                    </button>
                </li>
            </ul>
        </div>
    """

    context = get_project_aware_context(
        request,
        project=project,
        orders=orders[:10],  # Show first 10 orders
        page_obj=page_obj,
        products=page_obj,
        products_json=json.dumps(products_json),
        page_title=f"Project: {project.name}",
        project_actions=project_actions,
    )
    return render(request, "main/project_detail.html", context)


def project_create_view(request):
    """Create a new project."""
    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()

        if not name:
            messages.error(request, "Project name is required.")
            return redirect("main:projects")

        try:
            project = Project.objects.create(name=name, description=description)
            messages.success(request, f'Project "{project.name}" created successfully.')
            return redirect("main:project_detail", project_id=project.id)
        except Exception as e:
            messages.error(request, f"Error creating project: {str(e)}")
            return redirect("main:projects")

    return redirect("main:projects")


def project_update_view(request, project_id):
    """Update an existing project."""
    project = get_object_or_404(Project, id=project_id)

    if request.method == "POST":
        name = request.POST.get("name", "").strip()
        description = request.POST.get("description", "").strip()
        status = request.POST.get("status", project.status)

        if not name:
            messages.error(request, "Project name is required.")
            return redirect("main:project_detail", project_id=project.id)

        try:
            project.name = name
            project.description = description
            project.status = status
            project.save()
            messages.success(request, f'Project "{project.name}" updated successfully.')
        except Exception as e:
            messages.error(request, f"Error updating project: {str(e)}")

        return redirect("main:project_detail", project_id=project.id)

    return redirect("main:project_detail", project_id=project.id)


def project_delete_view(request, project_id):
    """Delete a project."""
    if request.method == "POST":
        project = get_object_or_404(Project, id=project_id)
        project_name = project.name

        try:
            project.delete()
            messages.success(request, f'Project "{project_name}" deleted successfully.')
        except Exception as e:
            messages.error(request, f"Error deleting project: {str(e)}")

    return redirect("main:projects")


def set_project_context_view(request, project_id):
    """Set project context in session and redirect to specified page."""
    try:
        project = Project.objects.get(id=project_id, status="active")
        set_project_context(request, project)
        messages.success(request, f"Switched to project: {project.name}")
    except Project.DoesNotExist:
        messages.error(request, "Project not found or inactive.")

    # Get redirect target from query parameter, default to order page
    next_url = request.GET.get("next", "main:order")
    try:
        return redirect(next_url)
    except:
        # Invalid redirect URL, fall back to order page
        return redirect("main:order")


def clear_project_context_view(request):
    """Clear project context from session and redirect to specified page."""
    clear_project_context(request)
    messages.info(request, "Project context cleared.")

    # Get redirect target from query parameter, default to projects page
    next_url = request.GET.get("next", "main:projects")
    try:
        return redirect(next_url)
    except:
        # Invalid redirect URL, fall back to projects page
        return redirect("main:projects")


# Project API Views
def projects_api(request):
    """API endpoint for projects list."""
    try:
        projects = Project.objects.filter(status="active").order_by("-updated_at")[:10]

        projects_data = []
        for project in projects:
            recent_products = project.get_recent_products(4)

            products_data = []
            for product in recent_products:
                products_data.append(
                    {
                        "id": product.id,
                        "file_url": product.file_url,
                        "title": product.title,
                        "created_at": product.created_at.isoformat(),
                    }
                )

            projects_data.append(
                {
                    "id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "status": project.status,
                    "order_count": project.order_count,
                    "product_count": project.product_count,
                    "created_at": project.created_at.isoformat(),
                    "updated_at": project.updated_at.isoformat(),
                    "recent_products": products_data,
                }
            )

        return JsonResponse({"projects": projects_data})

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)


def project_detail_api(request, project_id):
    """API endpoint for project details."""
    try:
        project = get_object_or_404(Project, id=project_id)

        # Get recent orders and products
        orders = project.order_set.all().order_by("-created_at")[:5]
        recent_products = project.get_recent_products(8)

        orders_data = []
        for order in orders:
            orders_data.append(
                {
                    "id": order.id,
                    "title": order.title or f"Order {order.id}",
                    "status": order.status,
                    "created_at": order.created_at.isoformat(),
                    "completion_percentage": order.completion_percentage,
                }
            )

        products_data = []
        for product in recent_products:
            products_data.append(
                {
                    "id": product.id,
                    "file_url": product.file_url,
                    "title": product.title,
                    "created_at": product.created_at.isoformat(),
                }
            )

        project_data = {
            "id": project.id,
            "name": project.name,
            "description": project.description,
            "status": project.status,
            "order_count": project.order_count,
            "product_count": project.product_count,
            "created_at": project.created_at.isoformat(),
            "updated_at": project.updated_at.isoformat(),
            "recent_orders": orders_data,
            "recent_products": products_data,
        }

        return JsonResponse(project_data)

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
