"""
Comprehensive tests for factory machine implementations.
Tests both SyncFalFactoryMachine and SyncReplicateFactoryMachine.
"""

from unittest.mock import MagicMock, mock_open, patch

from django.test import TestCase, override_settings

from main.factory_machines_sync import (
    SyncFalFactoryMachine,
    SyncReplicateFactoryMachine,
    execute_order_item_sync_batch,
    safe_seed_value,
)
from main.models import FactoryMachineDefinition, Order, OrderItem, Product


class SafeSeedValueTestCase(TestCase):
    """Test the safe_seed_value utility function."""

    def test_safe_seed_value_none(self):
        """Test handling of None value."""
        self.assertIsNone(safe_seed_value(None))

    def test_safe_seed_value_valid_int(self):
        """Test handling of valid integer."""
        self.assertEqual(safe_seed_value(12345), 12345)
        self.assertEqual(safe_seed_value(0), 0)
        self.assertEqual(safe_seed_value(-100), -100)

    def test_safe_seed_value_string(self):
        """Test conversion of string to int."""
        self.assertEqual(safe_seed_value("12345"), 12345)
        self.assertEqual(safe_seed_value("0"), 0)

    def test_safe_seed_value_large_positive(self):
        """Test handling of values larger than SQLite max."""
        max_sqlite = 9223372036854775807
        large_value = max_sqlite + 1000
        result = safe_seed_value(large_value)
        self.assertTrue(result <= max_sqlite)
        self.assertEqual(result, large_value % max_sqlite)

    def test_safe_seed_value_large_negative(self):
        """Test handling of very negative values."""
        max_sqlite = 9223372036854775807
        large_negative = -max_sqlite - 1000
        result = safe_seed_value(large_negative)
        self.assertTrue(result >= -max_sqlite)

    def test_safe_seed_value_invalid_string(self):
        """Test handling of invalid string values."""
        self.assertEqual(safe_seed_value("invalid"), 0)
        self.assertEqual(safe_seed_value("12.34"), 0)  # Not a valid int

    def test_safe_seed_value_invalid_type(self):
        """Test handling of invalid types."""
        self.assertEqual(safe_seed_value([1, 2, 3]), 0)
        self.assertEqual(safe_seed_value({"key": "value"}), 0)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
