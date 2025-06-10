from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    # Main pages
    path("", views.order_view, name="home"),
    path("order/", views.order_view, name="order"),
    path("inventory/", views.inventory_view, name="inventory"),
    path("production/", views.production_view, name="production"),
    path("settings/", views.settings_view, name="settings"),
    # API endpoints for AJAX
    path("api/factory-machines/", views.factory_machines_api, name="factory_machines_api"),
    path("api/place-order/", views.place_order_api, name="place-order"),
    path("api/recent-orders/", views.recent_orders_api, name="recent_orders_api"),
    path("api/recent-products/", views.recent_products_api, name="recent_products_api"),
    path("api/order-status/<int:order_id>/", views.order_status_api, name="order_status_api"),
    path("api/orders/<int:order_id>/", views.order_detail_api, name="order_detail_api"),
    path("api/products/<int:product_id>/", views.product_detail_api, name="product_detail_api"),
    # Product management
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("products/<int:product_id>/delete/", views.product_delete, name="product_delete"),
    path("products/<int:product_id>/download/", views.product_download, name="product_download"),
    path("products/bulk-download/", views.bulk_download_products, name="bulk_download_products"),
    path("products/bulk-delete/", views.bulk_delete_products, name="bulk_delete_products"),
]
