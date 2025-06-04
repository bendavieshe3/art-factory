# Parameter Merging Tests

## Overview

The `ParameterMergingTestCase` in `main/tests.py` contains comprehensive tests to ensure that factory machine parameter merging works correctly. These tests prevent critical regressions where safety check parameters and other machine defaults might not be applied to API calls.

## Why These Tests Are Critical

### The Problem We Solved

Previously, the factory machine implementations (`SyncFalFactoryMachine` and `SyncReplicateFactoryMachine`) were only using user-provided parameters when making API calls to external services. This meant:

1. **Safety check parameters were ignored** - Models were configured with `disable_safety_checker: true` or `enable_safety_checker: false` by default, but these defaults weren't being applied
2. **Other machine defaults were missing** - Parameters like guidance scale, inference steps, etc. weren't being applied if users didn't specify them
3. **Inconsistent behavior** - The same prompt might produce different results depending on whether the user specified all parameters

### The Fix

We modified both factory machine classes to properly merge parameters:

```python
# Before (BROKEN):
arguments = {
    'prompt': order_item.prompt,
    **order_item.parameters  # Only user parameters
}

# After (FIXED):
arguments = {
    'prompt': order_item.prompt,
    **self.machine_definition.default_parameters,  # Machine defaults first
    **order_item.parameters  # User overrides
}
```

## Test Coverage

The test suite covers:

### 1. Basic Parameter Merging
- **`test_fal_factory_machine_parameter_merging`** - Tests FLUX models with `enable_safety_checker: false`
- **`test_fal_sdxl_parameter_merging`** - Tests SDXL models with `disable_safety_checker: true`
- **`test_replicate_factory_machine_parameter_merging`** - Tests Replicate models

### 2. Safety Check Scenarios
- **Machine defaults are applied** when users don't specify safety settings
- **User overrides work** when users explicitly set safety parameters
- **Different safety parameter formats** (`enable_safety_checker` vs `disable_safety_checker`)

### 3. Edge Cases
- **`test_parameter_merging_preserves_all_defaults`** - Minimal user input gets all machine defaults
- **`test_parameter_merging_handles_missing_defaults_gracefully`** - Handles machines with empty defaults
- **`test_parameter_merging_with_negative_prompts`** - Negative prompts work with parameter merging

### 4. Integration Tests
- **`test_fal_execute_sync_uses_merged_parameters`** - Verifies actual API calls include merged parameters
- **`test_replicate_execute_sync_uses_merged_parameters`** - Same for Replicate API calls

## Critical Safety Check Parameters

### fal.ai Models
- **FLUX models**: Use `enable_safety_checker: false` (safety checks disabled)
- **SDXL models**: Use `disable_safety_checker: true` (safety checks disabled)

### Replicate Models
- **All models**: Use `disable_safety_checker: true` (safety checks disabled)

## Running the Tests

```bash
# Run all parameter merging tests
python manage.py test main.tests.ParameterMergingTestCase -v 2

# Run a specific test
python manage.py test main.tests.ParameterMergingTestCase.test_fal_sdxl_parameter_merging -v 2
```

## What These Tests Prevent

1. **Safety checker regression** - Ensures all models have safety checks disabled by default
2. **Missing machine defaults** - Ensures users get consistent results even with minimal parameters
3. **Parameter override failures** - Ensures users can still override defaults when needed
4. **API call parameter bugs** - Ensures the actual API calls include all necessary parameters

## When to Update These Tests

Update these tests when:

1. **Adding new factory machines** - Add test coverage for new models
2. **Changing parameter schemas** - Update expected parameter sets
3. **Modifying parameter merging logic** - Ensure tests still pass
4. **Adding new safety check parameters** - Add test cases for new safety configurations

## Files Modified by the Fix

- **`main/factory_machines_sync.py`** - Fixed parameter merging in both `SyncFalFactoryMachine` and `SyncReplicateFactoryMachine`
- **`main/tests.py`** - Added comprehensive `ParameterMergingTestCase`
- **`main/fixtures/factory_machines.json`** - Added safety check parameters to FLUX models
- **`main/management/commands/load_seed_data.py`** - Updated seed data with safety check parameters

The parameter merging tests serve as a permanent safety net to ensure that this critical functionality continues to work correctly as the codebase evolves.