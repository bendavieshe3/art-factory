# Worker Architecture for Asynchronous Order Processing

This document defines the autonomous worker system for processing AI generation orders without external dependencies or manual intervention.

## Design Principles

### Core Requirements
- **Zero Manual Intervention**: System operates autonomously once Django starts
- **Immediate Responsiveness**: Order submission triggers instant worker spawn
- **Resource Efficiency**: Workers exit when no work remains, returning resources to system
- **Enterprise Reliability**: Fault-tolerant processing with automatic recovery
- **Domain Model Integration**: Leverages existing OrderItem, FactoryMachine models

### User Experience Goals
- User submits order → immediate feedback that processing has started
- Multiple concurrent orders → automatic scaling via multiple workers
- Large orders (e.g., 20+ items) → single worker processes all items efficiently
- System failures → transparent recovery without user awareness

## Architecture Overview

### Component Relationships
```
Django Application Startup
    └── Auto-starts Foreman (monitoring process)

Order Submission (User Action)
    └── Creates OrderItems (pending status)
    └── Auto-spawns Smart Worker (immediate)

Smart Worker Process
    ├── Claims work in batches (atomic DB operations)
    ├── Processes batches efficiently
    ├── Continues until no work remains
    └── Exits gracefully (returns resources)

Foreman Process (Background)
    ├── Monitors worker health (heartbeat checks)
    ├── Kills stalled processes (OS-level)
    ├── Reassigns orphaned work (DB cleanup)
    └── Logs system health events
```

## Domain Model Integration

### Existing Models (No Changes Required)
- **OrderItem**: Natural task queue (`status='pending'`)
- **FactoryMachineDefinition**: Resource constraints and rate limits
- **FactoryMachineInstance**: Real-time resource utilization tracking
- **LogEntry**: Comprehensive activity logging

### New Models Required

#### Worker Model
```python
class Worker(models.Model):
    name = models.CharField(max_length=100)          # worker-{timestamp}
    process_id = models.IntegerField(unique=True)    # OS process ID
    status = models.CharField(choices=[
        ('starting', 'Starting'),
        ('working', 'Working'), 
        ('exiting', 'Exiting')
    ])
    
    # Processing capabilities
    provider = models.CharField(max_length=50)       # 'fal.ai', 'replicate'
    max_batch_size = models.IntegerField(default=5)  # Items per batch
    
    # Monitoring and metrics
    spawned_at = models.DateTimeField(auto_now_add=True)
    last_heartbeat = models.DateTimeField(auto_now=True)
    items_processed = models.IntegerField(default=0)
    items_failed = models.IntegerField(default=0)
```

#### Enhanced OrderItem Status
```python
# Add to existing STATUS_CHOICES
('assigned', 'Assigned to Worker')   # Claimed by worker, being processed
('stalled', 'Stalled')              # Manual retry required after repeated failures
```

## Smart Worker Behavior

### Autonomous Work Processing
```python
class SmartWorker:
    def run(self):
        self.register_worker()  # Create Worker record with PID
        
        while True:
            # 1. Claim available work atomically
            claimed_items = self.claim_work_batch()
            
            if not claimed_items:
                # No work available - exit to return resources
                self.graceful_exit("No pending work")
                return
            
            # 2. Process batch efficiently
            self.process_batch(claimed_items)
            
            # 3. Update heartbeat for monitoring
            self.update_heartbeat()
            
            # 4. Brief pause before next cycle
            time.sleep(10)
```

### Atomic Work Claiming
```python
def claim_work_batch(self):
    """Atomically claim multiple OrderItems for processing."""
    with transaction.atomic():
        available_items = OrderItem.objects.select_for_update().filter(
            status='pending',
            order__provider=self.provider  # Match worker's provider capability
        ).order_by('created_at')[:self.max_batch_size]
        
        claimed_items = []
        for item in available_items:
            if self.can_process_item(item):  # Check resource constraints
                item.status = 'assigned'
                item.assigned_worker = self.worker_record
                item.save()
                claimed_items.append(item)
        
        return claimed_items
```

### Resource Constraint Checking
```python
def can_process_item(self, order_item):
    """Check if this item can be processed given current constraints."""
    machine_def = FactoryMachineDefinition.objects.get(
        name=order_item.order.factory_machine_name
    )
    
    # Check rate limits
    recent_requests = self.count_recent_requests(machine_def.provider)
    rate_limit = machine_def.parameter_schema.get('rate_limit_per_minute', 10)
    
    if recent_requests >= rate_limit:
        return False
    
    # Check concurrent operation limits
    active_operations = self.count_active_operations(machine_def.provider)
    max_concurrent = machine_def.parameter_schema.get('max_concurrent', 3)
    
    return active_operations < max_concurrent
```

## Foreman Monitoring System

### Health Monitoring
```python
class Foreman:
    def monitor_cycle(self):
        """Continuous monitoring cycle for system health."""
        
        # 1. Process health checks
        self.check_worker_processes()
        
        # 2. Stall detection and recovery
        self.handle_stalled_workers()
        
        # 3. Orphaned work recovery
        self.reassign_orphaned_work()
        
        # 4. System health logging
        self.log_system_status()
        
        # 5. Wait before next cycle
        time.sleep(60)  # Check every minute
```

