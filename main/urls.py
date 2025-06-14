from django.urls import path

from . import views

app_name = "main"

urlpatterns = [
    # Main pages
    path("", views.projects_view, name="home"),
    path("projects/", views.projects_view, name="projects"),
    path("projects/all/", views.all_projects_view, name="all_projects"),
    path("projects/<int:project_id>/", views.project_detail_view, name="project_detail"),
    path("projects/create/", views.project_create_view, name="project_create"),
    path("projects/<int:project_id>/update/", views.project_update_view, name="project_update"),
    path("projects/<int:project_id>/delete/", views.project_delete_view, name="project_delete"),
    path("projects/<int:project_id>/set-context/", views.set_project_context_view, name="set_project_context"),
    path("projects/clear-context/", views.clear_project_context_view, name="clear_project_context"),
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
    path("api/products/<int:product_id>/download/", views.product_download, name="api_product_download"),
    path("api/projects/", views.projects_api, name="projects_api"),
    path("api/projects/<int:project_id>/", views.project_detail_api, name="project_detail_api"),
    # Product management
    path("products/<int:product_id>/", views.product_detail, name="product_detail"),
    path("products/<int:product_id>/delete/", views.product_delete, name="product_delete"),
    path("products/<int:product_id>/download/", views.product_download, name="product_download"),
    path("products/bulk-download/", views.bulk_download_products, name="bulk_download_products"),
    path("products/bulk-delete/", views.bulk_delete_products, name="bulk_delete_products"),
]
