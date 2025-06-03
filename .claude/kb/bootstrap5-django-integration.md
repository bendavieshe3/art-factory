# Bootstrap 5 Django Integration

## Topics Covered
- django-bootstrap5 package usage
- Form integration patterns
- Component implementations
- JavaScript interactions
- Migration from custom CSS

## Main Content

### Installation and Setup

**Package Installation**
```bash
pip install django-bootstrap5
```

**Django Settings**
```python
INSTALLED_APPS = [
    # ...
    'django_bootstrap5',
]

# Optional Bootstrap5 settings
BOOTSTRAP5 = {
    'css_url': {
        'href': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css',
        'integrity': 'sha384-...',
        'crossorigin': 'anonymous',
    },
    'javascript_url': {
        'url': 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js',
        'integrity': 'sha384-...',
        'crossorigin': 'anonymous',
    },
}
```

### Template Integration

**Base Template Setup**
```django
{% load django_bootstrap5 %}
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{% block title %}{% endblock %}</title>
    {% bootstrap_css %}
    {% block extra_css %}{% endblock %}
</head>
<body>
    {% block content %}{% endblock %}
    {% bootstrap_javascript %}
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Form Integration Patterns

**Basic Form Rendering**
```django
{% load django_bootstrap5 %}

<form method="post">
    {% csrf_token %}
    {% bootstrap_form form %}
    {% bootstrap_button "Submit" button_type="submit" button_class="btn-primary" %}
</form>
```

**Individual Field Control**
```django
{% bootstrap_field form.field_name layout="horizontal" %}
{% bootstrap_field form.email placeholder="email@example.com" %}
{% bootstrap_field form.description rows=3 %}
```

**Custom Form Layouts**
```django
<form method="post" class="row g-3">
    {% csrf_token %}
    <div class="col-md-6">
        {% bootstrap_field form.first_name %}
    </div>
    <div class="col-md-6">
        {% bootstrap_field form.last_name %}
    </div>
    <div class="col-12">
        {% bootstrap_field form.email %}
    </div>
</form>
```

### Component Implementations

**Cards**
```django
<div class="card">
    <div class="card-header">
        <h5 class="mb-0">{{ title }}</h5>
    </div>
    <div class="card-body">
        {{ content }}
    </div>
    <div class="card-footer text-muted">
        {{ timestamp }}
    </div>
</div>
```

**Modals**
```django
<!-- Trigger -->
<button type="button" class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#myModal">
    Open Modal
</button>

<!-- Modal -->
<div class="modal fade" id="myModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Title</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                Content
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Close</button>
                <button type="button" class="btn btn-primary">Save</button>
            </div>
        </div>
    </div>
</div>
```

**Alerts and Toasts**
```django
<!-- Alert -->
<div class="alert alert-success alert-dismissible fade show" role="alert">
    {{ message }}
    <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
</div>

<!-- Toast -->
<div class="toast-container position-fixed bottom-0 end-0 p-3">
    <div class="toast" role="alert">
        <div class="toast-header">
            <strong class="me-auto">Notification</strong>
            <button type="button" class="btn-close" data-bs-dismiss="toast"></button>
        </div>
        <div class="toast-body">
            {{ message }}
        </div>
    </div>
</div>
```

### JavaScript Integration

**Initialize Components**
```javascript
// Initialize all tooltips
const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]')
const tooltipList = [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl))

// Show toast programmatically
const toastElList = document.querySelectorAll('.toast')
const toastList = [...toastElList].map(toastEl => new bootstrap.Toast(toastEl))
toastList[0].show()
```

**Dynamic Content Updates**
```javascript
// Update modal content dynamically
const myModal = new bootstrap.Modal(document.getElementById('myModal'))
document.getElementById('myModal').addEventListener('show.bs.modal', event => {
    const button = event.relatedTarget
    const modalTitle = myModal.querySelector('.modal-title')
    modalTitle.textContent = `Edit ${button.getAttribute('data-bs-title')}`
})
```

### Migration Patterns

**From Custom CSS to Bootstrap**
```css
/* Old custom CSS */
.custom-card {
    border: 1px solid #ddd;
    padding: 15px;
    margin-bottom: 20px;
    border-radius: 4px;
}

/* Replace with Bootstrap classes */
<div class="card mb-3">
    <div class="card-body">
        <!-- Content -->
    </div>
</div>
```

**Preserving Custom Styles**
```django
<!-- Keep custom components when superior -->
<div class="custom-toast-container">
    <!-- Custom toast implementation -->
</div>

<!-- Use Bootstrap for standard components -->
<div class="row g-3">
    <div class="col-md-4">
        <!-- Bootstrap grid -->
    </div>
</div>
```

### Best Practices

**1. Responsive Design**
```django
<!-- Mobile-first approach -->
<div class="col-12 col-md-6 col-lg-4">
    <!-- Content scales appropriately -->
</div>

<!-- Responsive utilities -->
<div class="d-none d-md-block">
    <!-- Hidden on mobile -->
</div>
```

**2. Form Validation**
```django
{% if form.errors %}
    <div class="alert alert-danger">
        {% for field, errors in form.errors.items %}
            <strong>{{ field }}:</strong> {{ errors|join:", " }}<br>
        {% endfor %}
    </div>
{% endif %}
```

**3. Loading States**
```javascript
// Show spinner during AJAX
button.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Loading...'
button.disabled = true
```

## Local Considerations

### Art Factory Implementation
- Migrated inventory page from custom CSS to Bootstrap 5
- Preserved custom toast system (superior to Bootstrap toasts)
- Used Bootstrap cards for consistent layout
- Implemented responsive grid for product display

### Django Integration Tips
- Use `{% load django_bootstrap5 %}` in every template
- Keep custom CSS minimal - prefer utility classes
- Use Bootstrap's JavaScript for interactions
- Test form rendering with different field types

### Performance Considerations
- Use CDN with SRI hashes for security
- Consider local hosting for offline development
- Minimize custom CSS overrides
- Use PurgeCSS in production to remove unused styles

## Metadata
- **Last Updated**: 2025-06-02
- **Version**: Bootstrap 5.3.0, django-bootstrap5 23.0
- **Sources**: 
  - https://django-bootstrap5.readthedocs.io/
  - Bootstrap 5 documentation
  - Art Factory migration experience
  - Django template best practices