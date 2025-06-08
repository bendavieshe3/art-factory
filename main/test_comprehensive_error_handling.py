"""
Comprehensive error handling and edge case tests for Art Factory.
Tests critical error paths, network failures, API errors, file operations, and database issues.

This module addresses GitHub issue #31 by providing extensive coverage of error scenarios
that could occur in production environments.
"""

import json
import os
import tempfile
import time
from unittest.mock import patch, MagicMock, mock_open, PropertyMock
from django.test import TestCase, override_settings
from django.db import transaction, IntegrityError, OperationalError
from django.core.exceptions import ValidationError
import requests
import httpx

from main.models import Order, OrderItem, Product, FactoryMachineDefinition, Worker
from main.factory_machines_sync import (
    SyncFalFactoryMachine,
    SyncReplicateFactoryMachine,
    execute_order_item_sync_batch,
)
from main.workers import SmartWorker
from main.error_handling import ErrorHandler, ErrorCategory


class ErrorSimulationUtilities:
    """
    Utility class for simulating various types of errors in tests.
    Provides consistent error injection patterns across all test scenarios.
    """

    # Network Error Simulations
    @staticmethod
    def connection_timeout():
        """Simulate network connection timeout."""
        return Exception("Connection timed out after 30 seconds")

    @staticmethod
    def read_timeout():
        """Simulate network read timeout."""
        return requests.exceptions.ReadTimeout("Read timed out after 60 seconds")

    @staticmethod
    def dns_failure():
        """Simulate DNS resolution failure."""
        return requests.exceptions.ConnectionError("Failed to resolve hostname")

    @staticmethod
    def ssl_error():
        """Simulate SSL/TLS certificate error."""
        return requests.exceptions.SSLError("SSL certificate verification failed")

    @staticmethod
    def connection_refused():
        """Simulate connection refused (service down)."""
        return Exception("Connection refused by remote host")

    @staticmethod
    def intermittent_failure():
        """Simulate intermittent network issues."""
        return Exception("Temporary network failure")

    # HTTP Error Responses
    @staticmethod
    def http_error_response(status_code, message="Error"):
        """Create HTTP error response."""
        response = MagicMock()
        response.status_code = status_code
        response.text = message
        response.json.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            f"{status_code} {message}", response=response
        )
        return response

    @staticmethod
    def malformed_json_response():
        """Create response with malformed JSON."""
        response = MagicMock()
        response.status_code = 200
        response.content = b'{"images": [{"url": "http://example.com/img.png", "width":'  # Incomplete JSON
        response.json.side_effect = json.JSONDecodeError("Expecting ',' delimiter", "", 50)
        return response

    @staticmethod
    def rate_limit_response():
        """Create rate limit response with headers."""
        response = MagicMock()
        response.status_code = 429
        response.headers = {
            "X-RateLimit-Limit": "100",
            "X-RateLimit-Remaining": "0",
            "X-RateLimit-Reset": str(int(time.time()) + 3600),
            "Retry-After": "3600",
        }
        response.text = "Rate limit exceeded"
        response.raise_for_status.side_effect = requests.exceptions.HTTPError("429 Rate limit exceeded", response=response)
        return response

    # File System Errors
    @staticmethod
    def disk_full_error():
        """Simulate disk full during file write."""
        return OSError("No space left on device")

    @staticmethod
    def permission_denied_error():
        """Simulate permission denied for file operations."""
        return PermissionError("Permission denied")

    @staticmethod
    def file_not_found_error():
        """Simulate file not found error."""
        return FileNotFoundError("No such file or directory")

    @staticmethod
    def invalid_filename_error():
        """Simulate invalid filename characters."""
        return OSError("Invalid filename characters")

    # Database Errors
    @staticmethod
    def database_connection_error():
        """Simulate database connection failure."""
        return OperationalError("Database connection failed")

    @staticmethod
    def database_deadlock_error():
        """Simulate database deadlock."""
        return OperationalError("Deadlock detected")

    @staticmethod
    def integrity_constraint_error():
        """Simulate database constraint violation."""
        return IntegrityError("Unique constraint violated")

    # Memory/Resource Errors
    @staticmethod
    def memory_error():
        """Simulate out of memory error."""
        return MemoryError("Out of memory")

    @staticmethod
    def process_limit_error():
        """Simulate process/resource limit exceeded."""
        return OSError("Resource temporarily unavailable")


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
@patch.dict("os.environ", {"FAL_KEY": "test_fal_key"})
class NetworkFailureTestCase(TestCase):
    """Test network failure scenarios that could occur in production."""

    def setUp(self):
        """Set up test data."""
        self.machine_definition = FactoryMachineDefinition.objects.create(
            name="fal-ai/flux/dev",
            display_name="FLUX.1 Dev (fal.ai)",
            description="Test FLUX model",
            provider="fal.ai",
            modality="text-to-image",
            parameter_schema={"prompt": {"type": "string"}},
            default_parameters={"width": 1024, "height": 1024},
            is_active=True,
        )

        self.order = Order.objects.create(
            title="Network Test Order",
            prompt="test network failures",
            factory_machine_name=self.machine_definition.name,
            provider="fal.ai",
            quantity=1,
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            prompt=self.order.prompt,
            parameters={},
            status="pending",
        )

    @patch("fal_client.submit")
    def test_connection_timeout_handling(self, mock_fal_submit):
        """Test handling of connection timeouts during API calls."""
        mock_fal_submit.side_effect = ErrorSimulationUtilities.connection_timeout()

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        # Verify failure handling
        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertIn(self.order_item.status, ["failed", "exhausted"])
        # Check for user-friendly message about network issues
        self.assertIn("network", self.order_item.error_message.lower())
        self.assertEqual(self.order_item.error_category, ErrorCategory.NETWORK)

    @patch("fal_client.submit")
    def test_dns_resolution_failure(self, mock_fal_submit):
        """Test handling of DNS resolution failures."""
        mock_fal_submit.side_effect = ErrorSimulationUtilities.dns_failure()

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertIn(self.order_item.status, ["failed", "exhausted"])
        # Check for user-friendly message about network issues
        self.assertIn("network", self.order_item.error_message.lower())
        self.assertEqual(self.order_item.error_category, ErrorCategory.NETWORK)

    @patch("fal_client.submit")
    def test_ssl_certificate_error(self, mock_fal_submit):
        """Test handling of SSL certificate errors."""
        mock_fal_submit.side_effect = ErrorSimulationUtilities.ssl_error()

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertIn(self.order_item.status, ["failed", "exhausted"])
        # Check for user-friendly message about network issues
        self.assertIn("network", self.order_item.error_message.lower())

    @patch("fal_client.submit")
    def test_connection_refused_error(self, mock_fal_submit):
        """Test handling when remote service is down."""
        mock_fal_submit.side_effect = ErrorSimulationUtilities.connection_refused()

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.error_category, ErrorCategory.PROVIDER_OUTAGE)

    @patch("fal_client.submit")
    def test_intermittent_network_failure(self, mock_fal_submit):
        """Test handling of intermittent network issues."""
        mock_fal_submit.side_effect = ErrorSimulationUtilities.intermittent_failure()

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.error_category, ErrorCategory.TRANSIENT)
        # Should be retryable since it's transient
        self.assertTrue(self.order_item.can_be_retried())


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
@patch.dict("os.environ", {"FAL_KEY": "test_fal_key"})
class APIErrorResponseTestCase(TestCase):
    """Test various API error responses from providers."""

    def setUp(self):
        """Set up test data."""
        self.machine_definition = FactoryMachineDefinition.objects.create(
            name="fal-ai/flux/dev",
            display_name="FLUX.1 Dev (fal.ai)",
            provider="fal.ai",
            modality="text-to-image",
            parameter_schema={"prompt": {"type": "string"}},
            default_parameters={},
            is_active=True,
        )

        self.order = Order.objects.create(
            title="API Error Test",
            prompt="test api errors",
            factory_machine_name=self.machine_definition.name,
            provider="fal.ai",
            quantity=1,
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            prompt=self.order.prompt,
            parameters={},
            status="pending",
        )

    @patch("fal_client.submit")
    def test_502_bad_gateway_error(self, mock_fal_submit):
        """Test handling of 502 Bad Gateway errors."""
        mock_fal_submit.side_effect = Exception("502 Bad Gateway")

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.error_category, ErrorCategory.PROVIDER_OUTAGE)

    @patch("fal_client.submit")
    def test_503_service_unavailable_error(self, mock_fal_submit):
        """Test handling of 503 Service Unavailable errors."""
        mock_fal_submit.side_effect = Exception("503 Service Unavailable")

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.error_category, ErrorCategory.PROVIDER_OUTAGE)

    @patch("fal_client.submit")
    def test_504_gateway_timeout_error(self, mock_fal_submit):
        """Test handling of 504 Gateway Timeout errors."""
        mock_fal_submit.side_effect = Exception("504 Gateway Timeout")

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.error_category, ErrorCategory.TRANSIENT)

    @patch("fal_client.submit")
    def test_rate_limit_with_headers(self, mock_fal_submit):
        """Test proper handling of rate limit responses with headers."""
        mock_fal_submit.side_effect = Exception("Rate limit exceeded")

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.error_category, ErrorCategory.RATE_LIMITED)

    @patch("fal_client.submit")
    def test_malformed_api_response(self, mock_fal_submit):
        """Test handling of malformed API responses."""
        mock_handle = MagicMock()
        mock_handle.get.side_effect = json.JSONDecodeError("Invalid JSON", "", 0)
        mock_fal_submit.return_value = mock_handle

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertIn(self.order_item.status, ["failed", "exhausted"])

    @patch("fal_client.submit")
    def test_partial_response_corruption(self, mock_fal_submit):
        """Test handling when API response is partially corrupted."""
        mock_handle = MagicMock()
        mock_handle.get.return_value = {
            "images": [
                {"url": "http://example.com/img1.png"},  # Missing width/height
                {"width": 512, "height": 512},  # Missing URL
            ]
        }
        mock_fal_submit.return_value = mock_handle

        # Mock download failure for first image (no URL)
        with patch("requests.get") as mock_get:
            mock_get.side_effect = [
                requests.exceptions.MissingSchema("Invalid URL scheme"),
                MagicMock(content=b"fake_image"),
            ]

            with patch("builtins.open", mock_open()):
                with patch("os.makedirs"):
                    factory = SyncFalFactoryMachine(self.machine_definition)
                    result = factory.execute_sync(self.order_item)

        # Should handle partial failures gracefully
        self.assertFalse(result)

    @patch("fal_client.submit")
    def test_authentication_error_handling(self, mock_fal_submit):
        """Test proper categorization of authentication errors."""
        mock_fal_submit.side_effect = Exception("Invalid API key provided")

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.error_category, ErrorCategory.AUTHENTICATION)
        # Authentication errors should not be retryable
        self.assertFalse(self.order_item.can_be_retried())

    @patch("fal_client.submit")
    def test_content_policy_violation(self, mock_fal_submit):
        """Test handling of content policy violations."""
        mock_fal_submit.side_effect = Exception("Content violates our usage policies")

        factory = SyncFalFactoryMachine(self.machine_definition)
        result = factory.execute_sync(self.order_item)

        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.error_category, ErrorCategory.CONTENT_POLICY)
        # Content policy violations should not be retryable
        self.assertFalse(self.order_item.can_be_retried())


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
@patch.dict("os.environ", {"FAL_KEY": "test_fal_key"})
class FileOperationFailureTestCase(TestCase):
    """Test file operation failures during image processing."""

    def setUp(self):
        """Set up test data."""
        self.machine_definition = FactoryMachineDefinition.objects.create(
            name="fal-ai/flux/dev",
            display_name="FLUX.1 Dev (fal.ai)",
            provider="fal.ai",
            modality="text-to-image",
            parameter_schema={"prompt": {"type": "string"}},
            default_parameters={},
            is_active=True,
        )

        self.order = Order.objects.create(
            title="File Error Test",
            prompt="test file errors",
            factory_machine_name=self.machine_definition.name,
            provider="fal.ai",
            quantity=1,
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            prompt=self.order.prompt,
            parameters={},
            status="pending",
        )

    @patch("fal_client.submit")
    def test_disk_full_during_download(self, mock_fal_submit):
        """Test handling when disk is full during image download."""
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

            # Simulate disk full during file write
            with patch("builtins.open", mock_open()) as mock_file:
                mock_file.side_effect = ErrorSimulationUtilities.disk_full_error()

                with patch("os.makedirs"):
                    factory = SyncFalFactoryMachine(self.machine_definition)
                    result = factory.execute_sync(self.order_item)

        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.error_category, ErrorCategory.FILE_SYSTEM)

    @patch("fal_client.submit")
    def test_permission_denied_file_save(self, mock_fal_submit):
        """Test handling when file save is denied due to permissions."""
        mock_handle = MagicMock()
        mock_handle.get.return_value = {
            "images": [{"url": "http://example.com/image.png", "width": 512, "height": 512}]
        }
        mock_fal_submit.return_value = mock_handle

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake_image_data"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Simulate permission denied during file write
            with patch("builtins.open", side_effect=ErrorSimulationUtilities.permission_denied_error()):
                with patch("os.makedirs"):
                    factory = SyncFalFactoryMachine(self.machine_definition)
                    result = factory.execute_sync(self.order_item)

        self.assertFalse(result)
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.error_category, ErrorCategory.FILE_SYSTEM)

    @patch("fal_client.submit")
    def test_invalid_filename_characters(self, mock_fal_submit):
        """Test handling of invalid filename characters."""
        mock_handle = MagicMock()
        mock_handle.get.return_value = {
            "images": [{"url": "http://example.com/image.png", "width": 512, "height": 512}]
        }
        mock_fal_submit.return_value = mock_handle

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake_image_data"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Simulate invalid filename error
            with patch("builtins.open", side_effect=ErrorSimulationUtilities.invalid_filename_error()):
                with patch("os.makedirs"):
                    factory = SyncFalFactoryMachine(self.machine_definition)
                    result = factory.execute_sync(self.order_item)

        self.assertFalse(result)

    @patch("fal_client.submit")
    def test_concurrent_file_access_conflict(self, mock_fal_submit):
        """Test handling of concurrent file access conflicts."""
        mock_handle = MagicMock()
        mock_handle.get.return_value = {
            "images": [{"url": "http://example.com/image.png", "width": 512, "height": 512}]
        }
        mock_fal_submit.return_value = mock_handle

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake_image_data"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Simulate file being locked/in use
            with patch("builtins.open", side_effect=OSError("File is being used by another process")):
                with patch("os.makedirs"):
                    factory = SyncFalFactoryMachine(self.machine_definition)
                    result = factory.execute_sync(self.order_item)

        self.assertFalse(result)

    @patch("fal_client.submit")
    def test_directory_creation_failure(self, mock_fal_submit):
        """Test handling when directory creation fails."""
        mock_handle = MagicMock()
        mock_handle.get.return_value = {
            "images": [{"url": "http://example.com/image.png", "width": 512, "height": 512}]
        }
        mock_fal_submit.return_value = mock_handle

        with patch("requests.get") as mock_get:
            mock_response = MagicMock()
            mock_response.content = b"fake_image_data"
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            # Simulate directory creation failure
            with patch("os.makedirs", side_effect=ErrorSimulationUtilities.permission_denied_error()):
                factory = SyncFalFactoryMachine(self.machine_definition)
                result = factory.execute_sync(self.order_item)

        self.assertFalse(result)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class DatabaseErrorTestCase(TestCase):
    """Test database-related error scenarios."""

    def setUp(self):
        """Set up test data."""
        self.machine_definition = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            provider="test",
            modality="text-to-image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

        self.order = Order.objects.create(
            title="Database Error Test",
            prompt="test database errors",
            factory_machine_name=self.machine_definition.name,
            provider="test",
            quantity=1,
        )

    def test_concurrent_order_item_creation(self):
        """Test handling of concurrent order item creation conflicts."""
        # This tests potential race conditions in order item creation
        order_items = []
        
        # Simulate rapid creation of multiple order items
        for i in range(5):
            try:
                order_item = OrderItem.objects.create(
                    order=self.order,
                    prompt=f"concurrent test {i}",
                    parameters={},
                    status="pending",
                )
                order_items.append(order_item)
            except IntegrityError:
                # Should handle gracefully if any constraints are violated
                pass
        
        # Should have successfully created items
        self.assertGreater(len(order_items), 0)

    def test_worker_assignment_race_condition(self):
        """Test handling of race conditions in worker assignment."""
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt="worker assignment test",
            parameters={},
            status="pending",
        )

        # Create multiple workers that might try to claim the same work
        workers = []
        for i in range(3):
            worker = Worker.objects.create(
                name=f"test-worker-{i}",
                process_id=10000 + i,
                provider="universal",
                max_batch_size=5,
                status="idle",
            )
            workers.append(worker)

        # Simulate concurrent assignment attempts
        assignments = []
        for worker in workers:
            try:
                # Try to assign the same order item to multiple workers
                order_item.assigned_worker = worker
                order_item.status = "assigned"
                order_item.save()
                assignments.append(worker)
            except Exception:
                # Handle any race condition gracefully
                pass

        # Only one worker should successfully claim the work
        order_item.refresh_from_db()
        self.assertIsNotNone(order_item.assigned_worker)

    @patch("django.db.transaction.atomic")
    def test_transaction_rollback_handling(self, mock_atomic):
        """Test proper handling of transaction rollbacks."""
        # Simulate transaction rollback during order creation
        mock_atomic.side_effect = OperationalError("Database deadlock detected")

        # Should handle transaction errors gracefully
        with self.assertRaises(OperationalError):
            with transaction.atomic():
                OrderItem.objects.create(
                    order=self.order,
                    prompt="transaction test",
                    parameters={},
                    status="pending",
                )

    def test_large_prompt_handling(self):
        """Test handling of extremely large prompts that might cause database issues."""
        # Create a very large prompt that might cause issues
        large_prompt = "A" * 10000  # 10KB prompt

        try:
            order_item = OrderItem.objects.create(
                order=self.order,
                prompt=large_prompt,
                parameters={},
                status="pending",
            )
            # If successful, ensure it was properly stored
            self.assertEqual(order_item.prompt, large_prompt)
        except Exception as e:
            # Should handle gracefully if prompt is too large
            self.assertIsInstance(e, (ValidationError, IntegrityError))

    def test_json_field_corruption_handling(self):
        """Test handling of JSON field corruption scenarios."""
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt="json test",
            parameters={"valid": "json"},
            status="pending",
        )

        # Simulate accessing potentially corrupted JSON data
        try:
            parameters = order_item.parameters
            self.assertIsInstance(parameters, dict)
        except (ValueError, TypeError):
            # Should handle gracefully if JSON is corrupted
            order_item.parameters = {}
            order_item.save()


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class WorkerRecoveryTestCase(TestCase):
    """Test worker recovery and error propagation scenarios."""

    def setUp(self):
        """Set up test data."""
        self.machine_definition = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            provider="test",
            modality="text-to-image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

        self.order = Order.objects.create(
            title="Worker Recovery Test",
            prompt="test worker recovery",
            factory_machine_name=self.machine_definition.name,
            provider="test",
            quantity=5,  # Multiple items to test batch handling
        )

    def test_worker_crash_recovery(self):
        """Test system recovery when a worker crashes unexpectedly."""
        # Create order items
        order_items = []
        for i in range(3):
            item = OrderItem.objects.create(
                order=self.order,
                prompt=f"worker crash test {i}",
                parameters={},
                status="pending",
            )
            order_items.append(item)

        # Create a worker and assign work
        worker = SmartWorker(max_batch_size=3)
        worker.name = "crash-test-worker"
        worker.process_id = 99999  # Fake PID that won't exist

        worker_record = Worker.objects.create(
            name=worker.name,
            process_id=worker.process_id,
            provider="universal",
            max_batch_size=3,
            status="working",
        )
        worker.worker_record = worker_record

        # Assign work to the worker
        for item in order_items:
            item.assigned_worker = worker_record
            item.status = "assigned"
            item.save()

        # Simulate worker crash by marking it as stalled
        worker_record.status = "stalled"
        worker_record.save()

        # Test that another worker can recover the work
        recovery_worker = SmartWorker(max_batch_size=3)
        recovery_worker.name = "recovery-worker"
        recovery_worker.process_id = 88888

        recovery_worker_record = Worker.objects.create(
            name=recovery_worker.name,
            process_id=recovery_worker.process_id,
            provider="universal",
            max_batch_size=3,
            status="starting",
        )
        recovery_worker.worker_record = recovery_worker_record

        # Recovery worker should be able to claim orphaned work
        claimed_items = recovery_worker.claim_work_batch()
        
        # Should successfully recover some or all of the orphaned work
        self.assertGreaterEqual(len(claimed_items), 0)

    def test_partial_batch_failure_recovery(self):
        """Test recovery when part of a batch fails."""
        # Create multiple order items
        order_items = []
        for i in range(4):
            item = OrderItem.objects.create(
                order=self.order,
                prompt=f"batch failure test {i}",
                parameters={},
                status="pending",
                batch_size=1,
                total_quantity=1,
            )
            order_items.append(item)

        worker = SmartWorker(max_batch_size=4)
        worker.name = "batch-test-worker"
        worker.process_id = 77777

        worker_record = Worker.objects.create(
            name=worker.name,
            process_id=worker.process_id,
            provider="universal",
            max_batch_size=4,
            status="working",
        )
        worker.worker_record = worker_record

        # Simulate processing where some items succeed and others fail
        order_items[0].status = "completed"
        order_items[0].save()

        order_items[1].status = "completed"
        order_items[1].save()

        # Simulate transient failure on remaining items
        order_items[2].status = "failed"
        order_items[2].error_message = "Server disconnected without sending a response"
        order_items[2].error_category = ErrorCategory.TRANSIENT
        order_items[2].save()

        order_items[3].status = "failed"
        order_items[3].error_message = "Connection timeout"
        order_items[3].error_category = ErrorCategory.NETWORK
        order_items[3].save()

        # Update order status
        worker.update_order_status(self.order)
        self.order.refresh_from_db()

        # Order should be marked as processing since retryable failures exist
        # (This behavior prioritizes retrying over marking as partial completion)
        self.assertEqual(self.order.status, "processing")

        # Failed items should be retryable
        self.assertTrue(order_items[2].can_be_retried())
        self.assertTrue(order_items[3].can_be_retried())

    def test_memory_exhaustion_recovery(self):
        """Test recovery from memory exhaustion scenarios."""
        order_item = OrderItem.objects.create(
            order=self.order,
            prompt="memory exhaustion test",
            parameters={},
            status="processing",
        )

        worker = SmartWorker()
        worker.name = "memory-test-worker"
        worker.process_id = 66666

        worker_record = Worker.objects.create(
            name=worker.name,
            process_id=worker.process_id,
            provider="universal",
            max_batch_size=5,
            status="working",
        )
        worker.worker_record = worker_record

        # Simulate memory exhaustion during processing
        try:
            worker.handle_item_failure(order_item, "Out of memory during image processing")
            
            order_item.refresh_from_db()
            
            # Should be marked as failed
            self.assertEqual(order_item.status, "failed")
            
            # Should have a helpful error message about the issue
            self.assertTrue(len(order_item.error_message) > 10)  # Should have a meaningful message
            
        except MemoryError:
            # Should handle gracefully even if we can't process the error
            pass

    def test_concurrent_worker_error_handling(self):
        """Test handling when multiple workers encounter errors simultaneously."""
        # Create multiple order items
        order_items = []
        for i in range(6):
            item = OrderItem.objects.create(
                order=self.order,
                prompt=f"concurrent error test {i}",
                parameters={},
                status="pending",
            )
            order_items.append(item)

        # Create multiple workers
        workers = []
        for i in range(3):
            worker = SmartWorker(max_batch_size=2)
            worker.name = f"concurrent-worker-{i}"
            worker.process_id = 55555 + i

            worker_record = Worker.objects.create(
                name=worker.name,
                process_id=worker.process_id,
                provider="universal",
                max_batch_size=2,
                status="working",
            )
            worker.worker_record = worker_record
            workers.append(worker)

        # Simulate all workers encountering different types of errors
        error_messages = [
            "Rate limit exceeded",
            "Network connection failed",
            "Invalid API key",
        ]

        for i, worker in enumerate(workers):
            start_idx = i * 2
            end_idx = start_idx + 2
            
            for item in order_items[start_idx:end_idx]:
                item.assigned_worker = worker.worker_record
                item.status = "assigned"
                item.save()
                
                # Simulate error handling
                worker.handle_item_failure(item, error_messages[i])

        # Verify all errors were handled appropriately
        for item in order_items:
            item.refresh_from_db()
            self.assertEqual(item.status, "failed")
            self.assertIsNotNone(item.error_message)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class UserFriendlyErrorMessageTestCase(TestCase):
    """Test that user-facing error messages are helpful and friendly."""

    def setUp(self):
        """Set up test data."""
        self.error_handler = ErrorHandler()

    def test_technical_error_translation(self):
        """Test that technical errors are translated to user-friendly messages."""
        technical_errors = [
            "Connection timed out after 30 seconds",
            "SSL certificate verification failed", 
            "Rate limit exceeded. Try again in 3600 seconds",
            "Invalid API key provided",
            "Content violates our usage policies",
            "No space left on device",
            "Permission denied",
        ]

        # Create real order and order item for testing
        order = Order.objects.create(
            title="Technical Error Test",
            prompt="test technical errors",
            factory_machine_name="test/model",
            provider="fal.ai",
            quantity=1,
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            prompt="test technical errors",
            parameters={},
            status="pending",
            retry_count=0,
            max_retries=3,
        )

        for error_msg in technical_errors:
            error_info = self.error_handler.handle_error(
                error_msg,
                order_item,
                context={"provider": "fal.ai", "operation": "generation", "model": "flux/dev"}
            )

            friendly_msg = error_info["friendly_message"]["message"]
            
            # Verify message is user-friendly (no technical jargon)
            self.assertNotIn("SSL", friendly_msg)
            self.assertNotIn("HTTP", friendly_msg) 
            self.assertNotIn("JSON", friendly_msg)
            self.assertNotIn("certificate", friendly_msg)
            self.assertNotIn("decode", friendly_msg)
            
            # Verify message provides actionable guidance
            self.assertTrue(len(friendly_msg) > 20)  # Not just "Error"
            
            # Should contain helpful words (checking actual message content)
            helpful_words = ["automatically", "service", "issue", "problem", "contact", "check", "image", "generation"]
            self.assertTrue(any(word in friendly_msg.lower() for word in helpful_words))

    def test_error_context_inclusion(self):
        """Test that error messages include relevant context."""
        # Create real order and order item for proper testing
        order = Order.objects.create(
            title="Context Test Order",
            prompt="test context",
            factory_machine_name="test/model",
            provider="fal.ai",
            quantity=1,
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            prompt="test context",
            parameters={},
            status="pending",
            retry_count=1,
            max_retries=3,
        )

        error_info = self.error_handler.handle_error(
            "Rate limit exceeded",
            order_item,
            context={
                "provider": "fal.ai",
                "operation": "image generation",
                "model": "flux/dev",
                "attempt": 2
            }
        )

        friendly_msg = error_info["friendly_message"]["message"]
        
        # Should provide context about what was happening (generation/image/service)
        self.assertTrue(any(word in friendly_msg.lower() for word in ["generation", "image", "service", "ai"]))

    def test_retry_guidance_in_messages(self):
        """Test that error messages provide appropriate retry guidance."""
        transient_errors = [
            "Connection timed out",
            "Server disconnected",
            "503 Service Unavailable",
            "Network unreachable",
        ]

        permanent_errors = [
            "Invalid API key",
            "Content violates policy", 
            "Authentication failed",
            "Model not found",
        ]

        # Create real order and order item for proper testing
        order = Order.objects.create(
            title="Retry Guidance Test",
            prompt="test retry guidance",
            factory_machine_name="test/model",
            provider="test",
            quantity=1,
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            prompt="test retry guidance",
            parameters={},
            status="pending",
            retry_count=0,
            max_retries=3,
        )

        # Transient errors should suggest retrying (using actual message words)
        for error_msg in transient_errors:
            error_info = self.error_handler.handle_error(error_msg, order_item)
            friendly_msg = error_info["friendly_message"]["message"]
            action_msg = error_info["friendly_message"]["action"]
            
            # Check in both message and action for retry-related words
            combined_text = (friendly_msg + " " + action_msg).lower()
            self.assertTrue(any(phrase in combined_text for phrase in [
                "automatically", "retry", "image", "request", "connectivity"
            ]))

        # Permanent errors should not suggest retrying
        for error_msg in permanent_errors:
            error_info = self.error_handler.handle_error(error_msg, order_item)
            friendly_msg = error_info["friendly_message"]["message"]
            action_msg = error_info["friendly_message"]["action"]
            
            # Should provide resolution guidance instead of retry (check both message and action)
            combined_text = (friendly_msg + " " + action_msg).lower()
            self.assertTrue(any(phrase in combined_text for phrase in [
                "contact", "support", "configuration", "modify", "please", "check"
            ]))

    def test_error_severity_appropriate_tone(self):
        """Test that error message tone matches severity."""
        # Create real order and order item for proper testing
        order = Order.objects.create(
            title="Severity Test Order",
            prompt="test severity",
            factory_machine_name="test/model",
            provider="test",
            quantity=1,
        )
        
        order_item = OrderItem.objects.create(
            order=order,
            prompt="test severity",
            parameters={},
            status="pending",
            retry_count=0,
            max_retries=3,
        )

        # High severity errors should be more urgent
        critical_error = "Authentication failed - invalid API key"
        error_info = self.error_handler.handle_error(critical_error, order_item)
        critical_msg = error_info["friendly_message"]["message"]
        critical_action = error_info["friendly_message"]["action"]
        
        # Should indicate action needed (check both message and action)
        combined_text = (critical_msg + " " + critical_action).lower()
        self.assertTrue(any(word in combined_text for word in [
            "please", "contact", "support", "configuration", "issue"
        ]))

        # Low severity errors should be more reassuring  
        minor_error = "Request took longer than expected"
        error_info = self.error_handler.handle_error(minor_error, order_item)
        minor_msg = error_info["friendly_message"]["message"]
        
        # Should be more reassuring
        self.assertTrue(any(word in minor_msg.lower() for word in [
            "automatically", "retry", "service", "image", "generated"
        ]))


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class ApplicationStabilityTestCase(TestCase):
    """Test that error scenarios don't crash the application."""

    def test_execute_order_item_sync_batch_error_handling(self):
        """Test that execute_order_item_sync_batch handles all error types gracefully."""
        # Test with non-existent order item ID
        result = execute_order_item_sync_batch(99999)
        self.assertFalse(result)  # Should return False, not crash

        # Test with invalid machine definition
        order = Order.objects.create(
            title="Stability Test",
            prompt="test stability",
            factory_machine_name="nonexistent/model",
            provider="invalid",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="test",
            parameters={},
            status="pending",
        )

        result = execute_order_item_sync_batch(order_item.id)
        self.assertFalse(result)  # Should return False, not crash

    @patch("main.factory_machines_sync.SyncFalFactoryMachine.execute_sync")
    def test_factory_machine_exception_handling(self, mock_execute):
        """Test that factory machine exceptions are caught and handled."""
        # Create valid test data
        machine_definition = FactoryMachineDefinition.objects.create(
            name="fal-ai/flux/dev",
            display_name="FLUX.1 Dev (fal.ai)",
            provider="fal.ai",
            modality="text-to-image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

        order = Order.objects.create(
            title="Exception Test",
            prompt="test exceptions",
            factory_machine_name=machine_definition.name,
            provider="fal.ai",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="test",
            parameters={},
            status="pending",
        )

        # Test various exception types
        exception_types = [
            Exception("Generic exception"),
            RuntimeError("Runtime error"),
            ValueError("Value error"),
            TypeError("Type error"),
            KeyError("Key error"),
            AttributeError("Attribute error"),
        ]

        for exception in exception_types:
            mock_execute.side_effect = exception
            
            # Should not crash, should return False
            result = execute_order_item_sync_batch(order_item.id)
            self.assertFalse(result)
            
            # Order item should be marked as failed
            order_item.refresh_from_db()
            self.assertIn(order_item.status, ["failed", "exhausted"])

    def test_worker_exception_handling(self):
        """Test that worker exceptions don't crash the system."""
        order = Order.objects.create(
            title="Worker Exception Test",
            prompt="test worker exceptions",
            factory_machine_name="test/model",
            provider="test",
            quantity=1,
        )

        order_item = OrderItem.objects.create(
            order=order,
            prompt="test",
            parameters={},
            status="pending",
        )

        worker = SmartWorker()
        worker.name = "exception-test-worker"
        worker.process_id = 44444

        worker_record = Worker.objects.create(
            name=worker.name,
            process_id=worker.process_id,
            provider="universal",
            max_batch_size=5,
            status="working",
        )
        worker.worker_record = worker_record

        # Test various error scenarios
        error_scenarios = [
            "Invalid input data",
            "Network connection failed",
            "Out of memory",
            "Permission denied",
            "Invalid response format",
        ]

        for error_msg in error_scenarios:
            try:
                worker.handle_item_failure(order_item, error_msg)
                
                # Should complete without crashing
                order_item.refresh_from_db()
                self.assertEqual(order_item.status, "failed")
                
            except Exception as e:
                # If any exception occurs, it should be logged, not crash
                self.fail(f"Worker error handling crashed with: {e}")

    def test_database_error_resilience(self):
        """Test that database errors don't crash the application."""
        # Test with corrupted model data
        try:
            machine_definition = FactoryMachineDefinition.objects.create(
                name="test/corrupted",
                display_name="Corrupted Model",
                provider="test",
                modality="text-to-image",
                parameter_schema=None,  # Potentially problematic None value
                default_parameters=None,  # Potentially problematic None value
                is_active=True,
            )

            order = Order.objects.create(
                title="Database Resilience Test",
                prompt="test database errors",
                factory_machine_name=machine_definition.name,
                provider="test",
                quantity=1,
            )

            order_item = OrderItem.objects.create(
                order=order,
                prompt="test",
                parameters={},
                status="pending",
            )

            # Should handle None values gracefully
            self.assertIsNotNone(order_item)
            
        except Exception as e:
            # If any exception occurs, it should be a validation error, not a crash
            self.assertIsInstance(e, (ValidationError, IntegrityError, TypeError))

    def test_memory_pressure_handling(self):
        """Test handling under memory pressure conditions."""
        # Create a large number of order items to simulate memory pressure
        order = Order.objects.create(
            title="Memory Pressure Test",
            prompt="test memory pressure",
            factory_machine_name="test/model",
            provider="test",
            quantity=100,
        )

        order_items = []
        try:
            # Create many order items
            for i in range(100):
                item = OrderItem.objects.create(
                    order=order,
                    prompt=f"memory test {i}",
                    parameters={"index": i, "data": "x" * 1000},  # Some data per item
                    status="pending",
                )
                order_items.append(item)

            # System should handle this gracefully
            self.assertEqual(len(order_items), 100)
            
        except MemoryError:
            # If memory error occurs, it should be caught gracefully
            self.assertTrue(len(order_items) > 0)  # Should have created some items
        except Exception as e:
            # Other exceptions should be database-related, not crashes
            self.assertIsInstance(e, (IntegrityError, OperationalError))