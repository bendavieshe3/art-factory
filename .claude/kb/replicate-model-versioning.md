# Replicate Model Versioning

## Topics Covered
- Replicate model version requirements
- Version hash vs default versions
- Troubleshooting 404 errors
- Implementation patterns

## Key Finding

Replicate models have different versioning requirements that can cause confusing 404 errors if not handled correctly.

### Models Requiring Version Hash
Some models on Replicate **require** a specific version hash to be included in the model identifier:

- **SDXL Models**: Must include version hash
  - ❌ Wrong: `stability-ai/sdxl`
  - ✅ Correct: `stability-ai/sdxl:7762fd07cf82c948538e41f63f77d685e02b063e37e496e96eefd46c929f9bdc`

### Models with Default Versions
Other models work with just the model name (they have a default version):

- **FLUX Models**: Work without version hash
  - ✅ Works: `black-forest-labs/flux-schnell`
  - ✅ Also works: `black-forest-labs/flux-schnell:5f24084160c9089501c1b3545d9be3c27883ae2239b6f412990e82d4a6210f8f`

## How to Find Version Hashes

1. Visit the model page on Replicate (e.g., https://replicate.com/stability-ai/sdxl)
2. Look at the Python example code
3. The version hash appears after the colon in the model identifier

## Testing Model Availability

```python
import replicate

# Test if model requires version hash
try:
    # Try without version
    model = replicate.models.get('stability-ai/sdxl')
    print(f'Latest version: {model.latest_version.id}')
except:
    print('Model requires version hash in run() call')

# Always check the model page for the correct format
```

## Implementation Patterns

### In Django Factory Machines
When adding new Replicate models to factory_machines.json:

1. Always check the Python example on the model's Replicate page
2. If the example includes a version hash, include it in the `name` field
3. Test the model with a simple API call before adding to fixtures

### Dynamic Version Resolution
```python
# For models that might update versions
try:
    model = replicate.models.get('owner/model-name')
    version = model.latest_version.id
    full_model_id = f"{model.owner}/{model.name}:{version}"
except:
    # Fall back to hardcoded version
    full_model_id = "owner/model-name:abc123..."
```

## Error Symptoms and Solutions

### 404 Errors
If you see these errors, you likely need to add a version hash:
- `404: The requested resource could not be found`
- `404: Model not found`

Even though the model appears in search results, it may still require a version hash to actually run.

### Debugging Steps
1. Check if model appears in `replicate.models.search('model-name')`
2. Visit the model's Replicate page and copy the exact identifier from Python examples
3. Test with `replicate.run()` using the full identifier
4. If still failing, check API token permissions

## Local Considerations

- Some Replicate accounts may have restricted access to certain models
- Version hashes can change when models are updated
- Consider storing version hashes in environment variables for easier updates
- Always test model availability before deploying to production

## Metadata
- **Last Updated**: 2025-06-03
- **Version**: Based on Replicate API behavior as of June 2025
- **Sources**: 
  - Direct experience debugging SDXL 404 errors in Art Factory project
  - https://replicate.com/stability-ai/sdxl
  - https://replicate.com/black-forest-labs/flux-schnell