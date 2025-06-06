"""
Test-specific settings for the AI Art Factory project.
This file is used when running tests to disable features that cause issues in testing.
"""
from .settings import *
import tempfile
import os

# Disable automatic worker spawning during tests
DISABLE_AUTO_WORKER_SPAWN = True

# Use in-memory database for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Use temporary directories for media and logs during tests
MEDIA_ROOT = tempfile.mkdtemp(prefix='art_factory_test_media_')
LOG_DIR = tempfile.mkdtemp(prefix='art_factory_test_logs_')

# Ensure logs directory setting is used if it exists
if hasattr(locals(), 'LOGS_DIR'):
    LOGS_DIR = LOG_DIR

# Disable logging during tests
import logging
logging.disable(logging.CRITICAL)

# Test timeout to prevent hanging tests
TEST_RUNNER_TIMEOUT = 30  # seconds

# Prevent file creation in production locations
STATICFILES_DIRS = []
STATIC_ROOT = tempfile.mkdtemp(prefix='art_factory_test_static_')