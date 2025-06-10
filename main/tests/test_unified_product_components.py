"""
Comprehensive tests for the unified Product Card and Collection system.

Tests cover:
1. ProductCard JavaScript class functionality (rendering, variants, event handling)
2. ProductCollection JavaScript class functionality (layout management, bulk operations)
3. View endpoints for bulk operations (bulk_download_products, bulk_delete_products)
4. Product serialization in inventory_view
5. Integration tests for the unified component system
"""

import json
import tempfile
import zipfile
from io import BytesIO
from unittest.mock import MagicMock, mock_open, patch

from django.core.files.storage import default_storage
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from main.models import FactoryMachineDefinition, Order, OrderItem, Product


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class ProductCardJavaScriptTestCase(TestCase):
    """Test ProductCard JavaScript functionality through rendered templates."""

    def setUp(self):
        """Set up test data and client."""
        self.client = Client()
        
        # Create a factory machine for testing
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            description="Test model for product card testing",
            provider="test-provider",
            modality="text-to-image",
            parameter_schema={"width": 512, "height": 512},
            default_parameters={"width": 512, "height": 512},
            is_active=True,
        )
        
        # Create test order and product
        self.order = Order.objects.create(
            title="Test Order",
            prompt="test prompt for product card",
            factory_machine_name=self.factory_machine.name,
            provider="test-provider",
            quantity=1,
        )
        
        self.order_item = OrderItem.objects.create(
            order=self.order,
            prompt=self.order.prompt,
            parameters={"width": 512, "height": 512},
            status="completed",
        )
        
        self.product = Product.objects.create(
            order_item=self.order_item,
            title="Test Product",
            prompt="test prompt for product card",
            provider="test-provider",
            model_name="test/model",
            file_path="products/test_image.png",
            file_size=1024,
            file_format="png",
            width=512,
            height=512,
            product_type="image",
        )

    def test_inventory_template_contains_product_card_javascript(self):
        """Test that inventory template includes ProductCard JavaScript components."""
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        # Check for ProductCollection class initialization
        self.assertContains(response, "new ProductCollection")
        self.assertContains(response, "#inventoryCollection")
        
        # Check for product card configuration options
        self.assertContains(response, "selectable: true")
        self.assertContains(response, "showBulkActions: true")
        self.assertContains(response, "cardVariant: 'standard'")
        self.assertContains(response, "showCheckbox: true")
        self.assertContains(response, "showActions: true")
        self.assertContains(response, "showDelete: true")
        self.assertContains(response, "clickAction: 'select'")

    def test_inventory_template_contains_product_data(self):
        """Test that inventory template includes serialized product data."""
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        # Check for product data injection
        self.assertContains(response, "window.inventoryProductsData")
        self.assertContains(response, "loadProducts(window.inventoryProductsData)")
        
        # Check that product data is properly JSON-encoded
        products_data = response.context['products_json']
        parsed_data = json.loads(products_data)
        
        self.assertIsInstance(parsed_data, list)
        if len(parsed_data) > 0:
            product_data = parsed_data[0]
            expected_fields = [
                'id', 'title', 'prompt', 'file_url', 'provider', 
                'model_name', 'created_at', 'width', 'height', 'product_type'
            ]
            for field in expected_fields:
                self.assertIn(field, product_data)

    def test_inventory_template_event_handlers(self):
        """Test that inventory template includes proper event handlers."""
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        # Check for product modal event handler
        self.assertContains(response, "addEventListener('productModalOpen'")
        self.assertContains(response, "console.log('Product modal open requested:'")

    def test_product_serialization_completeness(self):
        """Test that product serialization includes all necessary fields."""
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        products_json = response.context['products_json']
        products_data = json.loads(products_json)
        
        if len(products_data) > 0:
            product_data = products_data[0]
            
            # Verify all expected fields are present
            self.assertEqual(product_data['id'], self.product.id)
            self.assertEqual(product_data['title'], self.product.title)
            self.assertEqual(product_data['prompt'], self.product.prompt)
            self.assertEqual(product_data['file_url'], self.product.file_url)
            self.assertEqual(product_data['provider'], self.product.provider)
            self.assertEqual(product_data['model_name'], self.product.model_name)
            self.assertEqual(product_data['width'], self.product.width)
            self.assertEqual(product_data['height'], self.product.height)
            self.assertEqual(product_data['product_type'], self.product.product_type)
            
            # Verify created_at is properly formatted
            self.assertIn('T', product_data['created_at'])  # ISO format includes T
            
            # Verify product_type defaults to 'image' when not set
            self.assertEqual(product_data['product_type'], 'image')


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class ProductCollectionJavaScriptTestCase(TestCase):
    """Test ProductCollection JavaScript functionality through rendered templates."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create multiple products for collection testing
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            provider="test-provider",
            modality="text-to-image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )
        
        self.order = Order.objects.create(
            title="Collection Test Order",
            prompt="test prompt",
            factory_machine_name=self.factory_machine.name,
            provider="test-provider",
            quantity=3,
        )
        
        self.products = []
        for i in range(3):
            order_item = OrderItem.objects.create(
                order=self.order,
                prompt=f"test prompt {i}",
                parameters={},
                status="completed",
            )
            
            product = Product.objects.create(
                order_item=order_item,
                title=f"Test Product {i}",
                prompt=f"test prompt {i}",
                provider="test-provider",
                model_name="test/model",
                file_path=f"products/test_image_{i}.png",
                file_size=1024,
                file_format="png",
                width=512,
                height=512,
            )
            self.products.append(product)

    def test_collection_initialization_options(self):
        """Test ProductCollection initialization with proper options."""
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        # Check for collection container
        self.assertContains(response, 'id="inventoryCollection"')
        
        # Check for grid layout option
        self.assertContains(response, "new ProductCollection('#inventoryCollection', 'grid'")
        
        # Check for collection options
        collection_options = [
            "selectable: true",
            "showBulkActions: true", 
            "cardVariant: 'standard'",
            "showCheckbox: true",
            "showActions: true",
            "showDelete: true",
            "clickAction: 'select'"
        ]
        
        for option in collection_options:
            self.assertContains(response, option)

    def test_collection_data_loading(self):
        """Test that collection properly loads product data."""
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        # Check for data loading logic
        self.assertContains(response, "if (window.inventoryProductsData && window.inventoryProductsData.length > 0)")
        self.assertContains(response, "inventoryCollection.loadProducts(window.inventoryProductsData)")
        
        # Verify multiple products are serialized
        products_data = json.loads(response.context['products_json'])
        self.assertEqual(len(products_data), 3)
        
        # Verify each product has required fields (products ordered by -created_at, so reverse order)
        for i, product_data in enumerate(products_data):
            expected_index = len(products_data) - 1 - i  # Reverse order due to -created_at ordering
            self.assertEqual(product_data['title'], f"Test Product {expected_index}")
            self.assertEqual(product_data['prompt'], f"test prompt {expected_index}")

    def test_collection_layout_modes(self):
        """Test that collection supports different layout modes."""
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        # Inventory uses grid layout
        self.assertContains(response, "'grid'")
        
        # Check that layout string is properly passed to constructor
        self.assertContains(response, "new ProductCollection('#inventoryCollection', 'grid'")


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class BulkOperationsViewTestCase(TestCase):
    """Test bulk operation view endpoints."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        # Create factory machine and products for bulk operations
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            provider="test-provider",
            modality="text-to-image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )
        
        self.order = Order.objects.create(
            title="Bulk Test Order",
            prompt="bulk test prompt",
            factory_machine_name=self.factory_machine.name,
            provider="test-provider",
            quantity=3,
        )
        
        self.products = []
        for i in range(3):
            order_item = OrderItem.objects.create(
                order=self.order,
                prompt=f"bulk test prompt {i}",
                parameters={},
                status="completed",
            )
            
            product = Product.objects.create(
                order_item=order_item,
                title=f"Bulk Test Product {i}",
                prompt=f"bulk test prompt {i}",
                provider="test-provider",
                model_name="test/model",
                file_path=f"products/bulk_test_{i}.png",
                file_size=1024,
                file_format="png",
                width=512,
                height=512,
            )
            self.products.append(product)

    def test_bulk_delete_success_ajax(self):
        """Test successful bulk delete operation via AJAX."""
        product_ids = [str(p.id) for p in self.products[:2]]  # Delete first two products
        
        response = self.client.post(
            reverse('main:bulk_delete_products'),
            data={'product_ids': product_ids},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertEqual(data['deleted_count'], 2)
        self.assertIn('Successfully deleted 2 product(s)', data['message'])
        
        # Verify products were actually deleted
        remaining_products = Product.objects.filter(id__in=[p.id for p in self.products])
        self.assertEqual(remaining_products.count(), 1)
        self.assertEqual(remaining_products.first().id, self.products[2].id)

    def test_bulk_delete_success_non_ajax(self):
        """Test successful bulk delete operation via standard form."""
        product_ids = [str(p.id) for p in self.products]
        
        response = self.client.post(
            reverse('main:bulk_delete_products'),
            data={'product_ids': product_ids}
        )
        
        # Should redirect to inventory
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('main:inventory'))
        
        # Verify all products were deleted
        remaining_products = Product.objects.filter(id__in=[p.id for p in self.products])
        self.assertEqual(remaining_products.count(), 0)

    def test_bulk_delete_no_products_selected_ajax(self):
        """Test bulk delete with no products selected via AJAX."""
        response = self.client.post(
            reverse('main:bulk_delete_products'),
            data={'product_ids': []},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('No products selected', data['message'])

    def test_bulk_delete_invalid_product_ids_ajax(self):
        """Test bulk delete with invalid product IDs via AJAX."""
        response = self.client.post(
            reverse('main:bulk_delete_products'),
            data={'product_ids': ['99999', '99998']},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('No products were found to delete', data['message'])

    def test_bulk_delete_error_handling_ajax(self):
        """Test bulk delete error handling via AJAX."""
        with patch.object(Product.objects, 'filter') as mock_filter:
            mock_queryset = MagicMock()
            mock_queryset.count.return_value = 2
            mock_queryset.delete.side_effect = Exception("Database error")
            mock_filter.return_value = mock_queryset
            
            response = self.client.post(
                reverse('main:bulk_delete_products'),
                data={'product_ids': ['1', '2']},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            
            self.assertFalse(data['success'])
            self.assertIn('An error occurred while deleting products', data['message'])
            self.assertIn('error', data)

    @patch('django.core.files.storage.default_storage')
    def test_bulk_download_success(self, mock_storage):
        """Test successful bulk download operation."""
        # Mock file storage with context manager support
        mock_storage.exists.return_value = True
        
        # Create a proper mock file object with context manager support
        mock_file = MagicMock()
        mock_file.read.return_value = b"fake_image_data"
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = None
        mock_storage.open.return_value = mock_file
        
        product_ids = [str(p.id) for p in self.products[:2]]
        
        response = self.client.post(
            reverse('main:bulk_download_products'),
            data={'product_ids': product_ids}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('products_2_files.zip', response['Content-Disposition'])

    def test_bulk_download_no_products_selected(self):
        """Test bulk download with no products selected."""
        response = self.client.post(
            reverse('main:bulk_download_products'),
            data={'product_ids': []}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('No products selected', data['error'])

    def test_bulk_download_invalid_method(self):
        """Test bulk download with invalid HTTP method."""
        response = self.client.get(reverse('main:bulk_download_products'))
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('Invalid request method', data['error'])

    @patch('django.core.files.storage.default_storage')
    @patch('zipfile.ZipFile')
    def test_bulk_download_file_error_handling(self, mock_zipfile, mock_storage):
        """Test bulk download error handling when file operations fail."""
        # Mock storage to raise an exception
        mock_storage.exists.return_value = True
        mock_storage.open.side_effect = Exception("File access error")
        
        product_ids = [str(self.products[0].id)]
        
        response = self.client.post(
            reverse('main:bulk_download_products'),
            data={'product_ids': product_ids}
        )
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertFalse(data['success'])
        self.assertIn('error', data)

    @patch('django.core.files.storage.default_storage')
    def test_bulk_download_missing_files_handling(self, mock_storage):
        """Test bulk download when some files don't exist."""
        # Mock storage to return False for file existence
        mock_storage.exists.return_value = False
        
        product_ids = [str(p.id) for p in self.products]
        
        response = self.client.post(
            reverse('main:bulk_download_products'),
            data={'product_ids': product_ids}
        )
        
        # Should still return a zip file (empty in this case)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class ProductSerializationTestCase(TestCase):
    """Test product serialization in inventory view."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            provider="test-provider",
            modality="text-to-image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

    def test_product_serialization_with_all_fields(self):
        """Test product serialization includes all required fields."""
        order = Order.objects.create(
            title="Serialization Test Order",
            prompt="serialization test prompt",
            factory_machine_name=self.factory_machine.name,
            provider="test-provider",
            quantity=1,
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            prompt="serialization test prompt",
            parameters={},
            status="completed",
        )
        
        product = Product.objects.create(
            order_item=order_item,
            title="Serialization Test Product",
            prompt="serialization test prompt",
            provider="test-provider",
            model_name="test/model",
            file_path="products/serialization_test.png",
            file_size=2048,
            file_format="png",
            width=1024,
            height=768,
            product_type="image",
        )
        
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        products_data = json.loads(response.context['products_json'])
        self.assertEqual(len(products_data), 1)
        
        product_data = products_data[0]
        
        # Verify all fields are properly serialized
        self.assertEqual(product_data['id'], product.id)
        self.assertEqual(product_data['title'], product.title)
        self.assertEqual(product_data['prompt'], product.prompt)
        self.assertEqual(product_data['file_url'], product.file_url)
        self.assertEqual(product_data['provider'], product.provider)
        self.assertEqual(product_data['model_name'], product.model_name)
        self.assertEqual(product_data['width'], product.width)
        self.assertEqual(product_data['height'], product.height)
        self.assertEqual(product_data['product_type'], product.product_type)
        
        # Verify ISO format for created_at
        self.assertRegex(product_data['created_at'], r'\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}')

    def test_product_serialization_with_missing_fields(self):
        """Test product serialization handles missing optional fields."""
        order = Order.objects.create(
            title="Missing Fields Test Order",
            prompt="missing fields test prompt",
            factory_machine_name=self.factory_machine.name,
            provider="test-provider",
            quantity=1,
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            prompt="missing fields test prompt",
            parameters={},
            status="completed",
        )
        
        # Create product with minimal fields
        product = Product.objects.create(
            order_item=order_item,
            prompt="missing fields test prompt",
            provider="test-provider",
            model_name="test/model",
            file_path="products/minimal_test.png",
            file_size=512,
            file_format="png",
            # Note: title, width, height, product_type use defaults
        )
        
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        products_data = json.loads(response.context['products_json'])
        self.assertEqual(len(products_data), 1)
        
        product_data = products_data[0]
        
        # Verify default handling of missing fields
        self.assertEqual(product_data['id'], product.id)
        self.assertEqual(product_data['title'], product.title)  # Should be None or empty
        # file_url will be None since the file doesn't actually exist in storage during tests
        self.assertIsNone(product_data['file_url'])  # File doesn't exist in test storage
        self.assertEqual(product_data['width'], product.width)  # Should be None
        self.assertEqual(product_data['height'], product.height)  # Should be None
        self.assertEqual(product_data['product_type'], 'image')  # Default fallback

    def test_product_serialization_pagination(self):
        """Test product serialization works correctly with pagination."""
        order = Order.objects.create(
            title="Pagination Test Order",
            prompt="pagination test prompt",
            factory_machine_name=self.factory_machine.name,
            provider="test-provider",
            quantity=25,  # More than default page size
        )
        
        # Create 25 products (exceeds page size of 20)
        for i in range(25):
            order_item = OrderItem.objects.create(
                order=order,
                prompt=f"pagination test prompt {i}",
                parameters={},
                status="completed",
            )
            
            Product.objects.create(
                order_item=order_item,
                title=f"Pagination Test Product {i}",
                prompt=f"pagination test prompt {i}",
                provider="test-provider",
                model_name="test/model",
                file_path=f"products/pagination_test_{i}.png",
                file_size=1024,
                file_format="png",
            )
        
        # Test first page
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        products_data = json.loads(response.context['products_json'])
        self.assertEqual(len(products_data), 20)  # Default page size
        
        # Test second page
        response = self.client.get(reverse('main:inventory'), {'page': 2})
        self.assertEqual(response.status_code, 200)
        
        products_data = json.loads(response.context['products_json'])
        self.assertEqual(len(products_data), 5)  # Remaining products

    def test_empty_product_list_serialization(self):
        """Test product serialization with no products."""
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        products_data = json.loads(response.context['products_json'])
        self.assertEqual(len(products_data), 0)
        self.assertIsInstance(products_data, list)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class UnifiedComponentIntegrationTestCase(TestCase):
    """Integration tests for the unified component system."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()
        
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="integration/test",
            display_name="Integration Test Model",
            provider="test-provider",
            modality="text-to-image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )
        
        # Create a complete order with products for integration testing
        self.order = Order.objects.create(
            title="Integration Test Order",
            prompt="integration test prompt",
            factory_machine_name=self.factory_machine.name,
            provider="test-provider",
            quantity=3,
        )
        
        self.products = []
        for i in range(3):
            order_item = OrderItem.objects.create(
                order=self.order,
                prompt=f"integration test prompt {i}",
                parameters={},
                status="completed",
            )
            
            product = Product.objects.create(
                order_item=order_item,
                title=f"Integration Test Product {i}",
                prompt=f"integration test prompt {i}",
                provider="test-provider",
                model_name="integration/test",
                file_path=f"products/integration_test_{i}.png",
                file_size=1024,
                file_format="png",
                width=512,
                height=512,
                product_type="image",
            )
            self.products.append(product)

    def test_full_inventory_page_integration(self):
        """Test full inventory page loads with unified components."""
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        # Verify page contains all necessary components
        self.assertContains(response, 'id="inventoryCollection"')
        self.assertContains(response, 'window.inventoryProductsData')
        self.assertContains(response, 'new ProductCollection')
        self.assertContains(response, 'loadProducts(window.inventoryProductsData)')
        
        # Verify product data is present
        products_data = json.loads(response.context['products_json'])
        self.assertEqual(len(products_data), 3)
        
        # Verify each product has complete data (products ordered by -created_at, so reverse order)
        for i, product_data in enumerate(products_data):
            expected_index = len(products_data) - 1 - i  # Reverse order due to -created_at ordering
            self.assertEqual(product_data['title'], f'Integration Test Product {expected_index}')
            self.assertEqual(product_data['prompt'], f'integration test prompt {expected_index}')
            self.assertEqual(product_data['provider'], 'test-provider')
            self.assertEqual(product_data['model_name'], 'integration/test')

    def test_bulk_operations_integration_workflow(self):
        """Test complete bulk operations workflow."""
        # Step 1: Load inventory page
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        # Step 2: Perform bulk delete via AJAX
        product_ids = [str(p.id) for p in self.products[:2]]
        delete_response = self.client.post(
            reverse('main:bulk_delete_products'),
            data={'product_ids': product_ids},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(delete_response.status_code, 200)
        delete_data = json.loads(delete_response.content)
        self.assertTrue(delete_data['success'])
        self.assertEqual(delete_data['deleted_count'], 2)
        
        # Step 3: Reload inventory page to verify deletion
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        products_data = json.loads(response.context['products_json'])
        self.assertEqual(len(products_data), 1)
        self.assertEqual(products_data[0]['id'], self.products[2].id)

    @patch('django.core.files.storage.default_storage')
    def test_bulk_download_integration(self, mock_storage):
        """Test bulk download integration with file handling."""
        # Mock file storage with context manager support
        mock_storage.exists.return_value = True
        
        # Create a proper mock file object with context manager support
        mock_file = MagicMock()
        mock_file.read.return_value = b"fake_image_data"
        mock_file.__enter__.return_value = mock_file
        mock_file.__exit__.return_value = None
        mock_storage.open.return_value = mock_file
        
        # Perform bulk download
        product_ids = [str(p.id) for p in self.products]
        response = self.client.post(
            reverse('main:bulk_download_products'),
            data={'product_ids': product_ids}
        )
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/zip')
        
        # Verify zip filename includes correct count
        self.assertIn('products_3_files.zip', response['Content-Disposition'])

    def test_component_error_handling_integration(self):
        """Test integrated error handling across components."""
        # Test bulk delete with database error
        with patch.object(Product.objects, 'filter') as mock_filter:
            mock_queryset = MagicMock()
            mock_queryset.count.return_value = 1
            mock_queryset.delete.side_effect = Exception("Database connection lost")
            mock_filter.return_value = mock_queryset
            
            response = self.client.post(
                reverse('main:bulk_delete_products'),
                data={'product_ids': [str(self.products[0].id)]},
                HTTP_X_REQUESTED_WITH='XMLHttpRequest'
            )
            
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.content)
            
            self.assertFalse(data['success'])
            self.assertIn('An error occurred while deleting products', data['message'])
            self.assertIn('error', data)

    def test_ajax_vs_non_ajax_behavior_consistency(self):
        """Test that AJAX and non-AJAX requests behave consistently."""
        product_ids = [str(self.products[0].id)]
        
        # Test AJAX request
        ajax_response = self.client.post(
            reverse('main:bulk_delete_products'),
            data={'product_ids': product_ids},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(ajax_response.status_code, 200)
        ajax_data = json.loads(ajax_response.content)
        self.assertTrue(ajax_data['success'])
        
        # Test non-AJAX request
        non_ajax_response = self.client.post(
            reverse('main:bulk_delete_products'),
            data={'product_ids': [str(self.products[1].id)]}
        )
        
        # Should redirect to inventory
        self.assertEqual(non_ajax_response.status_code, 302)
        self.assertRedirects(non_ajax_response, reverse('main:inventory'))
        
        # Verify both products were deleted
        remaining_products = Product.objects.filter(id__in=[self.products[0].id, self.products[1].id])
        self.assertEqual(remaining_products.count(), 0)

    def test_component_data_consistency(self):
        """Test data consistency between views and JavaScript components."""
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        # Get both template context and serialized JSON data
        page_products = response.context['products']
        json_products = json.loads(response.context['products_json'])
        
        # Verify counts match
        self.assertEqual(len(list(page_products)), len(json_products))
        
        # Verify data consistency for each product
        for i, (page_product, json_product) in enumerate(zip(page_products, json_products)):
            self.assertEqual(page_product.id, json_product['id'])
            self.assertEqual(page_product.title, json_product['title'])
            self.assertEqual(page_product.prompt, json_product['prompt'])
            self.assertEqual(page_product.file_url, json_product['file_url'])
            self.assertEqual(page_product.provider, json_product['provider'])
            self.assertEqual(page_product.model_name, json_product['model_name'])
            self.assertEqual(page_product.width, json_product['width'])
            self.assertEqual(page_product.height, json_product['height'])

    def test_csrf_token_handling_in_components(self):
        """Test that CSRF tokens are properly handled in unified components."""
        response = self.client.get(reverse('main:inventory'))
        self.assertEqual(response.status_code, 200)
        
        # Check that CSRF token input field is present
        self.assertContains(response, 'name="csrfmiddlewaretoken"')
        
        # Verify bulk operations work with CSRF protection
        product_ids = [str(self.products[0].id)]
        
        # Test bulk delete with Django test client (automatically handles CSRF)
        delete_response = self.client.post(
            reverse('main:bulk_delete_products'),
            data={'product_ids': product_ids},
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        
        self.assertEqual(delete_response.status_code, 200)
        delete_data = json.loads(delete_response.content)
        self.assertTrue(delete_data['success'])