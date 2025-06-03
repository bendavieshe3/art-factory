"""
Test-specific settings for the AI Art Factory project.
This file is used when running tests to disable features that cause issues in testing.
"""
from .settings import *

# Disable automatic worker spawning during tests
DISABLE_AUTO_WORKER_SPAWN = True

# Use in-memory database for tests
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# Disable logging during tests
import logging
logging.disable(logging.CRITICAL)