@patch.dict("os.environ", {"FAL_KEY": "test_fal_key"})
class SyncFalFactoryMachineTestCase(TestCase):
    """Test SyncFalFactoryMachine functionality."""

    def setUp(self):
        """Set up test data."""
        self.machine_definition = FactoryMachineDefinition.objects.create(
            name="fal-ai/flux/dev",
            display_name="FLUX.1 Dev (fal.ai)",
            description="Test FLUX model",
            provider="fal.ai",
            modality="text-to-image",
            parameter_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "width": {"type": "integer", "default": 1024},
                    "height": {"type": "integer", "default": 1024},
                    "num_inference_steps": {"type": "integer", "default": 28},
                    "enable_safety_checker": {"type": "boolean", "default": False},
                },
                "required": ["prompt"],
            },
            default_parameters={
                "width": 1024,
                "height": 1024,
                "num_inference_steps": 28,
                "enable_safety_checker": False,
            },
            is_active=True,
        )

        self.order = Order.objects.create(
            title="Test Order",
            prompt="a beautiful landscape",
            factory_machine_name=self.machine_definition.name,
            provider="fal.ai",
            quantity=1,
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            prompt=self.order.prompt,
            parameters={"width": 768, "height": 512},
            status="pending",
        )

    def test_factory_machine_initialization(self):
        """Test factory machine initialization."""
        factory = SyncFalFactoryMachine(self.machine_definition)

        self.assertEqual(factory.machine_definition, self.machine_definition)
        self.assertEqual(factory.provider, "fal.ai")
        self.assertEqual(factory.model_name, "fal-ai/flux/dev")
        self.assertIsNotNone(factory.error_handler)

    @patch.dict("os.environ", {}, clear=True)
    @patch("main.factory_machines_sync.settings")
    def test_factory_machine_no_api_key(self, mock_settings):
        """Test factory machine initialization without API key."""
        mock_settings.FAL_API_KEY = None

        with self.assertRaises(Exception) as context:
            SyncFalFactoryMachine(self.machine_definition)

        self.assertIn("FAL_API_KEY not configured", str(context.exception))

    @patch("fal_client.submit")
    def test_execute_sync_success_single_image(self, mock_fal_submit):
        """Test successful execution with single image."""
        # Mock fal.ai response
        mock_handle = MagicMock()
        mock_handle.get.return_value = {
            "images": [{"url": "http://example.com/image.png", "width": 768, "height": 512}],
            "seed": 12345,
            "request_id": "test_request_123",
        }
        mock_fal_submit.return_value = mock_handle

        # Mock HTTP download
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake_image_data"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Mock file operations
            with patch("builtins.open", mock_open()):
                with patch("os.makedirs"):
                    factory = SyncFalFactoryMachine(self.machine_definition)
                    result = factory.execute_sync(self.order_item)

        # Verify success
        self.assertTrue(result)

        # Verify order item was updated
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.status, "completed")
        self.assertIsNotNone(self.order_item.completed_at)
        self.assertEqual(self.order_item.batches_completed, 1)

        # Verify fal.ai was called with correct parameters
        mock_fal_submit.assert_called_once()
        call_args = mock_fal_submit.call_args
        self.assertEqual(call_args[0][0], "fal-ai/flux/dev")  # model name

        arguments = call_args[1]["arguments"]
        self.assertEqual(arguments["prompt"], "a beautiful landscape")
        self.assertEqual(arguments["width"], 768)  # User override
        self.assertEqual(arguments["height"], 512)  # User override
        self.assertEqual(arguments["num_inference_steps"], 28)  # Default
        self.assertEqual(arguments["enable_safety_checker"], False)  # Default

        # Verify product was created
        products = Product.objects.filter(order_item=self.order_item)
        self.assertEqual(products.count(), 1)

        product = products.first()
        self.assertEqual(product.provider, "fal.ai")
        self.assertEqual(product.model_name, "fal-ai/flux/dev")
        self.assertEqual(product.width, 768)
        self.assertEqual(product.height, 512)
        self.assertEqual(product.seed, 12345)

    @patch("fal_client.submit")
    def test_execute_sync_success_batch_images(self, mock_fal_submit):
        """Test successful execution with batch of images."""
        # Mock fal.ai response with multiple images
        mock_handle = MagicMock()
        mock_handle.get.return_value = {
            "images": [
                {"url": "http://example.com/image1.png", "width": 512, "height": 512},
                {"url": "http://example.com/image2.png", "width": 512, "height": 512},
            ],
            "seed": 12345,
            "request_id": "test_batch_123",
        }
        mock_fal_submit.return_value = mock_handle

        # Update order item for batch processing
        self.order_item.batch_size = 2
        self.order_item.total_quantity = 2
        self.order_item.save()

        # Mock HTTP download
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake_image_data"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Mock file operations
            with patch("builtins.open", mock_open()):
                with patch("os.makedirs"):
                    factory = SyncFalFactoryMachine(self.machine_definition)
                    result = factory.execute_sync(self.order_item)

        # Verify success
        self.assertTrue(result)

        # Verify multiple products were created
        products = Product.objects.filter(order_item=self.order_item)
        self.assertEqual(products.count(), 2)

        # Verify products have correct seeds (incremented)
        seeds = [p.seed for p in products]
        self.assertIn(12345, seeds)  # First image gets base seed
        self.assertIn(12346, seeds)  # Second image gets base seed + 1

    @patch("fal_client.submit")
    def test_execute_sync_base64_image(self, mock_fal_submit):
        """Test successful execution with base64 data URI."""
        # Mock fal.ai response with base64 image
        mock_handle = MagicMock()
        fake_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        mock_handle.get.return_value = {
            "images": [{"url": f"data:image/png;base64,{fake_base64}", "width": 1, "height": 1}],
            "seed": 67890,
        }
        mock_fal_submit.return_value = mock_handle

        # Mock file operations
        with patch("builtins.open", mock_open()):
            with patch("os.makedirs"):
                factory = SyncFalFactoryMachine(self.machine_definition)
                result = factory.execute_sync(self.order_item)

        # Verify success
        self.assertTrue(result)

        # Verify product was created with base64 data
        product = Product.objects.filter(order_item=self.order_item).first()
        self.assertIsNotNone(product)
        self.assertEqual(product.seed, 67890)

    def test_execute_sync_with_negative_prompt(self):
        """Test execution with negative prompt."""
        self.order_item.negative_prompt = "ugly, distorted"
        self.order_item.save()

        with patch("fal_client.submit") as mock_fal_submit:
            mock_handle = MagicMock()
            mock_handle.get.return_value = {
                "images": [{"url": "http://example.com/image.png", "width": 512, "height": 512}],
                "seed": 12345,
            }
            mock_fal_submit.return_value = mock_handle

            with patch("requests.get") as mock_get:
                mock_response = MagicMock()
                mock_response.content = b"fake_image_data"
                mock_response.raise_for_status.return_value = None
                mock_get.return_value = mock_response

                with patch("builtins.open", mock_open()):
                    with patch("os.makedirs"):
                        factory = SyncFalFactoryMachine(self.machine_definition)
                        factory.execute_sync(self.order_item)

        # Verify negative prompt was included in arguments
        call_args = mock_fal_submit.call_args
        arguments = call_args[1]["arguments"]
        self.assertEqual(arguments["negative_prompt"], "ugly, distorted")

    @patch("fal_client.submit")
    def test_execute_sync_no_images_returned(self, mock_fal_submit):
        """Test handling when no images are returned."""
        mock_handle = MagicMock()
        mock_handle.get.return_value = {"images": []}  # Empty images array
        mock_fal_submit.return_value = mock_handle

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        # Verify failure
        self.assertFalse(result)

        # Verify order item status
        self.order_item.refresh_from_db()
        self.assertIn(self.order_item.status, ["failed", "exhausted"])
        self.assertIsNotNone(self.order_item.error_message)

    @patch("fal_client.submit")
    def test_execute_sync_api_error(self, mock_fal_submit):
        """Test handling of fal.ai API errors."""
        mock_fal_submit.side_effect = Exception("Rate limit exceeded")

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        # Verify failure
        self.assertFalse(result)

        # Verify error handling
        self.order_item.refresh_from_db()
        self.assertIn(self.order_item.status, ["failed", "exhausted"])
        self.assertIsNotNone(self.order_item.error_message)
        self.assertIsNotNone(self.order_item.error_category)

    @patch("fal_client.submit")
    def test_execute_sync_download_error(self, mock_fal_submit):
        """Test handling of image download errors."""
        mock_handle = MagicMock()
        mock_handle.get.return_value = {
            "images": [{"url": "http://example.com/image.png", "width": 512, "height": 512}],
            "seed": 12345,
        }
        mock_fal_submit.return_value = mock_handle

        # Mock failed download
        with patch("requests.get") as mock_get:
            mock_get.side_effect = Exception("Connection timeout")

            factory = SyncFalFactoryMachine(self.machine_definition)
            result = factory.execute_sync(self.order_item)

        # Verify failure
        self.assertFalse(result)

        # Verify error handling
        self.order_item.refresh_from_db()
        self.assertIn(self.order_item.status, ["failed", "exhausted"])

    @patch("fal_client.submit")
    def test_execute_sync_file_save_error(self, mock_fal_submit):
        """Test handling of file save errors."""
        mock_handle = MagicMock()
        mock_handle.get.return_value = {
            "images": [{"url": "http://example.com/image.png", "width": 512, "height": 512}],
            "seed": 12345,
        }
        mock_fal_submit.return_value = mock_handle

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake_image_data"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Mock file save failure
            with patch("builtins.open", side_effect=IOError("Permission denied")):
                with patch("os.makedirs"):
                    factory = SyncFalFactoryMachine(self.machine_definition)
                    result = factory.execute_sync(self.order_item)

        # Verify failure
        self.assertFalse(result)

    def test_create_product_directory_creation_failure(self):
        """Test _create_product when directory creation fails."""
        factory = SyncFalFactoryMachine(self.machine_definition)

        with patch("os.makedirs", side_effect=OSError("Permission denied")):
            with self.assertRaises(Exception) as context:
                factory._create_product(
                    self.order_item, b"fake_data", "test.jpg", {"width": 512, "height": 512, "seed": 12345}
                )

            self.assertIn("Failed to create media directory", str(context.exception))

    def test_update_order_status_no_items(self):
        """Test _update_order_status with order that has no items."""
        factory = SyncFalFactoryMachine(self.machine_definition)

        # Create order with no items
        empty_order = Order.objects.create(
            title="Empty Order",
            prompt="test",
            factory_machine_name=self.machine_definition.name,
            provider="fal.ai",
            quantity=0,
        )

        # Should not crash
        factory._update_order_status(empty_order)

        # Order status should remain unchanged
        empty_order.refresh_from_db()
        self.assertEqual(empty_order.status, "pending")


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
@patch.dict("os.environ", {"REPLICATE_API_TOKEN": "test_replicate_token"})
class SyncReplicateFactoryMachineTestCase(TestCase):
    """Test SyncReplicateFactoryMachine functionality."""

    def setUp(self):
        """Set up test data."""
        self.machine_definition = FactoryMachineDefinition.objects.create(
            name="black-forest-labs/flux-schnell",
            display_name="FLUX.1 Schnell (Replicate)",
            description="Test Replicate model",
            provider="replicate",
            modality="text-to-image",
            parameter_schema={
                "type": "object",
                "properties": {
                    "prompt": {"type": "string"},
                    "width": {"type": "integer", "default": 1024},
                    "height": {"type": "integer", "default": 1024},
                    "num_outputs": {"type": "integer", "default": 1},
                    "disable_safety_checker": {"type": "boolean", "default": True},
                },
                "required": ["prompt"],
            },
            default_parameters={
                "width": 1024,
                "height": 1024,
                "num_outputs": 1,
                "disable_safety_checker": True,
            },
            is_active=True,
        )

        self.order = Order.objects.create(
            title="Test Replicate Order",
            prompt="a beautiful sunset",
            factory_machine_name=self.machine_definition.name,
            provider="replicate",
            quantity=1,
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            prompt=self.order.prompt,
            parameters={"width": 512, "num_outputs": 2},
            status="pending",
        )

    def test_factory_machine_initialization(self):
        """Test Replicate factory machine initialization."""
        factory = SyncReplicateFactoryMachine(self.machine_definition)

        self.assertEqual(factory.machine_definition, self.machine_definition)
        self.assertEqual(factory.provider, "replicate")
        self.assertEqual(factory.model_name, "black-forest-labs/flux-schnell")
        self.assertIsNotNone(factory.error_handler)

    @patch.dict("os.environ", {}, clear=True)
    @patch("main.factory_machines_sync.settings")
    def test_factory_machine_no_api_token(self, mock_settings):
        """Test factory machine initialization without API token."""
        mock_settings.REPLICATE_API_TOKEN = None

        with self.assertRaises(Exception) as context:
            SyncReplicateFactoryMachine(self.machine_definition)

        self.assertIn("REPLICATE_API_TOKEN not configured", str(context.exception))

    @patch("replicate.run")
    def test_execute_sync_success_single_output(self, mock_replicate_run):
        """Test successful execution with single output."""
        mock_replicate_run.return_value = ["http://example.com/image.png"]

        # Mock HTTP download
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake_image_data"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Mock file operations
            with patch("builtins.open", mock_open()):
                with patch("os.makedirs"):
                    factory = SyncReplicateFactoryMachine(self.machine_definition)
                    result = factory.execute_sync(self.order_item)

        # Verify success
        self.assertTrue(result)

        # Verify order item was updated
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.status, "completed")
        self.assertIsNotNone(self.order_item.completed_at)
        self.assertEqual(self.order_item.batches_completed, 1)

        # Verify replicate.run was called with correct parameters
        mock_replicate_run.assert_called_once()
        call_args = mock_replicate_run.call_args

        model_name = call_args[0][0]  # First positional arg
        input_params = call_args[1]["input"]  # Keyword arg

        self.assertEqual(model_name, "black-forest-labs/flux-schnell")
        self.assertEqual(input_params["prompt"], "a beautiful sunset")
        self.assertEqual(input_params["width"], 512)  # User override
        self.assertEqual(input_params["height"], 1024)  # Default
        self.assertEqual(input_params["num_outputs"], 2)  # User override
        self.assertTrue(input_params["disable_safety_checker"])  # Default

    @patch("replicate.run")
    def test_execute_sync_multiple_outputs(self, mock_replicate_run):
        """Test successful execution with multiple outputs."""
        mock_replicate_run.return_value = [
            "http://example.com/image1.png",
            "http://example.com/image2.png",
        ]

        # Mock HTTP download
        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake_image_data"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Mock file operations
            with patch("builtins.open", mock_open()):
                with patch("os.makedirs"):
                    factory = SyncReplicateFactoryMachine(self.machine_definition)
                    result = factory.execute_sync(self.order_item)

        # Verify success
        self.assertTrue(result)

        # Verify multiple products were created
        products = Product.objects.filter(order_item=self.order_item)
        self.assertEqual(products.count(), 2)

    @patch("replicate.run")
    def test_execute_sync_api_error(self, mock_replicate_run):
        """Test handling of Replicate API errors."""
        mock_replicate_run.side_effect = Exception("Authentication failed")

        factory = SyncReplicateFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        # Verify failure
        self.assertFalse(result)

        # Verify error handling
        self.order_item.refresh_from_db()
        self.assertIn(self.order_item.status, ["failed", "exhausted"])
        self.assertIsNotNone(self.order_item.error_message)

    @patch("replicate.run")
    def test_execute_sync_no_output(self, mock_replicate_run):
        """Test handling when no output is returned."""
        mock_replicate_run.return_value = None

        factory = SyncReplicateFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        # Verify failure
        self.assertFalse(result)

        # Verify error handling
        self.order_item.refresh_from_db()
        self.assertIn(self.order_item.status, ["failed", "exhausted"])


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class ExecuteOrderItemSyncBatchTestCase(TestCase):
    """Test the execute_order_item_sync_batch function."""

    def setUp(self):
        """Set up test data."""
        self.fal_machine = FactoryMachineDefinition.objects.create(
            name="fal-ai/flux/dev",
            display_name="FLUX.1 Dev (fal.ai)",
            provider="fal.ai",
            modality="text-to-image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

        self.replicate_machine = FactoryMachineDefinition.objects.create(
            name="black-forest-labs/flux-schnell",
            display_name="FLUX.1 Schnell (Replicate)",
            provider="replicate",
            modality="text-to-image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

    def test_execute_fal_order_item(self):
        """Test executing a fal.ai order item."""
        order = Order.objects.create(
            title="Test Order",
            prompt="test prompt",
            factory_machine_name=self.fal_machine.name,
            provider="fal.ai",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="test prompt",
            parameters={},
            status="pending",
        )

        with patch.object(SyncFalFactoryMachine, "execute_sync", return_value=True) as mock_execute:
            result = execute_order_item_sync_batch(order_item.id)

        self.assertTrue(result)
        mock_execute.assert_called_once_with(order_item)

    def test_execute_replicate_order_item(self):
        """Test executing a Replicate order item."""
        order = Order.objects.create(
            title="Test Order",
            prompt="test prompt",
            factory_machine_name=self.replicate_machine.name,
            provider="replicate",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="test prompt",
            parameters={},
            status="pending",
        )

        with patch.object(SyncReplicateFactoryMachine, "execute_sync", return_value=True) as mock_execute:
            result = execute_order_item_sync_batch(order_item.id)

        self.assertTrue(result)
        mock_execute.assert_called_once_with(order_item)

    def test_execute_unknown_provider(self):
        """Test executing with unknown provider."""
        unknown_machine = FactoryMachineDefinition.objects.create(
            name="unknown/model",
            display_name="Unknown Model",
            provider="unknown_provider",
            modality="text-to-image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

        order = Order.objects.create(
            title="Test Order",
            prompt="test prompt",
            factory_machine_name=unknown_machine.name,
            provider="unknown_provider",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="test prompt",
            parameters={},
            status="pending",
        )

        result = execute_order_item_sync_batch(order_item.id)
        self.assertFalse(result)

    def test_execute_nonexistent_order_item(self):
        """Test executing with non-existent order item ID."""
        result = execute_order_item_sync_batch(99999)
        self.assertFalse(result)

    def test_execute_nonexistent_machine_definition(self):
        """Test executing with non-existent machine definition."""
        order = Order.objects.create(
            title="Test Order",
            prompt="test prompt",
            factory_machine_name="nonexistent/model",
            provider="fal.ai",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="test prompt",
            parameters={},
            status="pending",
        )

        result = execute_order_item_sync_batch(order_item.id)
        self.assertFalse(result)
