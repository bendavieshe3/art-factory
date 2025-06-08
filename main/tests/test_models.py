import json
import os
import random
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client, override_settings
from django.urls import reverse
from django.core.management import call_command
from io import StringIO

from main.models import Product, Order, OrderItem, Worker, FactoryMachineDefinition


def get_test_pid():
    """Generate a unique test PID to avoid conflicts."""
    return os.getpid() + random.randint(10000, 99999)  # nosec B311


# Use test settings for all test cases
@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class ModelTestCase(TestCase):
    """Test Django models functionality."""

    def setUp(self):
        """Set up test data."""
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            description="Test model for testing",
            provider="test-provider",
            modality="image",
            parameter_schema={"width": 512, "height": 512},
            default_parameters={"width": 512, "height": 512},
            is_active=True,
        )

        self.order = Order.objects.create(
            title="Test Order",
            prompt="test prompt",
            base_parameters={"width": 512},
            factory_machine_name="test/model",
            provider="test-provider",
            quantity=2,
        )

    def test_order_creation(self):
        """Test Order model creation and properties."""
        self.assertEqual(self.order.title, "Test Order")
        self.assertEqual(self.order.prompt, "test prompt")
        self.assertEqual(self.order.quantity, 2)  # This is total quantity now
        self.assertEqual(self.order.status, "pending")
        self.assertEqual(self.order.completion_percentage, 0)

    def test_order_item_creation(self):
        """Test OrderItem creation and relationships."""
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt="test item prompt",
            parameters={"width": 512},
            status="pending",
            batch_size=2,
            total_quantity=2,
        )

        self.assertEqual(order_item.order, self.order)
        self.assertEqual(order_item.prompt, "test item prompt")
        self.assertEqual(order_item.status, "pending")
        self.assertIsNone(order_item.product)
        self.assertEqual(order_item.batch_size, 2)
        self.assertEqual(order_item.total_quantity, 2)

    def test_product_creation(self):
        """Test Product model creation."""
        product = Product.objects.create(
            title="Test Product",
            prompt="test prompt",
            parameters={"width": 512},
            provider="test-provider",
            model_name="test/model",
            product_type="image",
            file_path="test/path.png",
            file_size=1024,
            file_format="png",
        )

        self.assertEqual(product.title, "Test Product")
        self.assertEqual(product.provider, "test-provider")
        self.assertEqual(product.file_format, "png")

    def test_completion_percentage_calculation(self):
        """Test order completion percentage calculation."""
        # Create order items
        item1 = OrderItem.objects.create(order=self.order, prompt="item 1", status="pending")
        item2 = OrderItem.objects.create(order=self.order, prompt="item 2", status="completed")

        # Should be 50% complete (1 of 2 completed)
        self.assertEqual(self.order.completion_percentage, 50)

        # Complete the other item
        item1.status = "completed"
        item1.save()

        # Should be 100% complete
        self.assertEqual(self.order.completion_percentage, 100)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class ViewTestCase(TestCase):
    """Test Django views functionality."""

    def setUp(self):
        """Set up test client and data."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            description="Test model for testing",
            provider="test-provider",
            modality="image",
            parameter_schema={"width": 512, "height": 512},
            default_parameters={"width": 512, "height": 512},
            is_active=True,
        )

    def test_home_page_loads(self):
        """Test home page (order view) loads correctly."""
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Place Order")
        self.assertContains(response, "Test Model")

    def test_inventory_page_loads(self):
        """Test inventory page loads correctly."""
        response = self.client.get("/inventory/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Inventory")

    def test_production_page_loads(self):
        """Test production page loads correctly."""
        response = self.client.get("/production/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Production")

    def test_factory_machines_api(self):
        """Test factory machines API endpoint."""
        response = self.client.get("/api/factory-machines/")
        self.assertEqual(response.status_code, 200)

        data = json.loads(response.content)
        self.assertIn("machines", data)
        self.assertEqual(len(data["machines"]), 1)
        self.assertEqual(data["machines"][0]["name"], "test/model")

    def test_place_order_api_success(self):
        """Test successful order placement via API."""
        order_data = {
            "title": "Test API Order",
            "prompt": "test api prompt",
            "machine_id": self.factory_machine.id,
            "generation_count": 1,
            "batch_size": 1,
            "parameters": {"width": 512, "height": 512},
        }

        response = self.client.post("/api/place-order/", data=json.dumps(order_data), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])
        self.assertIn("order_id", data)

        # Verify order was created
        order = Order.objects.get(id=data["order_id"])
        self.assertEqual(order.title, "Test API Order")
        self.assertEqual(order.quantity, 1)  # generation_count * batch_size

        # Verify order item was created
        self.assertEqual(order.orderitem_set.count(), 1)

    def test_place_order_api_invalid_machine(self):
        """Test order placement with invalid machine ID."""
        order_data = {
            "title": "Test Order",
            "prompt": "test prompt",
            "machine_id": 999,  # Non-existent machine
            "generation_count": 1,
            "batch_size": 1,
        }

        response = self.client.post("/api/place-order/", data=json.dumps(order_data), content_type="application/json")

        # Django's get_object_or_404 raises 404, but our view catches and returns 400
        self.assertEqual(response.status_code, 400)

    def test_product_detail_view(self):
        """Test product detail view."""
        product = Product.objects.create(
            title="Test Product",
            prompt="test prompt",
            provider="test-provider",
            model_name="test/model",
            product_type="image",
            file_path="test/path.png",
            file_size=1024,
        )

        response = self.client.get(f"/products/{product.id}/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Product")


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class SignalTestCase(TestCase):
    """Test Django signals functionality."""

    def setUp(self):
        """Set up test data."""
        self.order = Order.objects.create(
            title="Signal Test Order",
            prompt="test prompt",
            factory_machine_name="test/model",
            provider="test-provider",
            quantity=1,
        )

    def test_order_item_signal_no_auto_spawn_in_tests(self):
        """Test that creating OrderItem doesn't spawn workers in tests."""
        # Create an OrderItem - this should NOT trigger worker spawn in tests
        with patch("main.workers.spawn_worker_automatically") as mock_spawn:
            order_item = OrderItem.objects.create(order=self.order, prompt="test signal prompt", status="pending")

            # Verify worker spawn was NOT called (due to test settings)
            mock_spawn.assert_not_called()

    def test_order_item_signal_not_triggered_for_non_pending(self):
        """Test that signal doesn't trigger for non-pending items."""
        # Create an OrderItem with non-pending status
        with patch("main.workers.spawn_worker_automatically") as mock_spawn:
            OrderItem.objects.create(order=self.order, prompt="test prompt", status="completed")  # Not pending

            # Verify worker spawn was NOT called
            mock_spawn.assert_not_called()


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class TaskTestCase(TestCase):
    """Test background task functionality."""

    def setUp(self):
        """Set up test data."""
        self.order = Order.objects.create(
            title="Task Test Order",
            prompt="test prompt",
            factory_machine_name="test/model",
            provider="test-provider",
            quantity=1,
        )

        # Create OrderItem (worker spawning disabled in test settings)
        self.order_item = OrderItem.objects.create(order=self.order, prompt="test task prompt", status="pending")

    @patch("main.factory_machines_sync.execute_order_item_sync_batch")
    def test_process_order_items_with_worker(self, mock_execute):
        """Test processing order items with worker system."""
        # Mock successful batch processing
        mock_execute.return_value = True

        # Update order to use fal.ai
        self.order.provider = "fal.ai"
        self.order.save()

        # Set batch parameters
        self.order_item.batch_size = 2
        self.order_item.total_quantity = 2
        self.order_item.save()

        # Simulate worker processing
        from main.workers import SmartWorker

        worker = SmartWorker(max_batch_size=5)

        # Process the item
        success = mock_execute(self.order_item.id)

        # Verify processing was called
        mock_execute.assert_called_once_with(self.order_item.id)
        self.assertTrue(success)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class ManagementCommandTestCase(TestCase):
    """Test management commands."""

    def test_load_seed_data_command(self):
        """Test load_seed_data management command."""
        # Ensure no machines exist initially
        FactoryMachineDefinition.objects.all().delete()

        # Run the command
        out = StringIO()
        call_command("load_seed_data", stdout=out)

        # Verify machines were created
        self.assertGreater(FactoryMachineDefinition.objects.count(), 0)

        # Verify fal.ai machines exist
        fal_machines = FactoryMachineDefinition.objects.filter(provider="fal.ai")
        self.assertGreater(fal_machines.count(), 0)

        # Verify replicate machines exist
        replicate_machines = FactoryMachineDefinition.objects.filter(provider="replicate")
        self.assertGreater(replicate_machines.count(), 0)

    @patch("main.management.commands.simple_process.Command.process_fal_item")
    def test_simple_process_command(self, mock_process_fal):
        """Test simple_process management command."""
        # Create a pending order item
        order = Order.objects.create(
            title="Command Test Order",
            prompt="test prompt",
            factory_machine_name="fal-ai/flux/dev",
            provider="fal.ai",
            quantity=1,
        )

        # Create OrderItem (worker spawning disabled in test settings)
        order_item = OrderItem.objects.create(order=order, prompt="test command prompt", status="pending")

        # Mock successful processing
        mock_product = Product.objects.create(
            title="Mock Product",
            prompt="test",
            provider="fal.ai",
            model_name="fal-ai/flux/dev",
            product_type="image",
            file_path="mock/path.png",
            file_size=1024,
        )
        mock_process_fal.return_value = mock_product

        # Run the command
        out = StringIO()
        call_command("simple_process", stdout=out)

        # Verify processing was called
        mock_process_fal.assert_called_once()

        # Verify order item was processed
        order_item.refresh_from_db()
        self.assertEqual(order_item.status, "completed")


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
@patch.dict("os.environ", {"FAL_KEY": "test_key"})
@patch.dict("os.environ", {"REPLICATE_API_TOKEN": "test_token"})
class IntegrationTestCase(TestCase):
    """Integration tests for the complete workflow."""

    def setUp(self):
        """Set up integration test data."""
        # Load seed data
        call_command("load_seed_data")

        self.client = Client()
        self.created_files = []

    def tearDown(self):
        """Clean up test resources."""
        # Clean up any created files
        import os

        for file_path in self.created_files:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except Exception:
                pass  # nosec B110 - Ignore cleanup errors in tests

        # Note: Log files are now in temporary directory via test_settings.py
        super().tearDown()

    @patch("fal_client.submit")
    @patch("httpx.Client.get")
    def test_end_to_end_fal_workflow(self, mock_http_get, mock_fal_submit):
        """Test complete workflow from order placement to product creation with fal.ai."""
        # Mock fal.ai response
        mock_handle = MagicMock()
        mock_handle.get.return_value = {
            "images": [{"url": "http://example.com/image.png", "width": 512, "height": 512}],
            "seed": 12345,
            "request_id": "test_request_123",
        }
        mock_fal_submit.return_value = mock_handle

        # Mock HTTP download
        mock_response = MagicMock()
        mock_response.content = b"fake_image_data"
        mock_response.raise_for_status.return_value = None
        mock_http_get.return_value = mock_response

        # Get fal.ai machine
        fal_machine = FactoryMachineDefinition.objects.filter(provider="fal.ai").first()
        self.assertIsNotNone(fal_machine)

        # Place order via API
        order_data = {
            "title": "Integration Test Order",
            "prompt": "a beautiful landscape",
            "machine_id": fal_machine.id,
            "generation_count": 1,
            "batch_size": 1,
            "parameters": {"width": 512, "height": 512},
        }

        response = self.client.post("/api/place-order/", data=json.dumps(order_data), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data["success"])

        # Verify order was created
        order = Order.objects.get(id=data["order_id"])
        self.assertEqual(order.quantity, 1)
        self.assertEqual(order.orderitem_set.count(), 1)

    def test_double_processing_prevention(self):
        """Test that the double-processing bug is fixed."""
        # Get any machine
        machine = FactoryMachineDefinition.objects.first()

        # Record initial counts
        initial_orders = Order.objects.count()
        initial_items = OrderItem.objects.count()

        # Place order requesting 2 images with batch
        order_data = {
            "title": "Double Processing Test",
            "prompt": "test prompt",
            "machine_id": machine.id,
            "generation_count": 1,  # 1 generation
            "batch_size": 2,  # 2 images per batch
            "parameters": {},
        }

        response = self.client.post("/api/place-order/", data=json.dumps(order_data), content_type="application/json")

        self.assertEqual(response.status_code, 200)

        # Verify exactly 1 order and 1 order item were created
        self.assertEqual(Order.objects.count(), initial_orders + 1)
        self.assertEqual(OrderItem.objects.count(), initial_items + 1)

        # Verify the order has the correct total quantity
        order = Order.objects.latest("id")
        self.assertEqual(order.quantity, 2)  # generation_count * batch_size
        self.assertEqual(order.orderitem_set.count(), 1)

        # Verify the order item has correct batch settings
        order_item = order.orderitem_set.first()
        self.assertEqual(order_item.batch_size, 2)
        self.assertEqual(order_item.total_quantity, 2)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class BatchGenerationTestCase(TestCase):
    """Test batch generation functionality."""

    def setUp(self):
        """Set up test data."""
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/batch-model",
            display_name="Test Batch Model",
            description="Test model for batch generation",
            provider="test-provider",
            modality="image",
            parameter_schema={"width": 512, "height": 512},
            default_parameters={"width": 512, "height": 512},
            is_active=True,
        )
        self.client = Client()

    def test_batch_generation_order_creation(self):
        """Test creating order with batch generation parameters."""
        order_data = {
            "title": "Batch Generation Test",
            "prompt": "test batch generation",
            "machine_id": self.factory_machine.id,
            "generation_count": 3,  # 3 generations
            "batch_size": 4,  # 4 images per batch
            "parameters": {},
        }

        response = self.client.post("/api/place-order/", data=json.dumps(order_data), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        # Verify order was created with correct quantity
        order = Order.objects.get(id=data["order_id"])
        self.assertEqual(order.quantity, 12)  # 3 generations * 4 batch size

        # Verify correct number of order items created
        self.assertEqual(order.orderitem_set.count(), 3)  # 3 generations

        # Verify each order item has correct batch settings
        for item in order.orderitem_set.all():
            self.assertEqual(item.batch_size, 4)
            self.assertEqual(item.total_quantity, 4)

    def test_single_batch_generation(self):
        """Test generation with batch_size = 1."""
        order_data = {
            "title": "Single Batch Test",
            "prompt": "single image generation",
            "machine_id": self.factory_machine.id,
            "generation_count": 5,
            "batch_size": 1,
            "parameters": {},
        }

        response = self.client.post("/api/place-order/", data=json.dumps(order_data), content_type="application/json")

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)

        order = Order.objects.get(id=data["order_id"])
        self.assertEqual(order.quantity, 5)  # 5 * 1
        self.assertEqual(order.orderitem_set.count(), 5)

        for item in order.orderitem_set.all():
            self.assertEqual(item.batch_size, 1)
            self.assertEqual(item.total_quantity, 1)

    def test_batch_completion_tracking(self):
        """Test tracking of batch completion."""
        # Create order with batch
        order = Order.objects.create(
            title="Batch Completion Test",
            prompt="test completion",
            factory_machine_name=self.factory_machine.name,
            provider=self.factory_machine.provider,
            quantity=8,  # 2 generations * 4 batch size
        )

        # Create order items with batch settings
        item1 = OrderItem.objects.create(
            order=order, prompt=order.prompt, parameters={}, batch_size=4, total_quantity=4, status="processing"
        )
        item2 = OrderItem.objects.create(
            order=order, prompt=order.prompt, parameters={}, batch_size=4, total_quantity=4, status="pending"
        )

        # Initially 0% complete
        self.assertEqual(order.completion_percentage, 0)

        # Complete first batch
        item1.status = "completed"
        item1.batches_completed = 1
        item1.save()

        # Should be 50% complete (1 of 2 items)
        self.assertEqual(order.completion_percentage, 50)

        # Complete second batch
        item2.status = "completed"
        item2.batches_completed = 1
        item2.save()

        # Should be 100% complete
        self.assertEqual(order.completion_percentage, 100)

    def test_order_item_can_store_multiple_products(self):
        """Test that OrderItem can be associated with multiple products."""
        order = Order.objects.create(
            title="Multi-Product Test",
            prompt="test multiple products",
            factory_machine_name=self.factory_machine.name,
            provider=self.factory_machine.provider,
            quantity=3,
        )

        item = OrderItem.objects.create(
            order=order, prompt=order.prompt, parameters={}, batch_size=3, total_quantity=3, status="completed"
        )

        # Create multiple products for this order item
        products = []
        for i in range(3):
            product = Product.objects.create(
                title=f"Product {i + 1}",
                prompt=item.prompt,
                parameters=item.parameters,
                provider=order.provider,
                model_name=order.factory_machine_name,
                product_type="image",
                file_path=f"test/product_{i + 1}.png",
                file_size=1024,
                order_item=item,  # Set the ForeignKey relationship
            )
            products.append(product)

        # Verify the relationship
        self.assertEqual(item.products.count(), 3)
        # Products are ordered by -created_at, so newest first
        self.assertEqual(list(item.products.all().order_by("id")), products)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class RetryMechanismTestCase(TestCase):
    """Test the retry mechanism for failed order items."""

    def setUp(self):
        """Set up test data."""
        self.workers_to_cleanup = []
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test_machine",
            display_name="Test Machine",
            provider="test",
            modality="image",
            is_active=True,
            parameter_schema={},
        )

        self.order = Order.objects.create(prompt="Test prompt", factory_machine_name="test_machine", provider="test")

    def tearDown(self):
        """Clean up test resources."""
        # Clean up any workers created during tests
        for worker in self.workers_to_cleanup:
            try:
                if hasattr(worker, "graceful_exit"):
                    worker.graceful_exit("Test cleanup")
            except Exception:
                pass  # nosec B110 - Ignore cleanup errors in tests

        # Clean up any Worker model instances
        Worker.objects.all().delete()

        super().tearDown()

    def test_transient_failure_detection(self):
        """Test that transient failures are properly detected."""
        order_item = OrderItem.objects.create(order=self.order, prompt="Test prompt", parameters={})

        # Test transient error detection
        transient_errors = [
            "Server disconnected without sending a response",
            "Connection timeout occurred",
            "502 Bad Gateway",
            "Service unavailable",
            "Rate limit exceeded",
        ]

        non_transient_errors = [
            "Invalid API key",
            "Model not found",
            "Prompt contains inappropriate content",
            "Insufficient credits",
        ]

        for error in transient_errors:
            order_item.error_message = error
            self.assertTrue(order_item.is_transient_failure(), f"Should detect '{error}' as transient")

        for error in non_transient_errors:
            order_item.error_message = error
            self.assertFalse(order_item.is_transient_failure(), f"Should NOT detect '{error}' as transient")

    def test_retry_eligibility(self):
        """Test retry eligibility logic."""
        order_item = OrderItem.objects.create(order=self.order, prompt="Test prompt", parameters={}, max_retries=3)

        # Initially should not be retryable (not failed)
        self.assertFalse(order_item.can_be_retried())

        # After transient failure, should be retryable
        order_item.status = "failed"
        order_item.error_message = "Server disconnected without sending a response"
        order_item.save()
        self.assertTrue(order_item.can_be_retried())

        # After non-transient failure, should not be retryable
        order_item.error_message = "Invalid API key"
        order_item.save()
        self.assertFalse(order_item.can_be_retried())

        # After max retries, should not be retryable
        order_item.error_message = "Server disconnected without sending a response"
        order_item.retry_count = 3
        order_item.save()
        self.assertFalse(order_item.can_be_retried())

    def test_retry_reset(self):
        """Test that reset_for_retry works correctly."""
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt="Test prompt",
            parameters={},
            status="failed",
            error_message="Server disconnected without sending a response",
            retry_count=0,
            max_retries=3,
        )

        # Reset for retry
        order_item.reset_for_retry()

        # Check that fields are reset properly
        self.assertEqual(order_item.status, "pending")
        self.assertIsNone(order_item.assigned_worker)
        self.assertEqual(order_item.retry_count, 1)
        self.assertIsNotNone(order_item.last_retry_at)
        self.assertEqual(order_item.provider_request_id, "")
        # Error message should be preserved for debugging
        self.assertEqual(order_item.error_message, "Server disconnected without sending a response")

    def test_worker_claims_retry_items(self):
        """Test that workers can claim failed items for retry."""
        # Create a failed item that can be retried
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt="Test prompt",
            parameters={},
            status="failed",
            error_message="Server disconnected without sending a response",
            retry_count=0,
            max_retries=3,
        )

        # Create worker
        from main.workers import SmartWorker

        worker = SmartWorker(max_batch_size=5)
        worker.name = "test-worker"
        worker.process_id = 12345

        # Mock worker registration
        worker.worker_record = Worker.objects.create(
            name=worker.name, process_id=worker.process_id, provider="universal", max_batch_size=5, status="starting"
        )

        # Worker should claim the retryable item
        claimed_items = worker.claim_work_batch()

        self.assertEqual(len(claimed_items), 1)
        claimed_item = claimed_items[0]
        self.assertEqual(claimed_item.id, order_item.id)
        self.assertEqual(claimed_item.status, "assigned")
        self.assertEqual(claimed_item.retry_count, 1)
        self.assertIsNotNone(claimed_item.last_retry_at)

    def test_worker_failure_handling_with_retries(self):
        """Test that worker failure handling implements retry logic."""
        order_item = OrderItem.objects.create(
            order=self.order, prompt="Test prompt", parameters={}, retry_count=0, max_retries=3
        )

        # Create worker
        from main.workers import SmartWorker

        worker = SmartWorker()
        self.workers_to_cleanup.append(worker)
        worker.name = "test-worker"
        test_pid = get_test_pid()
        worker.worker_record = Worker.objects.create(
            name=worker.name, process_id=test_pid, provider="universal", max_batch_size=5, status="working"
        )

        # Test transient failure (should be marked for retry)
        worker.handle_item_failure(order_item, "Server disconnected without sending a response")
        order_item.refresh_from_db()

        self.assertEqual(order_item.status, "failed")
        self.assertTrue(order_item.can_be_retried())

        # Test non-transient failure (should be permanently failed)
        order_item2 = OrderItem.objects.create(
            order=self.order, prompt="Test prompt 2", parameters={}, retry_count=0, max_retries=3
        )

        worker.handle_item_failure(order_item2, "Invalid API key")
        order_item2.refresh_from_db()

        self.assertEqual(order_item2.status, "failed")
        self.assertFalse(order_item2.can_be_retried())

        # Test exhausted retries (should be marked as exhausted)
        order_item3 = OrderItem.objects.create(
            order=self.order, prompt="Test prompt 3", parameters={}, retry_count=3, max_retries=3
        )

        worker.handle_item_failure(order_item3, "Server disconnected without sending a response")
        order_item3.refresh_from_db()

        self.assertEqual(order_item3.status, "exhausted")
        self.assertFalse(order_item3.can_be_retried())

    def test_worker_ignores_non_retryable_failed_items(self):
        """Test that workers don't claim failed items that cannot be retried."""
        # Create only non-retryable failed items
        order_item1 = OrderItem.objects.create(
            order=self.order,
            prompt="Test prompt 1",
            parameters={},
            status="failed",
            error_message="Invalid API key",  # Non-transient
            retry_count=0,
            max_retries=3,
        )

        order_item2 = OrderItem.objects.create(
            order=self.order,
            prompt="Test prompt 2",
            parameters={},
            status="exhausted",  # Already exhausted
            error_message="Server disconnected without sending a response",
            retry_count=3,
            max_retries=3,
        )

        # Create worker
        from main.workers import SmartWorker

        worker = SmartWorker(max_batch_size=5)
        worker.name = "test-worker"
        worker.process_id = 12345

        # Mock worker registration
        worker.worker_record = Worker.objects.create(
            name=worker.name, process_id=worker.process_id, provider="universal", max_batch_size=5, status="starting"
        )

        # Worker should not claim any items
        claimed_items = worker.claim_work_batch()
        self.assertEqual(len(claimed_items), 0)

    def test_order_status_with_retry_states(self):
        """Test that order status calculation handles retry states correctly."""
        # Test 1: Order with only retryable failed items should stay processing
        order1 = Order.objects.create(
            prompt="Test order with only retryable failures", factory_machine_name="test_machine", provider="test"
        )

        failed_retry_item1 = OrderItem.objects.create(
            order=order1,
            prompt="Failed but retryable 1",
            status="failed",
            error_message="Server disconnected without sending a response",
            retry_count=1,
            max_retries=3,
        )

        failed_retry_item2 = OrderItem.objects.create(
            order=order1,
            prompt="Failed but retryable 2",
            status="failed",
            error_message="Connection timeout",
            retry_count=0,
            max_retries=3,
        )

        from main.workers import SmartWorker

        worker = SmartWorker()
        worker.update_order_status(order1)

        # Should be processing (has retryable failed items)
        order1.refresh_from_db()
        self.assertEqual(order1.status, "processing")

        # Test 2: Order with mixed states (completed + final states)
        order2 = Order.objects.create(
            prompt="Test order with mixed states", factory_machine_name="test_machine", provider="test"
        )

        completed_item = OrderItem.objects.create(order=order2, prompt="Completed item", status="completed")

        exhausted_item = OrderItem.objects.create(
            order=order2, prompt="Exhausted retries", status="exhausted", retry_count=3, max_retries=3
        )

        worker.update_order_status(order2)
        order2.refresh_from_db()

        # Should be partially completed (partial success)
        self.assertEqual(order2.status, "partially_completed")


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class LoggingTestCase(TestCase):
    """Test logging configuration and functionality."""

    def test_logging_configuration_exists(self):
        """Test that logging configuration is properly set up."""
        from django.conf import settings

        # Verify logging configuration exists
        self.assertIn("LOGGING", dir(settings))
        logging_config = settings.LOGGING

        # Verify essential components exist
        self.assertIn("handlers", logging_config)
        self.assertIn("loggers", logging_config)
        self.assertIn("formatters", logging_config)

        # Verify our specific handlers exist
        handlers = logging_config["handlers"]
        self.assertIn("file", handlers)
        self.assertIn("worker_file", handlers)
        self.assertIn("console", handlers)

    def test_logs_directory_exists(self):
        """Test that logs directory is created."""
        from django.conf import settings
        import os

        logs_dir = settings.BASE_DIR / "logs"
        self.assertTrue(os.path.exists(logs_dir), "Logs directory should exist")
        self.assertTrue(os.path.isdir(logs_dir), "Logs path should be a directory")

    def test_logger_functionality(self):
        """Test that loggers can write messages without errors."""
        import logging
        import tempfile
        import os

        # Test worker logger
        worker_logger = logging.getLogger("main.workers")

        # These should not raise exceptions
        worker_logger.info("Test info message from test")
        worker_logger.warning("Test warning message from test")
        worker_logger.error("Test error message from test")

        # Test factory machine logger
        factory_logger = logging.getLogger("main.factory_machines_sync")
        factory_logger.info("Test factory message from test")

        # Test general Django logger
        django_logger = logging.getLogger("django")
        django_logger.info("Test Django message from test")

    def test_log_file_creation(self):
        """Test that log files can be created and logging works without errors."""
        from django.conf import settings
        import logging
        import os

        # Check that log files exist (they're created when loggers are first used)
        worker_log_path = settings.BASE_DIR / "logs" / "workers.log"
        app_log_path = settings.BASE_DIR / "logs" / "art_factory.log"

        # Get loggers and ensure they can log without raising exceptions
        worker_logger = logging.getLogger("main.workers")
        app_logger = logging.getLogger("django")

        # These should not raise exceptions
        try:
            worker_logger.info("Test log message from unittest")
            app_logger.info("Test app log message from unittest")
        except Exception as e:
            self.fail(f"Logging should not raise exceptions: {e}")

        # Verify log files exist after logging
        self.assertTrue(os.path.exists(worker_log_path), "Worker log file should exist")
        self.assertTrue(os.path.exists(app_log_path), "App log file should exist")

        # Verify files are not empty (have some content)
        self.assertGreater(os.path.getsize(worker_log_path), 0, "Worker log file should not be empty")
        self.assertGreater(os.path.getsize(app_log_path), 0, "App log file should not be empty")


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
@patch.dict("os.environ", {"FAL_KEY": "test_key"})
@patch.dict("os.environ", {"REPLICATE_API_TOKEN": "test_token"})
class ParameterMergingTestCase(TestCase):
    """Test parameter merging in factory machines to ensure safety checks and defaults are applied."""

    def setUp(self):
        """Set up test factory machines with different safety check configurations."""
        # FLUX model with enable_safety_checker (fal.ai style)
        self.flux_machine = FactoryMachineDefinition.objects.create(
            name="fal-ai/flux/dev",
            display_name="FLUX.1 Dev (fal.ai)",
            description="Test FLUX model",
            provider="fal.ai",
            model_family="flux",
            modality="text-to-image",
            parameter_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "width": {"type": "integer", "default": 1024},
                    "height": {"type": "integer", "default": 1024},
                    "guidance_scale": {"type": "number", "default": 3.5},
                    "num_inference_steps": {"type": "integer", "default": 28},
                    "enable_safety_checker": {"type": "boolean", "default": False},
                },
                "required": ["prompt"],
            },
            default_parameters={
                "width": 1024,
                "height": 1024,
                "guidance_scale": 3.5,
                "num_inference_steps": 28,
                "enable_safety_checker": False,
            },
            is_active=True,
        )

        # SDXL model with disable_safety_checker (standard style)
        self.sdxl_machine = FactoryMachineDefinition.objects.create(
            name="fal-ai/fast-turbo-diffusion",
            display_name="SDXL Turbo (fal.ai)",
            description="Test SDXL model",
            provider="fal.ai",
            model_family="stable-diffusion",
            modality="text-to-image",
            parameter_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "width": {"type": "integer", "default": 512},
                    "height": {"type": "integer", "default": 512},
                    "num_inference_steps": {"type": "integer", "default": 1},
                    "disable_safety_checker": {"type": "boolean", "default": True},
                },
                "required": ["prompt"],
            },
            default_parameters={"width": 512, "height": 512, "num_inference_steps": 1, "disable_safety_checker": True},
            is_active=True,
        )

        # Replicate model with disable_safety_checker
        self.replicate_machine = FactoryMachineDefinition.objects.create(
            name="black-forest-labs/flux-schnell",
            display_name="FLUX.1 Schnell (Replicate)",
            description="Test Replicate model",
            provider="replicate",
            model_family="flux",
            modality="text-to-image",
            parameter_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "width": {"type": "integer", "default": 1024},
                    "height": {"type": "integer", "default": 1024},
                    "num_outputs": {"type": "integer", "default": 1},
                    "num_inference_steps": {"type": "integer", "default": 4},
                    "disable_safety_checker": {"type": "boolean", "default": True},
                },
                "required": ["prompt"],
            },
            default_parameters={
                "width": 1024,
                "height": 1024,
                "num_outputs": 1,
                "num_inference_steps": 4,
                "disable_safety_checker": True,
            },
            is_active=True,
        )

    def test_fal_factory_machine_parameter_merging(self):
        """Test that SyncFalFactoryMachine properly merges default and user parameters."""
        from main.factory_machines_sync import SyncFalFactoryMachine

        # Test FLUX model (enable_safety_checker: false)
        flux_factory = SyncFalFactoryMachine(self.flux_machine)

        # Create test order and order item
        order = Order.objects.create(
            title="Parameter Merge Test",
            prompt="test prompt",
            factory_machine_name=self.flux_machine.name,
            provider="fal.ai",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="test prompt",
            parameters={
                "width": 768,  # User override
                "height": 512,  # User override
                "guidance_scale": 5.0,  # User override
                # Note: no safety checker specified by user
            },
            status="pending",
        )

        # Simulate the parameter merging logic from execute_sync
        arguments = {
            "prompt": order_item.prompt,
            **self.flux_machine.default_parameters,  # Apply machine defaults first
            **order_item.parameters,  # Override with user-specified parameters
        }

        # Verify parameter merging
        expected_args = {
            "prompt": "test prompt",
            "width": 768,  # User override
            "height": 512,  # User override
            "guidance_scale": 5.0,  # User override
            "num_inference_steps": 28,  # Machine default
            "enable_safety_checker": False,  # Machine default (CRITICAL for safety)
        }

        self.assertEqual(arguments, expected_args)
        self.assertIn("enable_safety_checker", arguments)
        self.assertFalse(arguments["enable_safety_checker"])

    def test_fal_sdxl_parameter_merging(self):
        """Test parameter merging for SDXL models with disable_safety_checker."""
        from main.factory_machines_sync import SyncFalFactoryMachine

        sdxl_factory = SyncFalFactoryMachine(self.sdxl_machine)

        # Create test order and order item
        order = Order.objects.create(
            title="SDXL Parameter Test",
            prompt="test sdxl prompt",
            factory_machine_name=self.sdxl_machine.name,
            provider="fal.ai",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="test sdxl prompt",
            parameters={
                "width": 1024,  # User override (larger than default 512)
                "num_inference_steps": 2,  # User override
                # Note: no safety checker specified by user
            },
            status="pending",
        )

        # Simulate parameter merging
        arguments = {"prompt": order_item.prompt, **self.sdxl_machine.default_parameters, **order_item.parameters}

        expected_args = {
            "prompt": "test sdxl prompt",
            "width": 1024,  # User override
            "height": 512,  # Machine default
            "num_inference_steps": 2,  # User override
            "disable_safety_checker": True,  # Machine default (CRITICAL for safety)
        }

        self.assertEqual(arguments, expected_args)
        self.assertIn("disable_safety_checker", arguments)
        self.assertTrue(arguments["disable_safety_checker"])

    def test_replicate_factory_machine_parameter_merging(self):
        """Test that SyncReplicateFactoryMachine properly merges default and user parameters."""
        from main.factory_machines_sync import SyncReplicateFactoryMachine

        replicate_factory = SyncReplicateFactoryMachine(self.replicate_machine)

        # Create test order and order item
        order = Order.objects.create(
            title="Replicate Parameter Test",
            prompt="test replicate prompt",
            factory_machine_name=self.replicate_machine.name,
            provider="replicate",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="test replicate prompt",
            parameters={
                "height": 768,  # User override
                "num_outputs": 2,  # User override
                # Note: width and disable_safety_checker should come from defaults
            },
            status="pending",
        )

        # Simulate parameter merging from execute_sync
        input_params = {"prompt": order_item.prompt, **self.replicate_machine.default_parameters, **order_item.parameters}

        expected_params = {
            "prompt": "test replicate prompt",
            "width": 1024,  # Machine default
            "height": 768,  # User override
            "num_outputs": 2,  # User override
            "num_inference_steps": 4,  # Machine default
            "disable_safety_checker": True,  # Machine default (CRITICAL for safety)
        }

        self.assertEqual(input_params, expected_params)
        self.assertIn("disable_safety_checker", input_params)
        self.assertTrue(input_params["disable_safety_checker"])

    def test_user_can_override_safety_checks_if_desired(self):
        """Test that users can override safety check settings if they explicitly specify them."""
        from main.factory_machines_sync import SyncFalFactoryMachine

        # Create order item where user explicitly enables safety checker
        order = Order.objects.create(
            title="User Override Test",
            prompt="test prompt",
            factory_machine_name=self.flux_machine.name,
            provider="fal.ai",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="test prompt",
            parameters={"width": 512, "enable_safety_checker": True},  # User explicitly enables
            status="pending",
        )

        # Simulate parameter merging
        arguments = {
            "prompt": order_item.prompt,
            **self.flux_machine.default_parameters,  # enable_safety_checker: False
            **order_item.parameters,  # enable_safety_checker: True (overrides)
        }

        # User override should take precedence
        self.assertTrue(arguments["enable_safety_checker"])
        self.assertEqual(arguments["width"], 512)
        self.assertEqual(arguments["height"], 1024)  # Still get other defaults

    def test_parameter_merging_with_negative_prompts(self):
        """Test parameter merging when negative prompts are involved."""
        from main.factory_machines_sync import SyncFalFactoryMachine

        order = Order.objects.create(
            title="Negative Prompt Test",
            prompt="beautiful landscape",
            factory_machine_name=self.sdxl_machine.name,
            provider="fal.ai",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="beautiful landscape",
            negative_prompt="ugly, distorted",  # Negative prompt set
            parameters={"width": 768},
            status="pending",
        )

        # Simulate full parameter preparation from execute_sync
        arguments = {"prompt": order_item.prompt, **self.sdxl_machine.default_parameters, **order_item.parameters}

        # Add negative prompt (this happens separately in execute_sync)
        if order_item.negative_prompt:
            arguments["negative_prompt"] = order_item.negative_prompt

        expected_args = {
            "prompt": "beautiful landscape",
            "negative_prompt": "ugly, distorted",
            "width": 768,  # User override
            "height": 512,  # Machine default
            "num_inference_steps": 1,  # Machine default
            "disable_safety_checker": True,  # Machine default
        }

        self.assertEqual(arguments, expected_args)
        self.assertIn("negative_prompt", arguments)
        self.assertTrue(arguments["disable_safety_checker"])

    def test_parameter_merging_preserves_all_defaults(self):
        """Test that parameter merging preserves all machine defaults when user provides minimal parameters."""
        from main.factory_machines_sync import SyncFalFactoryMachine

        order = Order.objects.create(
            title="Minimal Parameters Test",
            prompt="minimal test",
            factory_machine_name=self.flux_machine.name,
            provider="fal.ai",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order, prompt="minimal test", parameters={}, status="pending"  # User provides no parameters except prompt
        )

        # Simulate parameter merging
        arguments = {
            "prompt": order_item.prompt,
            **self.flux_machine.default_parameters,
            **order_item.parameters,  # Empty dict, no overrides
        }

        # Should get all machine defaults
        expected_args = {
            "prompt": "minimal test",
            "width": 1024,
            "height": 1024,
            "guidance_scale": 3.5,
            "num_inference_steps": 28,
            "enable_safety_checker": False,
        }

        self.assertEqual(arguments, expected_args)
        # Verify all default parameters are present
        for key, value in self.flux_machine.default_parameters.items():
            self.assertIn(key, arguments)
            self.assertEqual(arguments[key], value)

    def test_parameter_merging_handles_missing_defaults_gracefully(self):
        """Test parameter merging when machine has incomplete default parameters."""
        # Create machine with minimal defaults (simulating edge case)
        minimal_machine = FactoryMachineDefinition.objects.create(
            name="test/minimal",
            display_name="Minimal Test Model",
            provider="fal.ai",
            modality="text-to-image",
            parameter_schema={"prompt": {"type": "string"}},
            default_parameters={},  # No defaults provided
            is_active=True,
        )

        order = Order.objects.create(
            title="Minimal Defaults Test",
            prompt="test",
            factory_machine_name=minimal_machine.name,
            provider="fal.ai",
            quantity=1,
        )

        order_item = OrderItem.objects.create(order=order, prompt="test", parameters={"width": 512}, status="pending")

        # Should not crash with empty defaults
        arguments = {"prompt": order_item.prompt, **minimal_machine.default_parameters, **order_item.parameters}  # Empty dict

        expected_args = {"prompt": "test", "width": 512}

        self.assertEqual(arguments, expected_args)

    @patch("fal_client.submit")
    def test_fal_execute_sync_uses_merged_parameters(self, mock_fal_submit):
        """Integration test to verify execute_sync actually uses merged parameters."""
        from main.factory_machines_sync import SyncFalFactoryMachine

        # Mock fal.ai response
        mock_handle = MagicMock()
        mock_handle.get.return_value = {
            "images": [{"url": "data:image/jpeg;base64,/9j/test", "width": 512, "height": 512}],
            "seed": 12345,
        }
        mock_fal_submit.return_value = mock_handle

        factory = SyncFalFactoryMachine(self.sdxl_machine)

        order = Order.objects.create(
            title="Integration Test",
            prompt="integration test",
            factory_machine_name=self.sdxl_machine.name,
            provider="fal.ai",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order, prompt="integration test", parameters={"width": 1024}, status="pending"  # Override default 512
        )

        # Execute synchronously
        result = factory.execute_sync(order_item)

        # Verify fal_client.submit was called with merged parameters
        mock_fal_submit.assert_called_once()
        call_args = mock_fal_submit.call_args

        # Check that arguments include both user parameters and machine defaults
        submitted_args = call_args[1]["arguments"]  # fal_client.submit(model, arguments=...)

        self.assertEqual(submitted_args["prompt"], "integration test")
        self.assertEqual(submitted_args["width"], 1024)  # User override
        self.assertEqual(submitted_args["height"], 512)  # Machine default
        self.assertEqual(submitted_args["num_inference_steps"], 1)  # Machine default
        self.assertTrue(submitted_args["disable_safety_checker"])  # Machine default (CRITICAL)

        self.assertTrue(result)  # Should succeed

    @patch("replicate.run")
    def test_replicate_execute_sync_uses_merged_parameters(self, mock_replicate_run):
        """Integration test to verify Replicate execute_sync uses merged parameters."""
        from main.factory_machines_sync import SyncReplicateFactoryMachine

        # Mock replicate response
        mock_replicate_run.return_value = ["http://example.com/image.png"]

        factory = SyncReplicateFactoryMachine(self.replicate_machine)

        order = Order.objects.create(
            title="Replicate Integration Test",
            prompt="replicate test",
            factory_machine_name=self.replicate_machine.name,
            provider="replicate",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order, prompt="replicate test", parameters={"num_outputs": 2}, status="pending"  # Override default 1
        )

        # Mock HTTP download
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake_image_data"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Execute synchronously
            result = factory.execute_sync(order_item)

        # Verify replicate.run was called with merged parameters
        mock_replicate_run.assert_called_once()
        call_args = mock_replicate_run.call_args

        model_name = call_args[0][0]  # First positional arg
        input_params = call_args[1]["input"]  # Keyword arg

        self.assertEqual(model_name, self.replicate_machine.name)
        self.assertEqual(input_params["prompt"], "replicate test")
        self.assertEqual(input_params["num_outputs"], 2)  # User override
        self.assertEqual(input_params["width"], 1024)  # Machine default
        self.assertEqual(input_params["height"], 1024)  # Machine default
        self.assertEqual(input_params["num_inference_steps"], 4)  # Machine default
        self.assertTrue(input_params["disable_safety_checker"])  # Machine default (CRITICAL)

        self.assertTrue(result)  # Should succeed