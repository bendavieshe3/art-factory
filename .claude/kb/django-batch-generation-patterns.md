# Django Batch Generation Patterns

## Topics Covered
- Batch vs generation count design patterns
- OneToMany relationships for batch processing
- Synchronous vs asynchronous execution
- Worker system architecture
- UI/UX for batch controls

## Overview

Batch generation in Django requires careful design to separate user intent (number of generations) from API optimization (batch size per call). This pattern is particularly important for AI/ML applications where APIs support multiple outputs per request.

## Key Concepts

### Generation Count vs Batch Size
- **Generation Count**: Number of API calls the user wants (user control)
- **Batch Size**: Number of outputs per API call (optimization)
- **Total Products**: Generation Count × Batch Size

Example:
- User wants 10 images
- API supports 4 images per call
- Solution: 3 generations with batch_size=4 (producing 12 images)

## Database Design

### OneToMany Pattern for Batch Results
```python
# OrderItem model (one per generation)
class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE)
    total_quantity = models.PositiveIntegerField(default=1)
    batch_size = models.PositiveIntegerField(default=1)
    batches_completed = models.PositiveIntegerField(default=0)
    # ... other fields

# Product model (many per OrderItem)
class Product(models.Model):
    order_item = models.ForeignKey(
        'OrderItem', 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='products'
    )
    # ... other fields
```

### Migration Strategy
```python
# Add batch fields to existing model
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='orderitem',
            name='batch_size',
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name='product',
            name='order_item',
            field=models.ForeignKey(
                'OrderItem',
                on_delete=models.SET_NULL,
                null=True,
                blank=True,
                related_name='products'
            ),
        ),
    ]
```

## Synchronous Batch Processing

### Why Synchronous?
- Avoids Django's async context issues with ORM
- Simpler error handling
- Better for background workers
- Maintains transaction integrity

### Implementation Pattern
```python
class SyncFactoryMachine:
    def execute_sync(self, order_item):
        """Execute batch generation synchronously."""
        try:
            # Update status
            order_item.status = 'processing'
            order_item.save()
            
            # Call API with batch parameters
            result = api_client.generate(
                prompt=order_item.prompt,
                num_outputs=order_item.batch_size,
                **order_item.parameters
            )
            
            # Process batch results
            products_created = []
            for idx, output in enumerate(result.outputs):
                product = self._create_product(
                    order_item=order_item,
                    output=output,
                    index=idx
                )
                products_created.append(product)
            
            # Update completion status
            order_item.status = 'completed'
            order_item.batches_completed = 1
            order_item.save()
            
            # Update parent order status
            self._update_order_status(order_item.order)
            
        except Exception as e:
            order_item.status = 'failed'
            order_item.error_message = str(e)
            order_item.save()
```

## Worker System Design

### Universal Workers
Instead of provider-specific workers, use universal workers that can process any job:

```python
class SmartWorker:
    def __init__(self, max_batch_size=5):
        self.max_batch_size = max_batch_size
        self.name = f"worker-{int(time.time())}"
        
    def claim_work_batch(self):
        """Claim any available work, regardless of provider."""
        with transaction.atomic():
            available_items = OrderItem.objects.select_for_update().filter(
                status='pending'
            ).order_by('created_at')[:self.max_batch_size]
            
            # Mark as claimed
            for item in available_items:
                item.status = 'assigned'
                item.assigned_worker = self.worker_record
                item.save()
```

### Order Status Updates
Critical: Update parent order status when items complete/fail:

```python
def update_order_status(self, order):
    """Update order status based on its items."""
    items = order.orderitem_set.all()
    total = items.count()
    completed = items.filter(status='completed').count()
    failed = items.filter(status='failed').count()
    
    if completed == total:
        order.status = 'completed'
    elif failed == total:
        order.status = 'failed'
    elif completed + failed == total:
        order.status = 'completed'  # Partial success
    elif completed > 0 or failed > 0:
        order.status = 'processing'
    
    order.save()
```

## UI/UX Implementation

### Separate Controls for Clarity
```html
<!-- Generation Control -->
<div class="col-md-4">
    <label>Number of Generations</label>
    <input type="number" id="generationCount" 
           value="1" min="1" max="50">
    <div class="form-text">How many API calls to make</div>
</div>

<!-- Batch Size Control -->
<div class="col-md-4">
    <label>Batch Size</label>
    <select id="batchSize">
        <option value="1">1 image per call</option>
        <option value="2">2 images per call</option>
        <option value="4">4 images per call</option>
    </select>
    <div class="form-text">Images per API call</div>
</div>

<!-- Total Display -->
<div class="col-md-4">
    <label>Total Products</label>
    <div id="totalProducts">1 image</div>
</div>
```

### Real-time Calculation
```javascript
function updateTotalProducts() {
    const generations = parseInt($('#generationCount').val()) || 1;
    const batchSize = parseInt($('#batchSize').val()) || 1;
    const total = generations * batchSize;
    
    $('#totalProducts').text(
        total === 1 ? '1 image' : `${total} images`
    );
}
```

## API Integration Patterns

### Provider Differences
Different providers use different parameter names:
- **fal.ai**: `num_images` (1-4)
- **Replicate**: `num_outputs` (1-4)

Handle in factory pattern:
```python
# Map generic batch_size to provider-specific parameter
if provider == 'fal.ai':
    params['num_images'] = order_item.batch_size
elif provider == 'replicate':
    params['num_outputs'] = order_item.batch_size
```

## Common Pitfalls

1. **Forgetting Order Status Updates**: Always update parent order status when items complete
2. **Provider-Specific Workers**: Makes system inflexible - use universal workers
3. **Async Context Issues**: Django ORM in async contexts can cause problems
4. **Not Handling Partial Batches**: API might return fewer results than requested
5. **Missing Version Hashes**: Some Replicate models require version hashes

## Local Considerations

- Django 5.1+ has better async support but sync is still safer for background tasks
- SQLite works fine for development but consider PostgreSQL for production batch processing
- Monitor worker processes - they can accumulate if not properly managed
- Use transactions for atomic batch operations

## Best Practices

1. **Separate Concerns**: User intent (generations) vs optimization (batch size)
2. **Fail Gracefully**: Handle partial successes in batches
3. **Track Progress**: Update batch completion counters
4. **Log Extensively**: Batch operations need good debugging trails
5. **Test Edge Cases**: Empty batches, single items, maximum sizes

## Metadata
- **Last Updated**: 2025-06-03
- **Version**: Django 5.1+ patterns
- **Sources**: 
  - Art Factory batch generation implementation
  - Django ORM documentation on select_for_update
  - fal.ai and Replicate API documentation