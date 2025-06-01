from django.urls import path
from . import views

app_name = 'main'

urlpatterns = [
    # Main pages
    path('', views.order_view, name='home'),
    path('order/', views.order_view, name='order'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('production/', views.production_view, name='production'),
    path('settings/', views.settings_view, name='settings'),
    
    
    # API endpoints for AJAX
    path('api/factory-machines/', views.factory_machines_api, name='factory_machines_api'),
    path('api/place-order/', views.place_order_api, name='place_order_api'),
    
    # Product management
    path('products/<int:product_id>/', views.product_detail, name='product_detail'),
    path('products/<int:product_id>/delete/', views.product_delete, name='product_delete'),
]