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
    return render(request, 'main/order_bootstrap.html', context)


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
            # Delete products
            deleted_count = Product.objects.filter(id__in=product_ids).delete()[0]
            
            if deleted_count > 0:
                messages.success(request, f'Successfully deleted {deleted_count} product(s).')
            else:
                messages.warning(request, 'No products were deleted.')
        else:
            messages.error(request, 'No products selected for deletion.')
    
    return redirect('main:inventory')


# API Views
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
        
        # Create the order
        order = Order.objects.create(
            title=data.get('title', ''),
            prompt=data.get('prompt', ''),
            base_parameters=data.get('parameters', {}),
            factory_machine_name=machine.name,
            provider=machine.provider,
            quantity=data.get('quantity', 1),
            project_name=data.get('project_name', ''),
        )
        
        # Merge machine defaults with user parameters (user parameters take precedence)
        merged_parameters = machine.default_parameters.copy()
        merged_parameters.update(order.base_parameters)
        
        # Create order items (signal will automatically trigger processing)
        for i in range(order.quantity):
            OrderItem.objects.create(
                order=order,
                prompt=order.prompt,
                parameters=merged_parameters,
                status='pending'
            )
        
        return JsonResponse({
            'success': True,
            'order_id': order.id,
            'message': f'Order placed successfully! {order.quantity} items are being generated.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400)
