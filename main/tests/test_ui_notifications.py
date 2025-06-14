"""
Tests for UI notification system (toast notifications, alerts, error banners).
"""

from django.test import Client, TestCase, override_settings

from main.models import FactoryMachineDefinition


@override_settings(DISABLE_AUTO_WORKER_SPAWN=True)
class UINotificationTestCase(TestCase):
    """Test the toast notification system and UI feedback mechanisms."""

    def setUp(self):
        """Set up test client and factory machine."""
        self.client = Client()
        self.factory_machine = FactoryMachineDefinition.objects.create(
            name="test/model",
            display_name="Test Model",
            description="Test model for UI testing",
            provider="test-provider",
            modality="image",
            parameter_schema={"width": 512, "height": 512},
            default_parameters={"width": 512, "height": 512, "enable_safety_checker": False},
            is_active=True,
        )

    def test_order_page_loads_with_toast_system(self):
        """Test that order page loads with toast notification system."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        # Check toast container is present
        self.assertContains(response, "toast-container")
        self.assertContains(response, 'id="toastContainer"')

        # Check toast JavaScript is loaded
        self.assertContains(response, "window.ToastNotification")
        self.assertContains(response, "ToastNotification.success")
        # Order page uses both toast notifications and error banner
        self.assertContains(response, "ToastNotification.error")

    def test_order_form_uses_toast_notifications(self):
        """Test that order form JavaScript uses toast notifications instead of alerts."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        # Check that old alert() calls are replaced with ToastNotification calls
        self.assertNotContains(response, "alert(")
        self.assertContains(response, "ToastNotification.success(")
        # Order page uses both toast notifications and error banner
        self.assertContains(response, "ToastNotification.error(")

        # Check toast message content
        self.assertContains(response, "Order Placed")
        self.assertContains(response, "Order Failed")
        self.assertContains(response, "Generation Complete")

    def test_no_alert_calls_in_templates(self):
        """Test that no JavaScript alert() calls remain in templates."""
        # Test all main template pages
        pages = ["/", "/inventory/", "/production/", "/settings/"]

        for page in pages:
            with self.subTest(page=page):
                response = self.client.get(page)
                if response.status_code == 200:  # Some pages might not exist yet
                    self.assertNotContains(response, "alert(", msg_prefix=f"Page {page} still contains alert() calls")

    def test_toast_css_classes_present(self):
        """Test that all necessary CSS classes for toasts are present."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        # Check main toast CSS classes
        self.assertContains(response, ".toast-container")
        self.assertContains(response, ".toast-notification")
        self.assertContains(response, ".toast-notification.show")
        self.assertContains(response, ".toast-notification.toast-success")
        self.assertContains(response, ".toast-notification.toast-error")
        self.assertContains(response, ".toast-notification.toast-warning")
        self.assertContains(response, ".toast-notification.toast-info")

        # Check toast component classes
        self.assertContains(response, ".toast-header")
        self.assertContains(response, ".toast-title")
        self.assertContains(response, ".toast-close")
        self.assertContains(response, ".toast-body")

    def test_toast_animations_configured(self):
        """Test that toast animations are properly configured."""
        response = self.client.get("/order/")
        self.assertEqual(response.status_code, 200)

        # Check animation CSS properties
        self.assertContains(response, "transform: translateX(100%)")
        self.assertContains(response, "transform: translateX(0)")
        self.assertContains(response, "transition: all 0.3s ease")
        self.assertContains(response, "opacity: 0")
        self.assertContains(response, "opacity: 1")