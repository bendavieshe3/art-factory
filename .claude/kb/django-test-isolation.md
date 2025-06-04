# Django Test Isolation Patterns

## Overview
Proper test isolation is crucial for reliable test suites, especially when dealing with background tasks, external services, and shared state.

## Key Concepts
- **Test Independence**: Each test should run in isolation
- **State Reset**: Database and cache state should reset between tests
- **External Service Mocking**: Prevent real API calls during tests
- **Background Task Control**: Manage async/background processes

## Common Isolation Issues

### 1. Background Workers
Problem: Auto-spawning workers can interfere with tests
```python
# In models.py - problematic pattern
def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    if self.status == 'pending':
        process_order_task.delay(self.id)  # Auto-spawns worker
```

### 2. Shared State
Problem: Global variables or class attributes persist between tests
```python
# Problematic
class MyFactory:
    _instance_count = 0  # Persists between tests
```

### 3. External API Calls
Problem: Tests make real API calls, causing flakiness
```python
# Problematic
def test_image_generation():
    response = requests.post('https://api.example.com/generate')
```

## Solution Patterns

### 1. Disable Auto-Worker Spawning
Use settings to control background task behavior:

```python
# test_settings.py
from .settings import *

# Disable automatic worker spawning in tests
DISABLE_AUTO_WORKER_SPAWN = True

# Optionally use synchronous task execution
CELERY_TASK_ALWAYS_EAGER = True
```

In your models:
```python
# models.py
from django.conf import settings

def save(self, *args, **kwargs):
    super().save(*args, **kwargs)
    if self.status == 'pending' and not getattr(settings, 'DISABLE_AUTO_WORKER_SPAWN', False):
        process_order_task.delay(self.id)
```

### 2. Use Django's TestCase
Django's TestCase provides automatic isolation:
```python
from django.test import TestCase

class MyTest(TestCase):
    # Database is reset between tests
    # Transactions are rolled back
    
    def setUp(self):
        # Fresh state for each test
        pass
```

### 3. Mock External Services
```python
from unittest.mock import patch, MagicMock

class TestImageGeneration(TestCase):
    @patch('main.factory_machines.fal.run')
    def test_fal_image_generation(self, mock_fal_run):
        # Configure mock
        mock_fal_run.return_value = {
            'images': [{'url': 'http://test.com/image.png'}]
        }
        
        # Test runs without real API call
        result = generate_image()
        mock_fal_run.assert_called_once()
```

### 4. Fixture Isolation
```python
class TestWithFixtures(TestCase):
    fixtures = ['test_data.json']  # Loaded fresh for each test
    
    def test_something(self):
        # Fixture data is isolated to this test
        pass
```

## Testing Background Tasks

### Synchronous Testing
```python
# Force synchronous execution for testing
from django.test import override_settings

@override_settings(CELERY_TASK_ALWAYS_EAGER=True)
class TestBackgroundTasks(TestCase):
    def test_task_execution(self):
        # Tasks run synchronously in test
        result = my_task.delay()
        self.assertEqual(result.get(), expected_value)
```

### Manual Task Testing
```python
class TestTasks(TestCase):
    def test_task_logic(self):
        # Test task logic directly without queueing
        from main.tasks import process_order_task
        
        order = Order.objects.create(...)
        result = process_order_task(order.id)
        self.assertTrue(result)
```

## Best Practices

### 1. Use Test-Specific Settings
```python
# manage.py test --settings=ai_art_factory.test_settings
```

### 2. Clear Caches
```python
from django.core.cache import cache

class MyTest(TestCase):
    def setUp(self):
        cache.clear()
```

### 3. Reset Singleton State
```python
class MyTest(TestCase):
    def tearDown(self):
        # Reset any singleton instances
        MyFactory._instance = None
```

### 4. Use Transactions
```python
from django.test import TransactionTestCase

class MyTransactionTest(TransactionTestCase):
    # For tests that need real transactions
    pass
```

## Common Pitfalls
1. **Forgetting to mock time**: Use `freezegun` for time-dependent tests
2. **File system side effects**: Clean up created files in tearDown
3. **Thread safety**: Be careful with multi-threaded code in tests
4. **Order dependencies**: Tests should not depend on execution order

## Testing Checklist
- [ ] All external API calls are mocked
- [ ] Background tasks are controlled (eager or disabled)
- [ ] Database state resets between tests
- [ ] No global state pollution
- [ ] Files/resources are cleaned up
- [ ] Time-dependent code is controlled
- [ ] Random values are seeded for reproducibility

## Related Topics
- Django testing framework
- Mock and patch strategies
- Continuous integration setup
- Test database configuration

## Sources
- Django testing documentation
- Python unittest.mock documentation
- Art Factory test implementation (2025-06-04)

## Local Context
These patterns were refined during Art Factory development, particularly around the worker system and background task processing. The DISABLE_AUTO_WORKER_SPAWN setting proved essential for reliable test execution.