"""
Comprehensive error handling system for Art Factory generation failures.
Implements provider-specific error handling, retry strategies, and user-friendly messaging.
"""

import logging
import re
from typing import Any, Dict, Tuple

logger = logging.getLogger(__name__)


class ErrorCategory:
    """Error category constants."""

    TRANSIENT = "transient"  # Can be retried immediately
    RATE_LIMITED = "rate_limited"  # Can be retried with delay
    AUTHENTICATION = "authentication"  # API key issues - permanent
    VALIDATION = "validation"  # Parameter issues - permanent
    CONTENT_POLICY = "content_policy"  # NSFW/policy violations - permanent
    PROVIDER_OUTAGE = "provider_outage"  # Service unavailable - temporary
    NETWORK = "network"  # Network connectivity issues - transient
    FILE_SYSTEM = "file_system"  # Local file operations - transient
    UNKNOWN = "unknown"  # Unclassified errors


class ErrorAnalyzer:
    """Analyzes errors and determines appropriate handling strategy."""

    # Provider-specific error patterns
    FAL_AI_PATTERNS = {
        ErrorCategory.RATE_LIMITED: [
            r"rate.*limit.*exceeded",
            r"quota.?exceeded",
            r"too.?many.?requests",
            r"429",
            r"rate.*limit",
        ],
        ErrorCategory.AUTHENTICATION: [
            r"invalid.?api.?key",
            r"unauthorized",
            r"authentication.?failed",
            r"401",
            r"forbidden",
            r"403",
        ],
        ErrorCategory.VALIDATION: [
            r"invalid.?parameter",
            r"bad.?request",
            r"400",
            r"validation.?error",
            r"parameter.?.*?required",
            r"invalid.?prompt",
        ],
        ErrorCategory.CONTENT_POLICY: [
            r"nsfw.?detected",
            r"content.*policy.*violation",
            r"content.*violates.*policies",
            r"inappropriate.?content",
            r"safety.?check.?failed",
            r"usage.*policies",
        ],
        ErrorCategory.TRANSIENT: [
            r"504.*gateway.*timeout",
            r"timeout.?occurred",
            r"request.?timeout",
            r"temporary.?failure",
            r"temporary.?network.?failure",
            r"try.?again",
        ],
        ErrorCategory.PROVIDER_OUTAGE: [
            r"service.?unavailable",
            r"502.?bad.?gateway",
            r"503.?service.?unavailable",
            r"internal.?server.?error",
            r"500",
            r"502",
            r"503",
            r"connection.?refused",
        ],
    }

    REPLICATE_PATTERNS = {
        ErrorCategory.RATE_LIMITED: [
            r"rate.?limit",
            r"too.?many.?requests",
            r"quota",
            r"429",
        ],
        ErrorCategory.AUTHENTICATION: [
            r"invalid.?token",
            r"unauthorized",
            r"401",
            r"authentication.?required",
        ],
        ErrorCategory.VALIDATION: [
            r"invalid.?input",
            r"bad.?request",
            r"400",
            r"validation.?failed",
            r"input.?.*?required",
        ],
        ErrorCategory.CONTENT_POLICY: [
            r"nsfw",
            r"inappropriate",
            r"safety.?filter",
            r"content.?blocked",
        ],
        ErrorCategory.PROVIDER_OUTAGE: [
            r"service.?unavailable",
            r"server.?error",
            r"502",
            r"503",
            r"504",
            r"500",
            r"connection.?refused",
        ],
        ErrorCategory.TRANSIENT: [
            r"timeout.?occurred",
            r"request.?timeout",
            r"temporary.?failure",
            r"temporary.?network.?failure",
            r"try.?again",
        ],
    }

    # Common network and system patterns (transient connectivity issues)
    NETWORK_PATTERNS = [
        r"connection.*timeout",
        r"timed.*out",
        r"connection.?reset",
        r"network.?unreachable",
        r"dns.?resolution.?failed",
        r"failed.?to.?resolve.?hostname",
        r"server.?disconnected",
        r"connection.?aborted",
        r"socket.?error",
        r"ssl.?certificate.?verification.?failed",
        r"ssl.?error",
        r"connection.?error",
        r"network.?error",
    ]

    # Transient errors that should be retried quickly
    TRANSIENT_PATTERNS = [
        r"temporary.*network.*failure",
        r"temporary.*failure",
        r"timeout.*occurred",
        r"request.*timeout",
        r"try.*again",
    ]

    FILE_SYSTEM_PATTERNS = [
        r"permission.?denied",
        r"disk.?full",
        r"no.?space.?left",
        r"file.?not.?found",
        r"directory.?not.?found",
        r"io.?error",
        r"disk.?error",
        r"invalid.?filename",
        r"file.?is.?being.?used",
    ]

    MEMORY_PATTERNS = [
        r"out.?of.?memory",
        r"memory.?error",
        r"insufficient.?memory",
        r"memory.?exhausted",
        r"resource.?temporarily.?unavailable",
    ]

    @classmethod
    def analyze_error(cls, error_message: str, provider: str = None) -> Tuple[ErrorCategory, bool, int]:
        """
        Analyze an error message and determine handling strategy.

        Returns:
            tuple: (category, should_retry, retry_delay_seconds)
        """
        if not error_message:
            return ErrorCategory.UNKNOWN, False, 0

        error_lower = error_message.lower()

        # Check file system errors first (universal)
        if cls._matches_patterns(error_lower, cls.FILE_SYSTEM_PATTERNS):
            return ErrorCategory.FILE_SYSTEM, True, 30  # Retry after 30 seconds

        # Check memory errors (universal)
        if cls._matches_patterns(error_lower, cls.MEMORY_PATTERNS):
            return ErrorCategory.TRANSIENT, True, 60  # Retry after 1 minute for memory issues

        # Check transient errors (universal)
        if cls._matches_patterns(error_lower, cls.TRANSIENT_PATTERNS):
            return ErrorCategory.TRANSIENT, True, 5  # Retry quickly for transient errors

        # Check network errors (universal)
        if cls._matches_patterns(error_lower, cls.NETWORK_PATTERNS):
            return ErrorCategory.NETWORK, True, 10  # Retry after 10 seconds

        # Provider-specific analysis
        provider_patterns = None
        if provider == "fal.ai":
            provider_patterns = cls.FAL_AI_PATTERNS
        elif provider == "replicate":
            provider_patterns = cls.REPLICATE_PATTERNS

        if provider_patterns:
            for category, patterns in provider_patterns.items():
                if cls._matches_patterns(error_lower, patterns):
                    return cls._get_retry_strategy(category)

        # If no specific pattern matches, treat as unknown
        return ErrorCategory.UNKNOWN, False, 0

    @classmethod
    def _matches_patterns(cls, text: str, patterns: list) -> bool:
        """Check if text matches any of the given regex patterns."""
        for pattern in patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False

    @classmethod
    def _get_retry_strategy(cls, category: ErrorCategory) -> Tuple[ErrorCategory, bool, int]:
        """Get retry strategy for a given error category."""
        strategies = {
            ErrorCategory.TRANSIENT: (category, True, 5),
            ErrorCategory.RATE_LIMITED: (category, True, 60),  # Wait 1 minute for rate limits
            ErrorCategory.AUTHENTICATION: (category, False, 0),  # Don't retry auth errors
            ErrorCategory.VALIDATION: (category, False, 0),  # Don't retry validation errors
            ErrorCategory.CONTENT_POLICY: (category, False, 0),  # Don't retry policy violations
            ErrorCategory.PROVIDER_OUTAGE: (category, True, 120),  # Wait 2 minutes for outages
            ErrorCategory.NETWORK: (category, True, 10),
            ErrorCategory.FILE_SYSTEM: (category, True, 30),
            ErrorCategory.UNKNOWN: (category, False, 0),
        }
        return strategies.get(category, (category, False, 0))


