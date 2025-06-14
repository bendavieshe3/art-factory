# Template Components Documentation

This document provides comprehensive documentation for all reusable template components in the AI Art Factory application.

## Component System Overview

Components are organized into functional categories under `templates/components/`:

```
templates/components/
├── cards/              # Card-based UI components
├── forms/              # Form-related components  
├── js/                 # JavaScript component templates
├── lists/              # List and table components
├── modals/             # Modal dialog components
├── navigation/         # Navigation and pagination components
└── ui/                 # General UI components
```

## Component Categories

### Navigation Components

#### `components/navigation/pagination.html`

**Purpose**: Standardized pagination for paginated content

**Parameters**:
- `page_obj` (required): Django Paginator page object
- `url_name` (optional): URL name for pagination links (default: current page URL)
- `url_params` (optional): Additional URL parameters to preserve
- `aria_label` (optional): Accessibility label (default: "Page navigation")
- `size` (optional): Pagination size - `sm`, `lg`, or default
- `justify` (optional): Alignment - `center`, `end`, or default (start)

**Usage Example**:
```django
{% include 'components/navigation/pagination.html' with page_obj=products url_name='main:inventory' aria_label='Product navigation' %}
```

**Advanced Example with Parameters**:
```django
{% include 'components/navigation/pagination.html' with page_obj=projects url_name='main:all_projects' url_params='search='|add:search_query size='sm' justify='center' %}
```

### Card Components

#### `components/cards/project_card.html`

**Purpose**: Standardized project display card

**Parameters**:
- `project` (required): Project model instance
- `show_stats` (optional): Show project statistics (default: true)
- `show_actions` (optional): Show action buttons (default: true)
- `card_class` (optional): Additional CSS classes for card
- `link_target` (optional): Target for project links (default: same window)

**Usage Example**:
```django
{% include 'components/cards/project_card.html' with project=project show_actions=False %}
```

#### `components/cards/product_card.html`

**Purpose**: Standardized product display card

**Parameters**:
- `product` (required): Product model instance
- `show_checkbox` (optional): Show selection checkbox (default: false)
- `show_actions` (optional): Show action buttons (default: true)
- `card_variant` (optional): Card style variant - `compact`, `full`, or default
- `click_action` (optional): Click behavior - `modal`, `link`, or `none` (default: modal)

**Usage Example**:
```django
{% include 'components/cards/product_card.html' with product=product card_variant='compact' click_action='link' %}
```

### Modal Components

#### `components/modals/project_create_modal.html`

**Purpose**: Modal for creating new projects

**Parameters**:
- `modal_id` (optional): Custom modal ID (default: 'createProjectModal')
- `modal_size` (optional): Modal size - `sm`, `lg`, `xl` (default: default)
- `form_action` (optional): Form action URL (default: project create URL)

**Usage Example**:
```django
{% include 'components/modals/project_create_modal.html' with modal_id='newProjectModal' modal_size='lg' %}
```

#### `components/modals/project_edit_modal.html`

**Purpose**: Modal for editing existing projects

**Parameters**:
- `modal_id` (optional): Custom modal ID (default: 'editProjectModal')
- `project` (optional): Project instance for pre-filling form
- `form_action` (optional): Form action URL

**Usage Example**:
```django
{% include 'components/modals/project_edit_modal.html' with project=project modal_id='editProject{{ project.id }}' %}
```

#### `components/modals/confirmation_modal.html`

**Purpose**: Generic confirmation dialog

**Parameters**:
- `modal_id` (required): Unique modal ID
- `title` (required): Modal title
- `message` (required): Confirmation message
- `confirm_text` (optional): Confirm button text (default: 'Confirm')
- `cancel_text` (optional): Cancel button text (default: 'Cancel')
- `confirm_class` (optional): CSS class for confirm button (default: 'btn-danger')
- `action_url` (optional): URL for form submission
- `action_method` (optional): HTTP method (default: 'POST')

**Usage Example**:
```django
{% include 'components/modals/confirmation_modal.html' with modal_id='deleteProject' title='Delete Project' message='Are you sure you want to delete this project?' action_url=project.get_delete_url %}
```

### List Components

#### `components/lists/order_list_item.html`

**Purpose**: Standardized order item display

**Parameters**:
- `order` (required): Order model instance
- `show_status` (optional): Show order status (default: true)
- `show_actions` (optional): Show action buttons (default: true)
- `compact` (optional): Use compact display (default: false)

**Usage Example**:
```django
{% include 'components/lists/order_list_item.html' with order=order compact=True %}
```

#### `components/lists/product_list_item.html`

**Purpose**: Standardized product item display for lists