### Failure Recovery
```python
def handle_stalled_workers(self):
    """Handle workers that have stopped responding."""
    stalled_workers = Worker.objects.filter(
        last_heartbeat__lt=timezone.now() - timedelta(minutes=3)
    )
    
    for worker in stalled_workers:
        if self.process_exists(worker.process_id):
            # Process exists but not responding - kill it
            try:
                os.kill(worker.process_id, signal.SIGTERM)
                LogEntry.objects.create(
                    level='WARNING',
                    message=f'Killed stalled worker {worker.name} (PID: {worker.process_id})',
                    logger_name='foreman',
                    extra_data={'event_type': 'worker_killed', 'worker_id': worker.id}
                )
            except ProcessLookupError:
                pass  # Process already dead
        
        # Reassign worker's claimed work
        assigned_items = OrderItem.objects.filter(
            assigned_worker=worker,
            status='assigned'
        )
        assigned_items.update(status='pending', assigned_worker=None)
        
        # Remove worker record
        worker.delete()
```

## Automatic System Startup

### Django Integration
```python
# In main/apps.py
class MainConfig(AppConfig):
    def ready(self):
        """Auto-start system components when Django starts."""
        if not self.is_management_command():
            self.start_foreman_if_needed()
    
    def start_foreman_if_needed(self):
        """Ensure foreman process is running."""
        if not self.foreman_is_running():
            import threading
            foreman_thread = threading.Thread(target=self.run_foreman)
            foreman_thread.daemon = True
            foreman_thread.start()
```

### Order Submission Integration
```python
# In views.py - place_order_api
def place_order_api(request):
    # ... create order and order items ...
    
    # Automatically spawn worker for immediate responsiveness
    spawn_worker_automatically()
    
    return JsonResponse({
        'success': True,
        'order_id': order.id,
        'message': f'Order placed! Processing started for {order.quantity} items.'
    })

def spawn_worker_automatically():
    """Spawn worker process automatically without user intervention."""
    import threading
    
    worker_thread = threading.Thread(target=run_smart_worker)
    worker_thread.daemon = True
    worker_thread.start()
```

## Example Scenarios

### Scenario 1: Single Order with 20 Items
1. User submits order → 20 OrderItems created with `status='pending'`
2. System auto-spawns 1 Smart Worker immediately
3. Worker claims 5 items (batch limit), processes them
4. Worker claims next 5 items, processes them
5. Worker continues until all 20 items are processed
6. Worker finds no more work, exits gracefully

### Scenario 2: Multiple Concurrent Orders
1. User A submits 10-item order → Worker A spawned
2. User B submits 15-item order → Worker B spawned  
3. Worker A processes User A's items in batches
4. Worker B processes User B's items in batches
5. Both workers exit when their respective work is complete
6. System returns to idle state with zero resource usage

### Scenario 3: Worker Failure Recovery
1. Worker claims 5 items, starts processing
2. Worker process crashes or becomes unresponsive
3. Foreman detects stalled worker (no heartbeat for 3+ minutes)
4. Foreman kills stalled process, reassigns 5 items to `status='pending'`
5. Next worker spawn will pick up the reassigned work
6. User sees no impact - work continues transparently

## Resource Management

### Provider Rate Limiting
- Workers check FactoryMachineDefinition for rate limits before claiming work
- Rate limit tracking per provider prevents API quota violations
- Workers back off when approaching limits

### Concurrent Operation Limits
- Maximum simultaneous requests per provider enforced
- Workers coordinate through database state to respect limits
- Graceful degradation when limits reached

### Memory and Process Management
- Workers exit when idle, returning memory to system
- No persistent worker processes consuming resources
- Foreman process is lightweight, minimal resource usage

## Monitoring and Debugging

### Production Monitoring
- LogEntry records capture all worker activity
- Admin interface shows current worker status
- System health metrics available through management commands

### Management Commands (Debugging Only)
```bash
# Monitoring and debugging (not required for operation)
python manage.py debug_workers        # Show current worker status
python manage.py monitor_production   # System health dashboard
python manage.py kill_all_workers     # Emergency cleanup
python manage.py force_restart        # Development reset
```

### Health Check Endpoints
```python
# For external monitoring systems
GET /health/workers/     # Current worker status
GET /health/queue/       # Pending work queue status  
GET /health/system/      # Overall system health
```

## Implementation Benefits

### For Users
- **Immediate Response**: Orders start processing instantly
- **Reliable Processing**: Fault-tolerant system handles failures transparently  
- **Scalable Performance**: System handles 1 order or 100 orders efficiently

### For Operations
- **Zero Configuration**: No external services or manual setup required
- **Self-Healing**: Automatic recovery from process failures
- **Resource Efficient**: No idle processes consuming memory
- **Observable**: Comprehensive logging and monitoring built-in

### For Development
- **Django Native**: Uses familiar Django patterns and tools
- **Testable**: Pure Python components, easy to unit test
- **Maintainable**: Clear separation of concerns, well-defined interfaces
- **Debuggable**: Rich logging and development commands

## Future Enhancements

### Potential Improvements
- **Priority Queues**: High-priority orders processed first
- **Load Balancing**: Intelligent work distribution across providers
- **Metrics Dashboard**: Real-time system performance visualization
- **Auto-scaling**: Dynamic worker count based on queue depth

### Integration Points
- **Parameter Interpolation**: Smart token expansion during batch processing
- **Result Streaming**: Real-time progress updates to user interface
- **Project Management**: Batch processing by project for efficiency
- **Template System**: Optimized processing for template-based orders

This architecture provides enterprise-grade reliability with zero operational complexity, perfectly aligned with Art Factory's Django-first philosophy.