class UserFriendlyMessages:
    """Generates user-friendly error messages."""

    MESSAGES = {
        ErrorCategory.RATE_LIMITED: {
            "title": "Rate Limit Reached",
            "message": "The AI service is temporarily limiting requests. Your image will be generated automatically in a few minutes.",
            "action": "Please wait, we'll retry automatically.",
        },
        ErrorCategory.AUTHENTICATION: {
            "title": "Service Configuration Issue",
            "message": "There's a configuration issue with the AI service. Please contact support.",
            "action": "Contact support for assistance.",
        },
        ErrorCategory.VALIDATION: {
            "title": "Invalid Parameters",
            "message": "Some of the settings for your image generation are invalid.",
            "action": "Please check your prompt and settings, then try again.",
        },
        ErrorCategory.CONTENT_POLICY: {
            "title": "Content Policy Violation",
            "message": "Your prompt may contain content that violates the AI service's policies.",
            "action": "Please modify your prompt and try again.",
        },
        ErrorCategory.PROVIDER_OUTAGE: {
            "title": "Service Temporarily Unavailable",
            "message": "The AI service is experiencing technical difficulties.",
            "action": "We'll automatically retry your request when the service is available.",
        },
        ErrorCategory.NETWORK: {
            "title": "Connection Issue",
            "message": "There was a network connectivity issue while generating your image.",
            "action": "We'll automatically retry your request shortly.",
        },
        ErrorCategory.FILE_SYSTEM: {
            "title": "Storage Issue",
            "message": "There was a problem saving your generated image.",
            "action": "We'll automatically retry saving your image.",
        },
        ErrorCategory.UNKNOWN: {
            "title": "Unexpected Error",
            "message": "An unexpected error occurred while generating your image.",
            "action": "Please try again or contact support if the problem persists.",
        },
    }

    @classmethod
    def get_friendly_message(cls, category: ErrorCategory, technical_error: str = None) -> Dict[str, str]:
        """Get user-friendly message for an error category."""
        message_info = cls.MESSAGES.get(category, cls.MESSAGES[ErrorCategory.UNKNOWN])

        result = message_info.copy()
        if technical_error:
            result["technical_details"] = technical_error

        return result