**Parameters**:
- `product` (required): Product model instance
- `show_thumbnail` (optional): Show product thumbnail (default: true)
- `show_metadata` (optional): Show metadata (default: true)
- `list_style` (optional): List style - `detailed`, `compact` (default: detailed)

**Usage Example**:
```django
{% include 'components/lists/product_list_item.html' with product=product list_style='compact' %}
```

### Form Components

#### `components/forms/project_form.html`

**Purpose**: Reusable project form fields

**Parameters**:
- `form` (required): Django form instance
- `form_id` (optional): Form element ID
- `submit_text` (optional): Submit button text (default: 'Save')
- `show_cancel` (optional): Show cancel button (default: true)
- `form_method` (optional): HTTP method (default: 'POST')

**Usage Example**:
```django
{% include 'components/forms/project_form.html' with form=project_form submit_text='Create Project' %}
```

### UI Components

#### `components/ui/page_header.html`

**Purpose**: Standardized page header with title, description, and actions

**Parameters**:
- `title` (required): Page title
- `description` (optional): Page description text
- `actions` (optional): HTML for header action buttons
- `breadcrumbs` (optional): Breadcrumb navigation HTML
- `header_class` (optional): Additional CSS classes

**Usage Example**:
```django
{% include 'components/ui/page_header.html' with title='My Page' description='Page description' actions='<button class="btn btn-primary">Action</button>' %}
```

#### `components/ui/empty_state.html`

**Purpose**: Consistent empty state display

**Parameters**:
- `title` (required): Empty state title
- `message` (optional): Descriptive message
- `icon` (optional): Bootstrap icon name
- `action_text` (optional): Action button text
- `action_url` (optional): Action button URL
- `action_class` (optional): Action button CSS classes

**Usage Example**:
```django
{% include 'components/ui/empty_state.html' with title='No Products Found' message='Start by creating your first product.' icon='plus-circle' action_text='Create Product' action_url='#' %}
```

#### `components/ui/loading_spinner.html`

**Purpose**: Consistent loading indicator

**Parameters**:
- `size` (optional): Spinner size - `sm`, `lg` (default: default)
- `text` (optional): Loading text (default: 'Loading...')
- `center` (optional): Center the spinner (default: false)

**Usage Example**:
```django
{% include 'components/ui/loading_spinner.html' with size='lg' text='Processing...' center=True %}
```

#### `components/ui/toast_system.html`

**Purpose**: Global toast notification system

**Parameters**: None (automatically included in layouts)

**JavaScript API**:
```javascript
// Success toast
ToastNotification.success('Operation completed successfully!', 'Success');

// Error toast  
ToastNotification.error('Something went wrong.', 'Error');

// Info toast
ToastNotification.info('Information message', 'Info');

// Warning toast
ToastNotification.warning('Warning message', 'Warning');
```

### JavaScript Components

#### `components/js/order_form_management.html`

**Purpose**: Order form functionality (validation, persistence, calculations)

**Parameters**:
- `max_generations` (optional): Maximum allowed generations (default: 50)
- `default_batch_size` (optional): Default batch size (default: 4)

**JavaScript API**:
```javascript
// Functions available globally
changeGenerationCount(delta);     // Adjust generation count
saveFormValues();                 // Save form to localStorage  
loadFormValues();                 // Load form from localStorage
debugFormPersistence();           // Debug form persistence issues
```

#### `components/js/order_machine_parameters.html`

**Purpose**: Dynamic machine parameter loading and management

**Parameters**:
- `dynamic_container_id` (optional): Container ID for parameters (default: 'dynamicParameters')
- `factory_machines_api_url` (optional): API URL for machine data

**JavaScript API**:
```javascript
// Functions available globally
updateDynamicParameters(machineId);  // Load parameters for machine
generateParameterFields(machine);    // Generate parameter form fields
clearDynamicParameters();            // Clear all parameters
```

#### `components/js/product_collection_init.html`

**Purpose**: Product gallery initialization and management

**Parameters**:
- `collection_container` (optional): Container selector (default: '#productCollection')
- `layout_type` (optional): Layout type - 'grid', 'strip' (default: 'grid')
- `selectable` (optional): Enable selection (default: false)
- `show_bulk_actions` (optional): Show bulk action buttons (default: false)

**JavaScript API**:
```javascript
// ProductCollection instance methods
collection.loadProducts(products);     // Load product data
collection.selectAll();               // Select all products
collection.clearSelection();          // Clear selection
collection.getSelected();             // Get selected products
```

## Component Integration Patterns

### Layout Integration

Components are designed to work seamlessly with all layouts:

