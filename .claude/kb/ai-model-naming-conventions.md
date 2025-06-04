# AI Model Naming Conventions

## Overview
Consistent and informative model naming is crucial for user experience and system maintainability when working with multiple AI providers and model versions.

## Key Principles
1. **Include Version Numbers**: Always include the model version in display names
2. **Be Provider-Agnostic**: Don't include provider names in model display names
3. **Use Descriptive Names**: Help users understand what the model does
4. **Maintain Consistency**: Follow the same pattern across all models

## Naming Pattern
```
<Model Name> <Version> [<Key Feature>]
```

Examples:
- ✅ "SDXL 1.0"
- ✅ "Flux Schnell"
- ✅ "Stable Diffusion 3.5 Large"
- ✅ "Dreamshaper 8"
- ❌ "Replicate SDXL"
- ❌ "sdxl-model"
- ❌ "Model v1"

## Implementation Example
From Art Factory's factory machines:

```python
class ReplicateSDXLMachine(BaseImageFactoryMachine):
    display_name = "SDXL 1.0"  # Clean, versioned name
    model_id = "stability-ai/sdxl:7762fd07..."  # Technical identifier
    
class FalStableDiffusion35LargeMachine(BaseImageFactoryMachine):
    display_name = "Stable Diffusion 3.5 Large"
    model_id = "fal-ai/stable-diffusion-v35-large"

class ReplicateDreamshaper8Machine(BaseImageFactoryMachine):
    display_name = "Dreamshaper 8"  # Version number included
    model_id = "prompthero/dreamshaper:4d3c1e18..."
```

## Version Number Importance
Version numbers are critical because:
1. **Feature Differences**: Different versions have different capabilities
2. **Performance Variations**: Speed and quality can vary significantly
3. **Parameter Changes**: Supported parameters may differ between versions
4. **User Expectations**: Users often know specific versions they prefer

## Special Cases

### When Version is Part of Name
Some models include version in their name naturally:
- "SDXL" (already implies version)
- "Flux Schnell" (schnell indicates the fast variant)
- "Stable Diffusion 3.5" (version is integral)

### When to Add Qualifiers
Add descriptive qualifiers when helpful:
- Size variants: "Large", "Medium", "Small"
- Speed variants: "Fast", "Quality", "Schnell"
- Style variants: "Artistic", "Photorealistic", "Anime"

## Django Model Configuration
```python
class FactoryMachine(models.Model):
    display_name = models.CharField(
        max_length=100,
        help_text="User-friendly name with version (e.g., 'SDXL 1.0')"
    )
    model_id = models.CharField(
        max_length=200,
        help_text="Technical model identifier for API calls"
    )
    provider = models.CharField(
        max_length=50,
        choices=Provider.choices,
        help_text="Provider is stored separately, not in display name"
    )
```

## Fixture Example
```json
{
    "model": "main.factorymachine",
    "fields": {
        "display_name": "Dreamshaper 8",
        "model_id": "prompthero/dreamshaper:4d3c1e18...",
        "provider": "replicate",
        "modality": "image",
        "is_active": true
    }
}
```

## Best Practices
1. **Research Official Names**: Use the model creator's official naming
2. **Test User Understanding**: Ensure names are clear to your target audience
3. **Document Extensively**: Include model descriptions in help text
4. **Maintain Consistency**: All similar models should follow similar patterns
5. **Avoid Technical Jargon**: Unless your users are technical

## Anti-Patterns to Avoid
- Including provider names in display names
- Using internal codenames or IDs
- Omitting version numbers
- Using inconsistent capitalization
- Creating overly long names

## Migration Strategy
When updating existing model names:
1. Update display names in fixtures
2. Run migrations to update database
3. Communicate changes to users
4. Consider adding model descriptions

## Related Topics
- User interface design
- Model metadata management
- API versioning strategies

## Sources
- Common AI model naming patterns
- User experience research
- Art Factory implementation experience (2025-06-04)

## Local Context
This naming convention was established during the Art Factory project to ensure users could easily identify and select the appropriate AI models for their creative needs, regardless of which provider hosted the model.