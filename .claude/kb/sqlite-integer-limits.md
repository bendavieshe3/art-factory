# SQLite Integer Limits and Seed Value Handling

## Overview
SQLite has specific limits for integer values that can cause issues when working with large numbers, particularly when using random seeds for AI generation models.

## Key Facts
- **SQLite Maximum Integer**: 9,223,372,036,854,775,807 (2^63 - 1)
- **Python's Random Seed Range**: Can generate much larger values
- **Common Issue**: OverflowError when storing large seed values in SQLite INTEGER fields

## Problem Scenario
When generating random seeds for AI models:
```python
import random
seed = random.randint(0, 2**32 - 1)  # Can still overflow in some cases
seed = random.randint(0, 2**64 - 1)  # Will definitely overflow SQLite
```

## Solution Pattern
Implement a `safe_seed_value()` method to ensure seeds stay within SQLite's limits:

```python
@staticmethod
def safe_seed_value(value):
    """Ensure seed value is within SQLite's integer range"""
    if value is None:
        return None
    
    # SQLite's maximum integer value
    MAX_SQLITE_INT = 9223372036854775807
    
    # Ensure the value is within bounds
    if value > MAX_SQLITE_INT:
        # Use modulo to keep the value in range while preserving randomness
        return value % MAX_SQLITE_INT
    elif value < -MAX_SQLITE_INT:
        return value % MAX_SQLITE_INT
    
    return value
```

## Implementation Example
From the Art Factory project:
```python
# In the factory machine's produce method
resolved_params = self.resolve_parameters(order_item)
if 'seed' in resolved_params and resolved_params['seed'] is not None:
    resolved_params['seed'] = self.safe_seed_value(resolved_params['seed'])
```

## Best Practices
1. **Always validate seed values** before storing in SQLite
2. **Use modulo operation** to preserve randomness while staying in range
3. **Consider using TEXT fields** for extremely large numbers if exact value preservation is critical
4. **Document the limitation** in model documentation

## Testing Considerations
```python
def test_safe_seed_value():
    # Test normal values
    assert safe_seed_value(12345) == 12345
    
    # Test overflow values
    large_seed = 2**64
    safe_seed = safe_seed_value(large_seed)
    assert safe_seed <= 9223372036854775807
    
    # Test None handling
    assert safe_seed_value(None) is None
```

## Related Topics
- Database field type selection
- Random number generation best practices
- Cross-database compatibility considerations

## Sources
- SQLite documentation on data types
- Python sqlite3 module documentation
- Art Factory debugging session (2025-06-04)

## Local Context
This issue was discovered in the Art Factory project when implementing seed parameters for AI image generation models. The solution allows for consistent seed handling across all provider implementations.