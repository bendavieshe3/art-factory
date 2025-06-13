"""
Production settings for Art Factory.

This file contains security-focused settings optimized for production deployment.
Use this by setting: DJANGO_SETTINGS_MODULE=ai_art_factory.production_settings
"""

import os
from pathlib import Path

from decouple import config

# Import base settings
from .settings import *  # noqa

# Production Security Settings
DEBUG = False

# Required security settings for production
SECRET_KEY = config("SECRET_KEY")  # Must be set in production
ALLOWED_HOSTS = config("ALLOWED_HOSTS", default="", cast=lambda v: [s.strip() for s in v.split(",")])

# Security middleware and headers
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Database Configuration for Production
# Supports PostgreSQL and MySQL for production use
DATABASE_URL = config("DATABASE_URL", default=None)
if DATABASE_URL:
    import dj_database_url

    DATABASES = {"default": dj_database_url.parse(DATABASE_URL)}
else:
    # Fallback to SQLite if no DATABASE_URL provided
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "production_db.sqlite3",
        }
    }

# Static and Media Files for Production
STATIC_ROOT = config("STATIC_ROOT", default=BASE_DIR / "staticfiles")
MEDIA_ROOT = config("MEDIA_ROOT", default=BASE_DIR / "media")

# Production API Keys (all required)
FAL_API_KEY = config("FAL_KEY")
REPLICATE_API_TOKEN = config("REPLICATE_API_TOKEN")
CIVITAI_API_KEY = config("CIVITAI_API_KEY", default=None)

# Production Logging Configuration
LOGS_DIR = config("LOGS_DIR", default=BASE_DIR / "logs", cast=Path)
os.makedirs(LOGS_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} {process:d} {thread:d} {message}",
            "style": "{",
        },
        "json": {
            "format": '{"level": "{levelname}", "time": "{asctime}", "module": "{module}", "message": "{message}"}',
            "style": "{",
        },
    },
    "handlers": {
        "file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "art_factory_production.log",
            "maxBytes": 50 * 1024 * 1024,  # 50 MB
            "backupCount": 10,
            "formatter": "json",  # JSON format for production
        },
        "worker_file": {
            "level": "INFO",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "workers_production.log",
            "maxBytes": 50 * 1024 * 1024,  # 50 MB
            "backupCount": 10,
            "formatter": "json",
        },
        "error_file": {
            "level": "ERROR",
            "class": "logging.handlers.RotatingFileHandler",
            "filename": LOGS_DIR / "errors_production.log",
            "maxBytes": 50 * 1024 * 1024,  # 50 MB
            "backupCount": 10,
            "formatter": "json",
        },
        "console": {
            "level": "WARNING",  # Reduced console logging in production
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
    },
    "loggers": {
        "django": {
            "handlers": ["file", "console"],
            "level": "INFO",
            "propagate": False,
        },
        "main.workers": {
            "handlers": ["worker_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "main.factory_machines": {
            "handlers": ["worker_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "main.factory_machines_sync": {
            "handlers": ["worker_file", "error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "main.error_handling": {
            "handlers": ["error_file"],
            "level": "INFO",
            "propagate": False,
        },
        "": {  # Root logger
            "handlers": ["file", "error_file"],
            "level": "WARNING",  # Only log warnings and errors at root level
        },
    },
}

# Performance and Optimization
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Cache Configuration (optional - can be added if needed)
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.redis.RedisCache',
#         'LOCATION': config('REDIS_URL', default='redis://127.0.0.1:6379/1'),
#     }
# }

# Email Configuration for Production (optional)
EMAIL_BACKEND = config("EMAIL_BACKEND", default="django.core.mail.backends.console.EmailBackend")
if EMAIL_BACKEND != "django.core.mail.backends.console.EmailBackend":
    EMAIL_HOST = config("EMAIL_HOST")
    EMAIL_PORT = config("EMAIL_PORT", cast=int)
    EMAIL_USE_TLS = config("EMAIL_USE_TLS", cast=bool)
    EMAIL_HOST_USER = config("EMAIL_HOST_USER")
    EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD")
    DEFAULT_FROM_EMAIL = config("DEFAULT_FROM_EMAIL")

# Application Settings
DISABLE_AUTO_WORKER_SPAWN = config("DISABLE_AUTO_WORKER_SPAWN", default=False, cast=bool)

# File Upload Settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# Security Headers
X_FRAME_OPTIONS = "DENY"
