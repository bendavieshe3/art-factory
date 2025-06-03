# Batch Generation APIs - fal.ai and Replicate

## Topics Covered
- Batch generation parameters for fal.ai
- Batch generation parameters for Replicate
- Implementation details and limitations
- Performance considerations
- Code examples

## Main Content

### fal.ai Batch Generation

fal.ai supports batch generation through the `num_images` parameter:

**Parameter Details:**
- **Name**: `num_images`
- **Type**: Integer
- **Default**: 1
- **Range**: 1-4 (maximum of 4 images per request)
- **Description**: "The number of images to generate. Default value: 1"

**Key Characteristics:**
- Higher batch sizes increase generation time
- Single API call generates multiple images
- Results returned as array in the `images` field
- Each image includes metadata (width, height, url)

**Example Usage:**
```python
import fal_client

result = fal_client.submit(
    "fal-ai/flux/dev",
    arguments={
        "prompt": "a beautiful landscape",
        "num_images": 4,  # Generate 4 images
        "width": 1024,
        "height": 1024
    }
)

# Process multiple images
for image in result['images']:
    print(f"Image URL: {image['url']}")
    print(f"Dimensions: {image['width']}x{image['height']}")
```

### Replicate Batch Generation

Replicate supports batch generation through the `num_outputs` parameter:

**Parameter Details:**
- **Name**: `num_outputs`
- **Type**: Integer
- **Default**: 1
- **Range**: 1-4 (maximum of 4 outputs per request)
- **Description**: "Number of outputs to generate"

**Key Characteristics:**
- Returns multiple FileOutput objects or URLs
- Lower batch sizes perform faster than higher ones
- Some models may use `batch_size` instead of `num_outputs`
- Results returned as iterable list

**Example Usage:**
```python
import replicate

output = replicate.run(
    "black-forest-labs/flux-schnell",
    input={
        "prompt": "a majestic lion",
        "num_outputs": 4,  # Generate 4 images
        "width": 1024,
        "height": 1024
    }
)

# Process multiple outputs
for idx, file_output in enumerate(output):
    with open(f'output_{idx}.png', 'wb') as f:
        f.write(file_output.read())
```

### Performance Considerations

1. **Generation Time**: Both providers note that higher batch sizes increase processing time
2. **API Limits**: Both providers limit batch size to 4 images per request
3. **Cost Efficiency**: Batch requests can be more cost-effective than individual calls
4. **Resource Usage**: Batch processing uses more compute resources in a single call

### Implementation Strategy for Art Factory

To generate more than 4 images efficiently:

1. **Calculate Batches**: Divide total requested images by max batch size (4)
   - Example: 12 images = 3 API calls with `num_images/num_outputs = 4`
   
2. **Sequential Calls**: Make multiple API calls with maximum batch size
   ```python
   total_images = 12
   batch_size = 4
   num_batches = (total_images + batch_size - 1) // batch_size
   
   all_images = []
   for batch in range(num_batches):
       remaining = min(batch_size, total_images - batch * batch_size)
       result = api_call(num_images=remaining)
       all_images.extend(result['images'])
   ```

3. **Error Handling**: Handle partial batch failures gracefully
4. **Progress Tracking**: Update progress after each batch completes

## Local Considerations

For the Art Factory project:
- Current implementation makes individual API calls for each image (inefficient)
- Both fal.ai and Replicate models in fixtures support batch parameters
- Need to update OrderItem model to support multiple products (OneToMany)
- Factory machine implementations need refactoring to handle batch responses
- UI should show batch progress (e.g., "Batch 2/3 processing...")

## Metadata
- **Last Updated**: 2025-06-02
- **Version**: Current as of June 2025
- **Sources**: 
  - https://fal.ai/models/fal-ai/flux/dev/api
  - https://replicate.com/black-forest-labs/flux-schnell/api
  - fal.ai API documentation
  - Replicate HTTP API documentation