from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages
from django.core.paginator import Paginator
import json

from .models import Product, Order, OrderItem, FactoryMachineDefinition, FactoryMachineInstance, LogEntry


def order_view(request):
    """Main order placement page - also serves as home page."""
    # Get available factory machines
    factory_machines = FactoryMachineDefinition.objects.filter(is_active=True).order_by('provider', 'display_name')
    
    context = {
        'factory_machines': factory_machines,
        'page_title': 'Place Order',
    }
    return render(request, 'main/order.html', context)


def inventory_view(request):
    """Product gallery and inventory management."""
    products = Product.objects.all().order_by('-created_at')
    
    # Pagination
    paginator = Paginator(products, 20)  # 20 products per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'products': page_obj,
        'page_title': 'Inventory',
    }
    return render(request, 'main/inventory.html', context)


def production_view(request):
    """Production monitoring and status."""
    # Get recent orders and their status
    recent_orders = Order.objects.all().order_by('-created_at')[:10]
    
    # Get factory machine instances
    machine_instances = FactoryMachineInstance.objects.all().order_by('machine_definition__display_name')
    
    # Get recent logs
    recent_logs = LogEntry.objects.all().order_by('-timestamp')[:50]
    
    context = {
        'recent_orders': recent_orders,
        'machine_instances': machine_instances,
        'recent_logs': recent_logs,
        'page_title': 'Production',
    }
    return render(request, 'main/production.html', context)


def settings_view(request):
    """Application settings and configuration."""
    context = {
        'page_title': 'Settings',
    }
    return render(request, 'main/settings.html', context)


def product_detail(request, product_id):
    """Individual product detail view."""
    product = get_object_or_404(Product, id=product_id)
    context = {
        'product': product,
        'page_title': f'Product {product.id}',
    }
    return render(request, 'main/product_detail.html', context)


def product_delete(request, product_id):
    """Delete a product."""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id)
        product.delete()
        messages.success(request, f'Product "{product.title or product.id}" has been deleted.')
        return redirect('main:inventory')
    return redirect('main:inventory')


def product_download(request, product_id):
    """Download a product file."""
    product = get_object_or_404(Product, id=product_id)
    
    if not product.file:
        messages.error(request, 'No file available for download.')
        return redirect('main:inventory')
    
    # Prepare the file response
    file_path = product.file.path
    file_name = f"{product.provider}_{product.id}_{product.created_at.strftime('%Y%m%d_%H%M%S')}.png"
    
    try:
        with open(file_path, 'rb') as f:
            response = HttpResponse(f.read(), content_type='application/octet-stream')
            response['Content-Disposition'] = f'attachment; filename="{file_name}"'
            return response
    except FileNotFoundError:
        messages.error(request, 'File not found.')
        return redirect('main:inventory')


def bulk_delete_products(request):
    """Delete multiple products at once."""
    if request.method == 'POST':
        product_ids = request.POST.getlist('product_ids')
        
        if product_ids:
            # Count products before deletion to get accurate count
            products_to_delete = Product.objects.filter(id__in=product_ids)
            product_count = products_to_delete.count()
            
            # Delete products (this will cascade delete related OrderItems)
            products_to_delete.delete()
            
            if product_count > 0:
                messages.success(request, f'Successfully deleted {product_count} product(s).')
            else:
                messages.warning(request, 'No products were deleted.')
        else:
            messages.error(request, 'No products selected for deletion.')
    
    return redirect('main:inventory')


