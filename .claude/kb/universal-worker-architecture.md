# Universal Worker Architecture Pattern

## Overview
A universal worker architecture uses generic workers that can process any type of task, rather than specialized workers for each provider or task type. This pattern simplifies deployment and improves resource utilization.

## Key Concepts
- **Provider-Agnostic Workers**: Workers don't know about specific providers
- **Task Routing**: Logic determines which handler processes each task
- **Dynamic Loading**: Handlers are loaded based on task metadata
- **Uniform Interface**: All handlers follow the same interface

## Architecture Overview

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Worker 1  │     │   Worker 2  │     │   Worker N  │
│  (Universal)│     │  (Universal)│     │  (Universal)│
└──────┬──────┘     └──────┬──────┘     └──────┬──────┘
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                    ┌──────▼──────┐
                    │ Task Router │
                    └──────┬──────┘
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
┌──────▼──────┐    ┌──────▼──────┐    ┌──────▼──────┐
│ Fal Handler │    │Replicate    │    │CivitAI      │
│             │    │Handler      │    │Handler      │
└─────────────┘    └─────────────┘    └─────────────┘
```

## Implementation Pattern

### 1. Universal Worker
```python
# workers.py
class UniversalWorker:
    """Generic worker that can process any order item"""
    
    def process_order_item(self, order_item_id):
        """Main processing method"""
        order_item = OrderItem.objects.get(id=order_item_id)
        
        # Get the appropriate factory machine
        factory_machine = order_item.factory_machine
        
        # Delegate to the factory machine's produce method
        try:
            factory_machine.produce(order_item)
            order_item.status = OrderItem.Status.COMPLETED
        except Exception as e:
            order_item.status = OrderItem.Status.FAILED
            order_item.error_message = str(e)
        
        order_item.save()
```

### 2. Factory Machine Pattern
```python
# factory_machines.py
class BaseFactoryMachine:
    """Base class for all factory machines"""
    
    def produce(self, order_item):
        """Produce a product for the given order item"""
        raise NotImplementedError
        
class FalFluxSchnellMachine(BaseFactoryMachine):
    """Specific implementation for Fal Flux Schnell"""
    
    def produce(self, order_item):
        # Provider-specific logic here
        response = fal.run(self.model_id, params)
        self.handle_response(response, order_item)

class ReplicateSDXLMachine(BaseFactoryMachine):
    """Specific implementation for Replicate SDXL"""
    
    def produce(self, order_item):
        # Different provider logic
        response = replicate.run(self.model_id, params)
        self.handle_response(response, order_item)
```

### 3. Task Distribution
```python
# tasks.py
from celery import shared_task

@shared_task
def process_order_item_task(order_item_id):
    """Celery task that can run on any worker"""
    worker = UniversalWorker()
    worker.process_order_item(order_item_id)
```

## Benefits

### 1. Simplified Deployment
- One worker type to deploy and manage
- No need for provider-specific worker pools
- Easier horizontal scaling

### 2. Better Resource Utilization
- Workers can process any type of task
- No idle specialized workers
- Dynamic load balancing

### 3. Easier Maintenance
- Single worker codebase
- Provider logic isolated in handlers
- Simpler monitoring and logging

### 4. Flexibility
- Easy to add new providers
- Can change provider logic without touching workers
- Runtime provider selection

## Comparison with Specialized Workers

### Specialized Workers (Anti-Pattern)
```python
# Don't do this
class FalWorker:
    def process_fal_tasks(self):
        # Only processes Fal tasks
        pass

class ReplicateWorker:
    def process_replicate_tasks(self):
        # Only processes Replicate tasks
        pass
```

Problems:
- Need separate queues for each provider
- Uneven load distribution
- Complex deployment configuration
- Idle workers when no provider-specific tasks

### Universal Workers (Recommended)
```python
# Do this instead
class UniversalWorker:
    def process_any_task(self, task):
        handler = self.get_handler(task.provider)
        handler.process(task)
```

## Implementation Considerations

### 1. Error Handling
```python
def process_order_item(self, order_item_id):
    try:
        order_item = OrderItem.objects.get(id=order_item_id)
        factory_machine = self.get_factory_machine(order_item)
        factory_machine.produce(order_item)
    except OrderItem.DoesNotExist:
        logger.error(f"OrderItem {order_item_id} not found")
    except Exception as e:
        logger.exception(f"Error processing {order_item_id}")
        # Update order item status
```

### 2. Monitoring
```python
class UniversalWorker:
    def process_order_item(self, order_item_id):
        start_time = time.time()
        
        # Process...
        
        duration = time.time() - start_time
        metrics.record('task.duration', duration, tags={
            'provider': order_item.factory_machine.provider,
            'model': order_item.factory_machine.model_id
        })
```

### 3. Configuration
```python
# settings.py
WORKER_CONFIG = {
    'max_retries': 3,
    'timeout': 300,  # 5 minutes
    'log_level': 'INFO',
}

# No provider-specific worker configuration needed!
```

## Testing Strategy
```python
class TestUniversalWorker(TestCase):
    def test_processes_any_provider(self):
        worker = UniversalWorker()
        
        # Test with different providers
        for provider in ['fal', 'replicate', 'civitai']:
            order_item = create_test_order_item(provider=provider)
            worker.process_order_item(order_item.id)
            
            order_item.refresh_from_db()
            self.assertEqual(order_item.status, 'completed')
```

## Migration Path
1. Implement universal worker alongside existing workers
2. Gradually move task processing to universal worker
3. Monitor performance and errors
4. Deprecate specialized workers
5. Remove specialized worker code

## Best Practices
1. **Keep workers thin**: Business logic belongs in handlers
2. **Use dependency injection**: Pass handlers to workers
3. **Log extensively**: Track which handler processes each task
4. **Monitor performance**: Compare with specialized workers
5. **Handle failures gracefully**: Implement retry logic

## Related Topics
- Task queue patterns
- Microservice architecture
- Factory pattern
- Dependency injection

## Sources
- Celery best practices documentation
- Distributed system design patterns
- Art Factory implementation (2025-06-04)

## Local Context
The Art Factory project successfully uses universal workers to process image generation tasks across multiple providers (fal.ai, Replicate, CivitAI) without any provider-specific worker code. This has simplified deployment and improved system reliability.