"""
Tests for comprehensive error handling system.
"""

import os
import random
from unittest.mock import patch, MagicMock
from django.test import TestCase, override_settings
from django.utils import timezone

from .models import Order, OrderItem, FactoryMachineDefinition, LogEntry
from .error_handling import ErrorAnalyzer, ErrorCategory, UserFriendlyMessages, RetryCalculator, ErrorHandler


def get_test_pid():
    """Generate a unique test PID to avoid conflicts."""
    return os.getpid() + random.randint(10000, 99999)  # nosec B311


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class ErrorAnalyzerTestCase(TestCase):
    """Test error analysis and categorization."""

    def test_fal_ai_rate_limit_detection(self):
        """Test detection of fal.ai rate limit errors."""
        error_messages = [
            "Rate limit exceeded",
            "Too many requests",
            "quota exceeded",
            "429 Too Many Requests",
        ]

        for error_msg in error_messages:
            category, should_retry, delay = ErrorAnalyzer.analyze_error(error_msg, "fal.ai")
            self.assertEqual(category, ErrorCategory.RATE_LIMITED)
            self.assertTrue(should_retry)
            self.assertGreater(delay, 0)

    def test_authentication_error_detection(self):
        """Test detection of authentication errors."""
        error_messages = [
            "Invalid API key",
            "Unauthorized",
            "401 Unauthorized",
            "Authentication failed",
        ]

        for error_msg in error_messages:
            category, should_retry, delay = ErrorAnalyzer.analyze_error(error_msg, "fal.ai")
            self.assertEqual(category, ErrorCategory.AUTHENTICATION)
            self.assertFalse(should_retry)
            self.assertEqual(delay, 0)

    def test_network_error_detection(self):
        """Test detection of network errors."""
        error_messages = [
            "Connection timeout",
            "Network unreachable",
            "Server disconnected without sending a response",
            "Socket error",
        ]

        for error_msg in error_messages:
            category, should_retry, delay = ErrorAnalyzer.analyze_error(error_msg, "fal.ai")
            self.assertEqual(category, ErrorCategory.NETWORK)
            self.assertTrue(should_retry)
            self.assertGreater(delay, 0)

    def test_file_system_error_detection(self):
        """Test detection of file system errors."""
        error_messages = [
            "Permission denied",
            "Disk full",
            "No space left on device",
            "IO error",
        ]

        for error_msg in error_messages:
            category, should_retry, delay = ErrorAnalyzer.analyze_error(error_msg)
            self.assertEqual(category, ErrorCategory.FILE_SYSTEM)
            self.assertTrue(should_retry)
            self.assertGreater(delay, 0)

    def test_content_policy_error_detection(self):
        """Test detection of content policy violations."""
        error_messages = [
            "NSFW detected",
            "Content policy violation",
            "Inappropriate content",
            "Safety check failed",
        ]

        for error_msg in error_messages:
            category, should_retry, delay = ErrorAnalyzer.analyze_error(error_msg, "fal.ai")
            self.assertEqual(category, ErrorCategory.CONTENT_POLICY)
            self.assertFalse(should_retry)
            self.assertEqual(delay, 0)

    def test_unknown_error_handling(self):
        """Test handling of unrecognized errors."""
        error_msg = "Some random error that doesn't match any pattern"
        category, should_retry, delay = ErrorAnalyzer.analyze_error(error_msg, "fal.ai")
        self.assertEqual(category, ErrorCategory.UNKNOWN)
        self.assertFalse(should_retry)
        self.assertEqual(delay, 0)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class UserFriendlyMessagesTestCase(TestCase):
    """Test user-friendly error message generation."""

    def test_rate_limit_message(self):
        """Test rate limit user message."""
        message_info = UserFriendlyMessages.get_friendly_message(ErrorCategory.RATE_LIMITED)

        self.assertIn("title", message_info)
        self.assertIn("message", message_info)
        self.assertIn("action", message_info)
        self.assertEqual(message_info["title"], "Rate Limit Reached")
        self.assertIn("automatically", message_info["message"])

    def test_authentication_message(self):
        """Test authentication error user message."""
        message_info = UserFriendlyMessages.get_friendly_message(ErrorCategory.AUTHENTICATION)

        self.assertEqual(message_info["title"], "Service Configuration Issue")
        self.assertIn("configuration", message_info["message"])
        self.assertIn("support", message_info["action"])

    def test_content_policy_message(self):
        """Test content policy violation user message."""
        message_info = UserFriendlyMessages.get_friendly_message(ErrorCategory.CONTENT_POLICY)

        self.assertEqual(message_info["title"], "Content Policy Violation")
        self.assertIn("prompt", message_info["message"])
        self.assertIn("modify", message_info["action"])

    def test_technical_details_inclusion(self):
        """Test that technical details are included when provided."""
        technical_error = "Original technical error message"
        message_info = UserFriendlyMessages.get_friendly_message(ErrorCategory.UNKNOWN, technical_error)

        self.assertIn("technical_details", message_info)
        self.assertEqual(message_info["technical_details"], technical_error)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class RetryCalculatorTestCase(TestCase):
    """Test retry delay calculation with exponential backoff."""

    def test_exponential_backoff(self):
        """Test that retry delays increase exponentially."""
        base_delay = 10

        # Test multiple times to account for jitter
        delay_0_values = [RetryCalculator.calculate_delay(ErrorCategory.NETWORK, 0, base_delay) for _ in range(10)]
        delay_1_values = [RetryCalculator.calculate_delay(ErrorCategory.NETWORK, 1, base_delay) for _ in range(10)]

        # Average should show exponential growth despite jitter
        avg_delay_0 = sum(delay_0_values) / len(delay_0_values)
        avg_delay_1 = sum(delay_1_values) / len(delay_1_values)

        self.assertGreater(avg_delay_1, avg_delay_0)

    def test_maximum_delay_cap(self):
        """Test that delays are capped at reasonable maximums."""
        # Test with high retry count to trigger max delay
        delay = RetryCalculator.calculate_delay(ErrorCategory.RATE_LIMITED, 10, 60)

        # Should be capped at 10 minutes (600 seconds) for rate limits
        self.assertLessEqual(delay, 600)

    def test_no_retry_delay(self):
        """Test that non-retryable errors return 0 delay."""
        delay = RetryCalculator.calculate_delay(ErrorCategory.AUTHENTICATION, 0, 0)
        self.assertEqual(delay, 0)


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class ErrorHandlerIntegrationTestCase(TestCase):
    """Test the complete error handling workflow."""

    def setUp(self):
        """Set up test data."""
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            description="Test model for error handling",
            provider="fal.ai",
            modality="image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

        self.order = Order.objects.create(
            title="Test Order",
            prompt="test prompt",
            factory_machine_name=self.factory_machine.name,
            provider="fal.ai",
            quantity=1,
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            prompt="test prompt",
            parameters={},
            status="processing",
        )

    def test_rate_limit_error_handling(self):
        """Test complete handling of rate limit errors."""
        error_handler = ErrorHandler(provider="fal.ai")
        error_message = "Rate limit exceeded - too many requests"

        result = error_handler.handle_error(error_message, self.order_item)

        # Should be marked for retry
        self.assertEqual(result["category"], ErrorCategory.RATE_LIMITED)
        self.assertTrue(result["should_retry"])
        self.assertGreater(result["retry_delay"], 0)

        # Should have user-friendly message
        self.assertIn("friendly_message", result)
        self.assertEqual(result["friendly_message"]["title"], "Rate Limit Reached")

    def test_authentication_error_handling(self):
        """Test complete handling of authentication errors."""
        error_handler = ErrorHandler(provider="fal.ai")
        error_message = "Invalid API key provided"

        result = error_handler.handle_error(error_message, self.order_item)

        # Should NOT be marked for retry
        self.assertEqual(result["category"], ErrorCategory.AUTHENTICATION)
        self.assertFalse(result["should_retry"])
        self.assertEqual(result["retry_delay"], 0)

        # Should have user-friendly message
        self.assertIn("friendly_message", result)
        self.assertEqual(result["friendly_message"]["title"], "Service Configuration Issue")

    def test_log_entry_creation(self):
        """Test that error handling creates appropriate log entries."""
        error_handler = ErrorHandler(provider="fal.ai")
        error_message = "Network timeout occurred"

        # Clear existing logs
        LogEntry.objects.all().delete()

        result = error_handler.handle_error(error_message, self.order_item)

        # Should create a log entry
        log_entries = LogEntry.objects.all()
        self.assertEqual(log_entries.count(), 1)

        log_entry = log_entries.first()
        self.assertEqual(log_entry.order_item, self.order_item)
        self.assertEqual(log_entry.level, "INFO")  # INFO because it's retryable
        self.assertIn("error_category", log_entry.extra_data)
        self.assertEqual(log_entry.extra_data["error_category"], ErrorCategory.NETWORK)

    def test_context_information_logging(self):
        """Test that context information is properly logged."""
        error_handler = ErrorHandler(provider="fal.ai")
        error_message = "Test error"
        context = {
            "operation": "image_generation",
            "model": "test/model",
            "provider": "fal.ai",
        }

        # Clear existing logs
        LogEntry.objects.all().delete()

        result = error_handler.handle_error(error_message, self.order_item, context)

        log_entry = LogEntry.objects.first()
        self.assertEqual(log_entry.extra_data["provider"], "fal.ai")
        self.assertEqual(log_entry.extra_data["operation"], "image_generation")


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class FactoryMachineErrorHandlingTestCase(TestCase):
    """Test error handling in factory machines."""

    def setUp(self):
        """Set up test data."""
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="fal-ai/flux/dev",
            display_name="FLUX Dev",
            description="Test model",
            provider="fal.ai",
            modality="image",
            parameter_schema={},
            default_parameters={"width": 1024, "height": 1024},
            is_active=True,
        )

        self.order = Order.objects.create(
            title="Test Order",
            prompt="test prompt",
            factory_machine_name=self.factory_machine.name,
            provider="fal.ai",
            quantity=1,
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            prompt="test prompt",
            parameters={},
            status="pending",
        )

    @patch("fal_client.submit")
    def test_fal_factory_error_handling(self, mock_fal_submit):
        """Test error handling in SyncFalFactoryMachine."""
        from .factory_machines_sync import SyncFalFactoryMachine

        # Mock fal.ai to raise a rate limit error
        mock_fal_submit.side_effect = Exception("Rate limit exceeded")

        factory = SyncFalFactoryMachine(self.factory_machine)
        result = factory.execute_sync(self.order_item)

        # Should return False (failure)
        self.assertFalse(result)

        # Order item should be updated with friendly message
        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.status, "failed")
        self.assertIn("temporarily limiting", self.order_item.error_message)

    def test_file_creation_error_handling(self):
        """Test error handling during file creation."""
        from .factory_machines_sync import SyncFalFactoryMachine

        factory = SyncFalFactoryMachine(self.factory_machine)

        # Test with invalid file content that would cause save to fail
        with patch("builtins.open", side_effect=OSError("Permission denied")):
            try:
                factory._create_product(self.order_item, b"fake_image_data", "test_file.jpg", {"width": 1024, "height": 1024})
                self.fail("Should have raised an exception")
            except Exception as e:
                self.assertIn("Product creation failed", str(e))
                self.assertIn("Permission denied", str(e))


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class WorkerErrorHandlingTestCase(TestCase):
    """Test error handling in worker system."""

    def setUp(self):
        """Set up test data."""
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            provider="fal.ai",
            modality="image",
            parameter_schema={},
            default_parameters={},
            is_active=True,
        )

        self.order = Order.objects.create(
            title="Test Order",
            prompt="test prompt",
            factory_machine_name=self.factory_machine.name,
            provider="fal.ai",
            quantity=1,
        )

        self.order_item = OrderItem.objects.create(
            order=self.order,
            prompt="test prompt",
            parameters={},
            status="pending",
            max_retries=3,
        )

    def test_worker_error_categorization(self):
        """Test that workers properly categorize errors."""
        from .workers import SmartWorker
        from .models import Worker

        worker = SmartWorker(max_batch_size=1)

        # Create worker record
        test_pid = get_test_pid()
        worker.worker_record = Worker.objects.create(
            name=worker.name,
            process_id=test_pid,
            provider="universal",
            max_batch_size=1,
            status="working",
        )

        # Test rate limit error
        worker.handle_item_failure(self.order_item, "Rate limit exceeded")

        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.status, "failed")  # But retryable
        self.assertIn("temporarily limiting", self.order_item.error_message)

    def test_worker_permanent_failure_handling(self):
        """Test that workers handle permanent failures correctly."""
        from .workers import SmartWorker
        from .models import Worker

        worker = SmartWorker(max_batch_size=1)

        # Create worker record
        test_pid = get_test_pid()
        worker.worker_record = Worker.objects.create(
            name=worker.name,
            process_id=test_pid,
            provider="universal",
            max_batch_size=1,
            status="working",
        )

        # Test authentication error (permanent)
        worker.handle_item_failure(self.order_item, "Invalid API key")

        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.status, "failed")
        self.assertIn("configuration issue", self.order_item.error_message)

    def test_worker_retry_exhaustion(self):
        """Test worker handling when retries are exhausted."""
        from .workers import SmartWorker
        from .models import Worker

        # Set order item to already have max retries
        self.order_item.retry_count = 3
        self.order_item.save()

        worker = SmartWorker(max_batch_size=1)

        # Create worker record
        test_pid = get_test_pid()
        worker.worker_record = Worker.objects.create(
            name=worker.name,
            process_id=test_pid,
            provider="universal",
            max_batch_size=1,
            status="working",
        )

        # Test transient error with exhausted retries
        worker.handle_item_failure(self.order_item, "Connection timeout")

        self.order_item.refresh_from_db()
        self.assertEqual(self.order_item.status, "exhausted")
