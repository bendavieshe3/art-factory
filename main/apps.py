from django.apps import AppConfig
import sys
import logging

logger = logging.getLogger(__name__)


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "main"

    def ready(self):
        """Auto-start system components when Django starts."""
        # Skip during migrations and other management commands
        if self.is_management_command():
            return

        # Start foreman process for system monitoring
        self.start_foreman_if_needed()

    def is_management_command(self):
        """Check if Django is running a management command."""
        # Skip for manage.py commands except runserver
        if "manage.py" in sys.argv[0]:
            # Allow foreman to start for runserver
            if "runserver" in sys.argv:
                return False
            return True

        # Skip for migrations
        if any(arg in sys.argv for arg in ["migrate", "makemigrations", "test"]):
            return True

        return False

    def start_foreman_if_needed(self):
        """Ensure foreman process is running."""
        try:
            from .foreman import start_foreman_if_needed

            start_foreman_if_needed()
            logger.info("Foreman auto-start initiated from Django app config")
        except Exception as e:
            logger.error(f"Failed to start foreman from app config: {e}")
