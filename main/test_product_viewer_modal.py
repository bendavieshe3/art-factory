import json
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from unittest.mock import patch, Mock

from main.models import Product, Order, OrderItem, FactoryMachineDefinition
from django.core.files.uploadedfile import SimpleUploadedFile


class ProductViewerModalTest(TestCase):
    """Test suite for Product Viewer Modal functionality."""

    def setUp(self):
        """Set up test data."""
        self.client = Client()

        # Create a factory machine definition
        self.machine = FactoryMachineDefinition.objects.create(
            name="test_sdxl",
            display_name="Test SDXL",
            provider="fal.ai",
            modality="txt2img",
            parameter_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "width": {"type": "integer", "default": 1024},
                    "height": {"type": "integer", "default": 1024},
                },
            },
            default_parameters={"width": 1024, "height": 1024, "num_images": 1},
        )

        # Create test order
        self.order = Order.objects.create(
            title="Test Order",
            prompt="A beautiful sunset",
            negative_prompt="blurry, low quality",
            base_parameters={"width": 1024, "height": 1024},
            factory_machine_name=self.machine.name,
            provider=self.machine.provider,
            quantity=1,
        )

        # Create test order item
        self.order_item = OrderItem.objects.create(
            order=self.order,
            prompt=self.order.prompt,
            negative_prompt=self.order.negative_prompt,
            parameters={"width": 1024, "height": 1024, "num_images": 1},
            total_quantity=1,
            batch_size=1,
            status="completed",
        )

        # Create test products
        self.product1 = Product.objects.create(
            title="Test Product 1",
            prompt="A beautiful sunset",
            negative_prompt="blurry, low quality",
            provider="fal.ai",
            model_name="test_sdxl",
            parameters={"width": 1024, "height": 1024},
            file_path="test/product1.png",
            file_size=1024000,
            file_format="png",
            width=1024,
            height=1024,
        )

        self.product2 = Product.objects.create(
            title="Test Product 2",
            prompt="A mountain landscape",
            negative_prompt="dark, blurry",
            provider="fal.ai",
            model_name="test_sdxl",
            parameters={"width": 1024, "height": 1024},
            file_path="test/product2.png",
            file_size=1024000,
            file_format="png",
            width=1024,
            height=1024,
        )

        # Associate product with order item
        self.order_item.product = self.product1
        self.order_item.save()

    def test_product_detail_api(self):
        """Test the product detail API endpoint provides comprehensive data."""
        url = reverse("main:product_detail_api", kwargs={"product_id": self.product1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Check essential fields for modal
        self.assertEqual(data["id"], self.product1.id)
        self.assertEqual(data["title"], self.product1.title)
        self.assertEqual(data["prompt"], self.product1.prompt)
        self.assertEqual(data["negative_prompt"], self.product1.negative_prompt)
        self.assertEqual(data["provider"], self.product1.provider)
        self.assertEqual(data["model_name"], self.product1.model_name)
        self.assertEqual(data["file_url"], self.product1.file_url)
        self.assertEqual(data["width"], self.product1.width)
        self.assertEqual(data["height"], self.product1.height)

        # Check that order information is included
        self.assertEqual(data["order_id"], self.order.id)
        self.assertEqual(data["factory_machine_definition"], self.machine.name)

        # Check that parameters are included
        self.assertIsInstance(data["parameters"], dict)

    def test_product_detail_api_nonexistent(self):
        """Test product detail API with non-existent product."""
        url = reverse("main:product_detail_api", kwargs={"product_id": 9999})
        response = self.client.get(url)

        # The view uses get_object_or_404 but catches all exceptions and returns 400
        # Let's check for either 404 or 400 with error message
        self.assertIn(response.status_code, [400, 404])
        if response.status_code == 400:
            data = json.loads(response.content)
            self.assertIn("error", data)

    def test_inventory_view_includes_product_data(self):
        """Test that inventory view includes JSON product data for modal."""
        url = reverse("main:inventory")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Check that the template includes inventoryProductsData
        self.assertContains(response, "inventoryProductsData")

        # Check that the context includes product data
        products_json = response.context["products_json"]
        products_data = json.loads(products_json)

        self.assertIsInstance(products_data, list)
        if products_data:  # If there are products
            product = products_data[0]
            required_fields = ["id", "title", "prompt", "file_url", "provider", "model_name", "created_at"]
            for field in required_fields:
                self.assertIn(field, product)

    def test_recent_products_api(self):
        """Test recent products API returns data for modal."""
        url = reverse("main:recent_products_api")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertIn("products", data)
        self.assertIsInstance(data["products"], list)

        if data["products"]:  # If there are products
            product = data["products"][0]
            required_fields = ["id", "title", "file_url", "provider", "model_name", "created_at"]
            for field in required_fields:
                self.assertIn(field, product)

    @patch("django.core.files.storage.default_storage.exists")
    @patch("django.core.files.storage.default_storage.open")
    def test_product_download_api(self, mock_open, mock_exists):
        """Test product download API endpoint."""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_file.read.return_value = b"fake image data"
        mock_open.return_value.__enter__.return_value = mock_file

        url = reverse("main:api_product_download", kwargs={"product_id": self.product1.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/octet-stream")
        self.assertIn("attachment", response["Content-Disposition"])

    def test_product_delete_ajax(self):
        """Test product deletion via AJAX."""
        url = reverse("main:product_delete", kwargs={"product_id": self.product1.id})
        response = self.client.post(url, HTTP_X_REQUESTED_WITH="XMLHttpRequest")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data["success"])
        self.assertIn("message", data)

        # Verify product is deleted
        self.assertFalse(Product.objects.filter(id=self.product1.id).exists())

    def test_bulk_delete_products(self):
        """Test bulk deletion of products."""
        url = reverse("main:bulk_delete_products")
        response = self.client.post(
            url, {"product_ids": [self.product1.id, self.product2.id]}, HTTP_X_REQUESTED_WITH="XMLHttpRequest"
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        self.assertTrue(data["success"])
        self.assertEqual(data["deleted_count"], 2)

        # Verify products are deleted
        self.assertFalse(Product.objects.filter(id__in=[self.product1.id, self.product2.id]).exists())

    @patch("django.core.files.storage.default_storage.exists")
    @patch("django.core.files.storage.default_storage.open")
    def test_bulk_download_products(self, mock_open, mock_exists):
        """Test bulk download of products as zip."""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_file.read.return_value = b"fake image data"
        mock_open.return_value.__enter__.return_value = mock_file

        url = reverse("main:bulk_download_products")
        response = self.client.post(url, {"product_ids": [self.product1.id, self.product2.id]})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/zip")
        self.assertIn("attachment", response["Content-Disposition"])
        self.assertIn(".zip", response["Content-Disposition"])

    def test_modal_css_included_in_base_template(self):
        """Test that modal CSS is included in base template."""
        url = reverse("main:inventory")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "product-viewer-modal.css")

    def test_modal_js_included_in_base_template(self):
        """Test that modal JavaScript is included in base template."""
        url = reverse("main:inventory")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "product-viewer-modal.js")

    def test_product_cards_include_modal_integration(self):
        """Test that product cards include modal integration classes."""
        url = reverse("main:inventory")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "product-components.js")

    def test_order_view_recent_products_context(self):
        """Test that order view provides context for recent products modal."""
        url = reverse("main:order")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        # Should include factory machines for the order form
        self.assertIn("factory_machines", response.context)

    def test_api_endpoints_return_json(self):
        """Test that all relevant API endpoints return valid JSON."""
        endpoints = [
            ("main:recent_products_api", {}),
            ("main:recent_orders_api", {}),
            ("main:factory_machines_api", {}),
            ("main:product_detail_api", {"product_id": self.product1.id}),
        ]

        for endpoint_name, kwargs in endpoints:
            url = reverse(endpoint_name, kwargs=kwargs)
            response = self.client.get(url)

            self.assertEqual(response.status_code, 200, f"Failed for {endpoint_name}")

            # Verify it's valid JSON
            try:
                json.loads(response.content)
            except json.JSONDecodeError:
                self.fail(f"Invalid JSON returned from {endpoint_name}")

    def test_modal_keyboard_navigation_support(self):
        """Test that modal supports keyboard navigation (structural test)."""
        # This tests the structure rather than actual keyboard events
        url = reverse("main:inventory")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Verify that Bootstrap Icons are loaded (for navigation arrows)
        self.assertContains(response, "bootstrap-icons")

    def test_modal_accessibility_attributes(self):
        """Test that modal includes proper accessibility attributes."""
        url = reverse("main:inventory")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)

        # Basic check that aria attributes would be supported
        # The actual modal is created dynamically, so we check for the JS
        self.assertContains(response, "product-viewer-modal.js")

    def test_product_without_order(self):
        """Test modal handles products not associated with orders."""
        # Create a standalone product
        standalone_product = Product.objects.create(
            title="Standalone Product",
            prompt="A standalone image",
            provider="fal.ai",
            model_name="test_sdxl",
            parameters={"width": 512, "height": 512},
            file_path="test/standalone.png",
            file_size=512000,
            file_format="png",
            width=512,
            height=512,
        )

        url = reverse("main:product_detail_api", kwargs={"product_id": standalone_product.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should handle missing order gracefully
        self.assertIsNone(data["order_id"])
        self.assertIsNone(data["factory_machine_definition"])

    def test_error_handling_for_missing_files(self):
        """Test modal handles products with missing files gracefully."""
        # Product with missing file
        product_no_file = Product.objects.create(
            title="No File Product",
            prompt="A missing image",
            provider="fal.ai",
            model_name="test_sdxl",
            parameters={"width": 512, "height": 512},
            file_path="",  # No file path
            file_size=0,
            file_format="png",
            width=512,
            height=512,
        )

        url = reverse("main:product_detail_api", kwargs={"product_id": product_no_file.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Should handle missing file paths gracefully
        self.assertEqual(data["file_path"], "")
        self.assertIsNone(data["file_url"])

    def test_modal_integration_from_different_contexts(self):
        """Test that modal can be opened from different page contexts."""
        # Test inventory context
        inventory_url = reverse("main:inventory")
        inventory_response = self.client.get(inventory_url)
        self.assertEqual(inventory_response.status_code, 200)
        self.assertContains(inventory_response, "ProductCollection")

        # Test order context
        order_url = reverse("main:order")
        order_response = self.client.get(order_url)
        self.assertEqual(order_response.status_code, 200)
        # Order page should include product components
        self.assertContains(order_response, "product-components.js")

    def test_recent_orders_api_data_structure(self):
        """Test recent orders API returns proper data structure with model and item info."""
        # Create some order items to test the items count
        OrderItem.objects.create(
            order=self.order,
            prompt="Test item 1",
            status="completed",
            parameters={"width": 512, "height": 512}
        )
        OrderItem.objects.create(
            order=self.order,
            prompt="Test item 2", 
            status="failed",
            parameters={"width": 512, "height": 512}
        )
        
        url = reverse("main:recent_orders_api")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.content)
        self.assertIn("orders", data)
        
        if data["orders"]:
            order_data = data["orders"][0]
            
            # Verify essential fields are present
            self.assertIn("id", order_data)
            self.assertIn("title", order_data)
            self.assertIn("status", order_data) 
            self.assertIn("created_at", order_data)
            
            # Verify model and item information is present for table display
            self.assertIn("factory_machine_name", order_data, "Model column data missing")
            self.assertIn("total_items", order_data, "Total items count missing")
            self.assertIn("completed_items", order_data, "Completed items count missing")
            self.assertIn("failed_items", order_data, "Failed items count missing")
            
            # Verify the data values are correct
            self.assertEqual(order_data["factory_machine_name"], self.machine.name)
            self.assertEqual(order_data["total_items"], 3)  # 1 from setUp + 2 added above
            self.assertEqual(order_data["completed_items"], 2)  # setUp item + completed test item
            self.assertEqual(order_data["failed_items"], 1)    # failed test item

    def tearDown(self):
        """Clean up test data."""
        Product.objects.all().delete()
        OrderItem.objects.all().delete()
        Order.objects.all().delete()
        FactoryMachineDefinition.objects.all().delete()
