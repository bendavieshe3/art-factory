# Django Fixtures vs Seed Data Commands

## Overview
Django provides multiple approaches for managing initial and test data. Understanding when to use fixtures versus custom management commands is crucial for maintainable applications.

## Fixtures: Static Data Snapshots

### What Are Fixtures?
Fixtures are serialized database snapshots in JSON, XML, or YAML format that Django can load into the database.

### When to Use Fixtures
- **Static reference data**: Countries, states, categories
- **Configuration data**: System settings, feature flags
- **Test data**: Predictable data for automated tests
- **Demo data**: Sample data for demonstrations

### Fixture Example
```json
// fixtures/factory_machines.json
[
    {
        "model": "main.factorymachine",
        "pk": 1,
        "fields": {
            "name": "fal_flux_schnell",
            "display_name": "Flux Schnell",
            "provider": "fal",
            "model_id": "fal-ai/flux/schnell",
            "is_active": true
        }
    }
]
```

### Loading Fixtures
```bash
# Load specific fixture
python manage.py loaddata factory_machines

# Load multiple fixtures in order
python manage.py loaddata factory_machines factory_machine_instances

# In tests
class MyTest(TestCase):
    fixtures = ['factory_machines.json']
```

### Fixture Advantages
- Simple and declarative
- Version controlled
- Django native support
- Automatic test loading
- Cross-database compatible

### Fixture Limitations
- No dynamic data generation
- Difficult to maintain relationships
- Can become outdated
- Limited to simple data types
- No business logic execution

## Seed Data Commands: Dynamic Data Generation

### What Are Seed Commands?
Custom Django management commands that programmatically create data using Python code.

### When to Use Seed Commands
- **Dynamic data**: User accounts, random content
- **Complex relationships**: Many-to-many, circular references
- **Business logic**: Data requiring validation or processing
- **Environment-specific**: Different data per environment
- **Large datasets**: Programmatically generated bulk data

### Seed Command Example
```python
# management/commands/load_seed_data.py
from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from main.models import Order, Product
import random

class Command(BaseCommand):
    help = 'Load seed data for development'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='Number of users to create'
        )
    
    def handle(self, *args, **options):
        User = get_user_model()
        
        # Create users with logic
        for i in range(options['users']):
            user = User.objects.create_user(
                username=f'user{i}',
                email=f'user{i}@example.com',
                password='testpass123'
            )
            
            # Create related data with business logic
            if random.choice([True, False]):
                order = Order.objects.create(
                    user=user,
                    status='pending'
                )
                # More complex logic here
        
        self.stdout.write(
            self.style.SUCCESS(f'Created {options["users"]} users')
        )
```

### Running Seed Commands
```bash
# Basic usage
python manage.py load_seed_data

# With options
python manage.py load_seed_data --users=50

# In deployment scripts
python manage.py migrate
python manage.py loaddata factory_machines  # Static data
python manage.py load_seed_data  # Dynamic data
```

## Comparison Table

| Aspect | Fixtures | Seed Commands |
|--------|----------|---------------|
| Format | JSON/XML/YAML | Python code |
| Dynamic data | ❌ No | ✅ Yes |
| Business logic | ❌ No | ✅ Yes |
| Maintainability | Medium | High |
| Version control | ✅ Easy | ✅ Easy |
| Testing | ✅ Built-in | Requires setup |
| Performance | Fast | Depends on logic |
| Debugging | Limited | Full Python debugging |
| Relationships | Difficult | Easy |
| Environment-specific | ❌ No | ✅ Yes |

## Best Practices

### 1. Hybrid Approach
Use both fixtures and seed commands:
```python
class Command(BaseCommand):
    def handle(self, *args, **options):
        # Load static data first
        call_command('loaddata', 'factory_machines')
        
        # Then create dynamic data
        self.create_dynamic_data()
```

### 2. Idempotent Seed Commands
Make commands safe to run multiple times:
```python
def handle(self, *args, **options):
    # Check if data exists
    if User.objects.filter(username='admin').exists():
        self.stdout.write('Admin user already exists')
        return
    
    # Create data
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
```

### 3. Environment Detection
```python
def handle(self, *args, **options):
    if settings.DEBUG:
        # Development data
        self.create_test_users(100)
    else:
        # Production data
        self.create_default_admin()
```

### 4. Fixture Organization
```
fixtures/
├── 01_static_data.json      # Load order matters
├── 02_config_data.json
└── test/
    └── test_orders.json     # Test-specific fixtures
```

### 5. Documentation
```python
class Command(BaseCommand):
    help = '''
    Load seed data for development environment.
    
    This command will:
    - Create 10 test users
    - Create sample orders for each user
    - Generate random product data
    
    Safe to run multiple times (idempotent).
    '''
```

## Common Patterns

### Pattern 1: Reference Data in Fixtures
```json
// Good for: Countries, categories, static configuration
[
    {
        "model": "main.category",
        "pk": 1,
        "fields": {
            "name": "Technology",
            "slug": "technology"
        }
    }
]
```

### Pattern 2: Test Data in Commands
```python
# Good for: User accounts, orders, dynamic content
def create_test_orders(self, count=10):
    for _ in range(count):
        user = random.choice(User.objects.all())
        Order.objects.create(
            user=user,
            total=random.uniform(10.0, 1000.0),
            status=random.choice(['pending', 'completed'])
        )
```

### Pattern 3: Conditional Loading
```python
def handle(self, *args, **options):
    # Only load if database is empty
    if Product.objects.exists():
        self.stdout.write('Database already has data')
        return
    
    # Load fixtures then create dynamic data
    call_command('loaddata', 'products')
    self.create_sample_orders()
```

## Related Topics
- Django migrations
- Database initialization
- Test data management
- Deployment automation

## Sources
- Django documentation on fixtures
- Django management commands guide
- Art Factory implementation patterns (2025-06-04)

## Local Context
In the Art Factory project, fixtures are used for factory machine definitions (static provider configurations), while seed data commands create dynamic test orders and user accounts. This separation ensures that provider configurations remain consistent while allowing flexible test data generation.