# API Views
def recent_orders_api(request):
    """API endpoint for recent orders with status."""
    try:
        # Get last 10 orders with their items
        orders = Order.objects.select_related().prefetch_related('orderitem_set').order_by('-created_at')[:10]
        
        orders_data = []
        for order in orders:
            # Calculate order status based on items
            items = order.orderitem_set.all()
            total_items = items.count()
            
            if total_items == 0:
                status = 'pending'
                progress = 0
            else:
                completed_items = items.filter(status='completed').count()
                failed_items = items.filter(status='failed').count()
                processing_items = items.filter(status__in=['assigned', 'processing']).count()
                pending_items = items.filter(status='pending').count()
                
                if completed_items == total_items:
                    status = 'completed'
                    progress = 100
                elif failed_items == total_items:
                    status = 'failed'
                    progress = 100
                elif failed_items > 0 and (completed_items + failed_items) == total_items:
                    status = 'partial'
                    progress = 100
                elif processing_items > 0 or pending_items < total_items:
                    status = 'processing'
                    progress = int((completed_items / total_items) * 100) if total_items > 0 else 0
                else:
                    status = 'pending'
                    progress = 0
            
            orders_data.append({
                'id': order.id,
                'title': order.title or f'Order {order.id}',
                'factory_machine_name': order.factory_machine_name,
                'provider': order.provider,
                'status': status,
                'progress': progress,
                'total_items': total_items,
                'completed_items': items.filter(status='completed').count() if total_items > 0 else 0,
                'failed_items': items.filter(status='failed').count() if total_items > 0 else 0,
                'created_at': order.created_at.isoformat(),
                'prompt': order.prompt[:100] + '...' if len(order.prompt) > 100 else order.prompt
            })
        
        return JsonResponse({'orders': orders_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def recent_products_api(request):
    """API endpoint for recent products."""
    try:
        # Get last 8 products for the strip display
        products = Product.objects.order_by('-created_at')[:8]
        
        products_data = []
        for product in products:
            products_data.append({
                'id': product.id,
                'title': product.title or f'Product {product.id}',
                'file_url': product.file_url,
                'provider': product.provider,
                'model_name': product.model_name,
                'created_at': product.created_at.isoformat(),
                'width': product.width,
                'height': product.height
            })
        
        return JsonResponse({'products': products_data})
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def order_status_api(request, order_id):
    """API endpoint for polling specific order status."""
    try:
        order = get_object_or_404(Order, id=order_id)
        items = order.orderitem_set.all()
        
        # Calculate detailed status
        total_items = items.count()
        status_counts = {
            'pending': items.filter(status='pending').count(),
            'assigned': items.filter(status='assigned').count(), 
            'processing': items.filter(status='processing').count(),
            'completed': items.filter(status='completed').count(),
            'failed': items.filter(status='failed').count()
        }
        
        # Determine overall status
        if status_counts['completed'] == total_items:
            overall_status = 'completed'
        elif status_counts['failed'] == total_items:
            overall_status = 'failed'
        elif status_counts['failed'] > 0 and (status_counts['completed'] + status_counts['failed']) == total_items:
            overall_status = 'partial'
        elif status_counts['processing'] > 0 or status_counts['assigned'] > 0:
            overall_status = 'processing'
        else:
            overall_status = 'pending'
        
        # Calculate progress
        completed_or_failed = status_counts['completed'] + status_counts['failed']
        progress = int((completed_or_failed / total_items) * 100) if total_items > 0 else 0
        
        # Get latest completed product for preview
        latest_product = None
        latest_item = items.filter(status='completed', product__isnull=False).order_by('-completed_at').first()
        if latest_item and latest_item.product:
            latest_product = {
                'id': latest_item.product.id,
                'file_url': latest_item.product.file_url,
                'created_at': latest_item.product.created_at.isoformat()
            }
        
        # Get any error messages
        error_items = items.filter(status='failed').exclude(error_message='')
        error_messages = [item.error_message for item in error_items[:3]]  # Show up to 3 errors
        
        return JsonResponse({
            'order_id': order.id,
            'status': overall_status,
            'progress': progress,
            'total_items': total_items,
            'status_counts': status_counts,
            'latest_product': latest_product,
            'error_messages': error_messages,
            'updated_at': order.updated_at.isoformat()
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


def factory_machines_api(request):
    """API endpoint to get available factory machines."""
    machines = FactoryMachineDefinition.objects.filter(is_active=True).values(
        'id', 'name', 'display_name', 'description', 'provider', 
        'modality', 'parameter_schema', 'default_parameters'
    )
    return JsonResponse({'machines': list(machines)})


@csrf_exempt
def place_order_api(request):
    """API endpoint to place a new order."""
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)
    
    try:
        data = json.loads(request.body)
        
        # Get the factory machine
        machine = get_object_or_404(FactoryMachineDefinition, id=data.get('machine_id'))
        
        # Get generation parameters
        generation_count = data.get('generation_count', 1)
        batch_size = data.get('batch_size', 4)
        total_products = generation_count * batch_size
        
        # Create the order
        order = Order.objects.create(
            title=data.get('title', ''),
            prompt=data.get('prompt', ''),
            negative_prompt=data.get('negative_prompt', ''),
            base_parameters=data.get('parameters', {}),
            factory_machine_name=machine.name,
            provider=machine.provider,
            quantity=total_products,  # Store total products for compatibility
            project_name=data.get('project_name', ''),
        )
        
        # Merge machine defaults with user parameters (user parameters take precedence)
        merged_parameters = machine.default_parameters.copy()
        merged_parameters.update(order.base_parameters)
        
        # Validate batch size
        max_batch_size = 4  # Both fal.ai and Replicate support up to 4
        validated_batch_size = min(batch_size, max_batch_size)
        
        if machine.provider == 'fal.ai':
            batch_param = 'num_images'
        else:  # replicate
            batch_param = 'num_outputs'
        
        # Create order items - one for each generation
        for generation in range(generation_count):
            # Set batch parameter in the item's parameters
            item_parameters = merged_parameters.copy()
            item_parameters[batch_param] = validated_batch_size
            
            OrderItem.objects.create(
                order=order,
                prompt=order.prompt,
                negative_prompt=order.negative_prompt,
                parameters=item_parameters,
                total_quantity=validated_batch_size,
                batch_size=validated_batch_size,
                status='pending'
            )
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'message': f'Order placed successfully! {generation_count} generations will create {total_products} products.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)


def order_detail_api(request, order_id):
    """API endpoint to get order details including negative prompt."""
    try:
        order = get_object_or_404(Order, id=order_id)
        order_items = order.orderitem_set.all()
        
        order_data = {
            'id': order.id,
            'title': order.title,
            'prompt': order.prompt,
            'negative_prompt': order.negative_prompt,
            'status': order.status,
            'created_at': order.created_at.isoformat(),
            'items': []
        }
        
        for item in order_items:
            order_data['items'].append({
                'id': item.id,
                'prompt': item.prompt,
                'negative_prompt': item.negative_prompt,
                'status': item.status,
                'parameters': item.parameters
            })
        
        return JsonResponse(order_data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)


def product_detail_api(request, product_id):
    """API endpoint to get product details including negative prompt."""
    try:
        product = get_object_or_404(Product, id=product_id)
        
        product_data = {
            'id': product.id,
            'title': product.title,
            'prompt': product.prompt,
            'negative_prompt': product.negative_prompt,
            'provider': product.provider,
            'model_name': product.model_name,
            'parameters': product.parameters,
            'file_url': product.file_url,
            'created_at': product.created_at.isoformat()
        }
        
        return JsonResponse(product_data)
        
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=400)