class RetryCalculator:
    """Calculates retry delays with exponential backoff."""

    @classmethod
    def calculate_delay(cls, category: ErrorCategory, retry_count: int, base_delay: int = None) -> int:
        """
        Calculate retry delay with exponential backoff.

        Args:
            category: Error category
            retry_count: Current retry attempt (0-based)
            base_delay: Base delay from error analysis

        Returns:
            Delay in seconds before next retry
        """
        if base_delay is None:
            _, _, base_delay = ErrorAnalyzer._get_retry_strategy(category)

        if base_delay == 0:
            return 0  # No retry

        # Exponential backoff with jitter
        import random

        multiplier = 2**retry_count
        jitter = random.uniform(0.5, 1.5)  # nosec B311 - Not cryptographic

        delay = int(base_delay * multiplier * jitter)

        # Cap maximum delay
        max_delays = {
            ErrorCategory.RATE_LIMITED: 600,  # 10 minutes max
            ErrorCategory.PROVIDER_OUTAGE: 1800,  # 30 minutes max
            ErrorCategory.NETWORK: 300,  # 5 minutes max
            ErrorCategory.FILE_SYSTEM: 300,  # 5 minutes max
        }

        max_delay = max_delays.get(category, 300)
        return min(delay, max_delay)


class ErrorHandler:
    """Main error handling coordinator."""

    def __init__(self, provider: str = None):
        self.provider = provider
        self.analyzer = ErrorAnalyzer()

    def handle_error(self, error_message: str, order_item, context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Handle an error comprehensively.

        Args:
            error_message: The technical error message
            order_item: The OrderItem that failed
            context: Additional context (provider, operation, etc.)

        Returns:
            Dict with handling instructions
        """
        context = context or {}
        provider = context.get("provider", self.provider)

        # Analyze the error
        category, should_retry, base_delay = self.analyzer.analyze_error(error_message, provider)

        # Calculate retry delay if applicable
        retry_delay = 0
        if should_retry and order_item.retry_count < order_item.max_retries:
            retry_delay = RetryCalculator.calculate_delay(category, order_item.retry_count, base_delay)
        else:
            should_retry = False

        # Get user-friendly message
        friendly_message = UserFriendlyMessages.get_friendly_message(category, error_message)

        # Log the error with context
        self._log_error(error_message, category, order_item, context, should_retry, retry_delay)

        return {
            "category": category,
            "should_retry": should_retry,
            "retry_delay": retry_delay,
            "friendly_message": friendly_message,
            "technical_error": error_message,
        }

    def _log_error(
        self,
        error_message: str,
        category: ErrorCategory,
        order_item,
        context: Dict[str, Any],
        should_retry: bool,
        retry_delay: int,
    ):
        """Log error with comprehensive context."""
        from .models import LogEntry

        log_level = "INFO" if should_retry else "ERROR"
        log_message = f"Error in {context.get('operation', 'generation')}: {category}"

        extra_data = {
            "error_category": category,
            "should_retry": should_retry,
            "retry_delay": retry_delay,
            "retry_count": order_item.retry_count,
            "max_retries": order_item.max_retries,
            "provider": context.get("provider", self.provider),
            "operation": context.get("operation", "generation"),
            "technical_error": error_message,
        }

        LogEntry.objects.create(
            level=log_level,
            message=log_message,
            order_item=order_item,
            order=order_item.order,
            extra_data=extra_data,
        )