```django
{% extends 'layouts/app_layout.html' %}

{% block content %}
<!-- Use components within layout blocks -->
{% include 'components/ui/page_header.html' with title='My Page' %}
{% include 'components/cards/product_card.html' with product=product %}
{% endblock %}
```

### Context Variable Passing

Pass context variables explicitly for clarity:

```django
<!-- Good: Explicit parameter passing -->
{% include 'components/cards/project_card.html' with project=project show_actions=True %}

<!-- Avoid: Implicit context inheritance -->
{% include 'components/cards/project_card.html' %}
```

### JavaScript Component Loading

Load JavaScript components in template order:

```django
<!-- Load in dependency order -->
{% include 'components/js/order_form_management.html' %}
{% include 'components/js/order_machine_parameters.html' %}
{% include 'components/js/order_main_init.html' %}
```

## Best Practices

### 1. Parameter Validation

Always validate required parameters in components:

```django
{% if not project %}
    <div class="alert alert-danger">Error: Project parameter is required</div>
{% else %}
    <!-- Component content -->
{% endif %}
```

### 2. Default Values

Provide sensible defaults for optional parameters:

```django
{% with show_actions=show_actions|default:True %}
    {% if show_actions %}
        <!-- Action buttons -->
    {% endif %}
{% endwith %}
```

### 3. CSS Class Composition

Allow additional CSS classes while maintaining base styling:

```django
<div class="card{{ card_class|default:'' }}">
    <!-- Card content -->
</div>
```

### 4. Accessibility

Include proper ARIA attributes and labels:

```django
<button type="button" 
        class="btn btn-primary"
        aria-label="{{ action_label|default:'Perform action' }}"
        {% if disabled %}disabled{% endif %}>
    {{ button_text }}
</button>
```

### 5. Responsive Design

Ensure components work across all screen sizes:

```django
<div class="row g-3">
    <div class="col-12 col-md-6 col-lg-4">
        <!-- Responsive grid item -->
    </div>
</div>
```

## Testing Components

### Template Tests

Test component rendering with various parameters:

```python
def test_project_card_component(self):
    """Test project card component renders correctly."""
    response = self.client.get('/projects/')
    self.assertContains(response, 'class="project-card"')
    self.assertContains(response, self.project.name)
```

### JavaScript Tests

Test JavaScript component functionality:

```javascript
// Test form persistence
function testFormPersistence() {
    // Fill form
    document.getElementById('prompt').value = 'test prompt';
    
    // Save and reload
    saveFormValues();
    document.getElementById('prompt').value = '';
    loadFormValues();
    
    // Verify restoration
    assert(document.getElementById('prompt').value === 'test prompt');
}
```

### Integration Tests

Test component integration with layouts and other components:

```python
def test_pagination_component_integration(self):
    """Test pagination component works with product gallery."""
    # Create paginated content
    products = [Product.objects.create() for _ in range(25)]
    
    response = self.client.get('/inventory/')
    self.assertContains(response, 'pagination')
    self.assertContains(response, 'Previous')
    self.assertContains(response, 'Next')
```

## Troubleshooting

### Common Issues

1. **Missing Context Variables**: Ensure all required parameters are passed
2. **CSS Conflicts**: Check for class name collisions with custom styles
3. **JavaScript Errors**: Verify component dependencies are loaded in correct order
4. **Template Inheritance**: Ensure components don't conflict with layout blocks

### Debug Tools

1. **Django Debug Toolbar**: View template context and inheritance
2. **Browser DevTools**: Inspect rendered HTML and JavaScript errors
3. **Template Debug**: Use `{{ variable|pprint }}` to debug context
4. **JavaScript Console**: Use `debugFormPersistence()` for form issues

## Migration Guide

### Converting Inline HTML to Components

```django
<!-- Before: Inline pagination -->
{% if page_obj.has_other_pages %}
    <nav aria-label="Page navigation">
        <!-- 20+ lines of pagination HTML -->
    </nav>
{% endif %}

<!-- After: Component usage -->
{% include 'components/navigation/pagination.html' with page_obj=products %}
```

### Updating JavaScript Patterns

```django
<!-- Before: Inline JavaScript -->
<script>
    document.addEventListener('DOMContentLoaded', function() {
        // 100+ lines of JavaScript
    });
</script>

<!-- After: Component inclusion -->
{% include 'components/js/product_collection_init.html' with collection_container='#myProducts' %}
```

## Related Documentation

- `docs/template-layouts.md` - Layout system documentation  
- `docs/design.md` - Frontend architecture
- `docs/testing.md` - Testing standards and practices
- `templates/components/` - Component source code and examples