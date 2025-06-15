# Django Project Context Patterns

## Topics Covered
- Session-based project context management
- Contextual page headers with project specifiers
- Reusable filtered content components
- Template security with data attributes
- Project-aware UI/UX patterns
- Component documentation and testing

## Main Content

### Session-Based Project Context System

**Core Pattern**: Use Django sessions to maintain project context across page navigation rather than URL parameters.

**Implementation**:
```python
# utils/project_context.py
def ensure_project_context(request):
    """Get current project from session, with URL parameter override support."""
    project_id = request.session.get("current_project_id")
    if project_id:
        try:
            return Project.objects.get(id=project_id, status="active")
        except Project.DoesNotExist:
            del request.session["current_project_id"]
    return None

def get_project_aware_context(request, **additional_context):
    """Generate context dictionary with project information."""
    context = {"current_project": ensure_project_context(request), **additional_context}
    return context
```

**Benefits**:
- Consistent project context across page navigation
- No URL pollution with project parameters
- Automatic fallback when projects are deleted
- Clean, maintainable view code

### Contextual Page Headers with Project Specifiers

**Pattern**: Use different prepositions to show relationship between page and project.

**Template Implementation**:
```html
<!-- components/ui/page_header.html -->
<h1 class="h2 mb-1">
    {{ title }}{% if current_project and project_specifier %}
        <span class="text-muted"> {{ project_specifier }} {{ current_project.name }}</span>
    {% endif %}
</h1>
```

**Usage Examples**:
- **Order Page**: "Order for Project Name" (action within project)
- **Inventory Page**: "Inventory of Project Name" (content belonging to project)
- **Production Page**: "Production in Project Name" (activity within project)

**View Implementation**:
```python
def order_view(request):
    context = get_project_aware_context(
        request,
        page_title="Order",
        project_specifier="for",  # "Order for Project"
    )
    return render(request, "main/order.html", context)
```

### Reusable Filtered Content Components

**Pattern**: Create API-based components that automatically filter by project context with visual indicators.

**Component Structure**:
```html
<!-- components/ui/recent_products.html -->
<div class="card" data-component="recent-products" 
     data-api-url="{% url 'main:recent_products_api' %}"
     data-limit="8">
    <div class="card-header">
        <h6 class="mb-0">Recent Products</h6>
        {% if current_project %}
            <span class="badge bg-primary">
                <i class="bi bi-funnel"></i> {{ current_project.name }}
            </span>
        {% endif %}
    </div>
    <!-- Content loaded via JavaScript -->
</div>
```

**JavaScript Implementation**:
```javascript
// Use data attributes for security instead of dynamic function names
document.addEventListener('DOMContentLoaded', function() {
    const cards = document.querySelectorAll('[data-component="recent-products"]');
    cards.forEach(function(card) {
        const apiUrl = card.getAttribute('data-api-url');
        const limit = card.getAttribute('data-limit');
        // Load and render content
    });
});
```

**API Implementation**:
```python
def recent_products_api(request):
    """API endpoint with automatic project filtering."""
    current_project = ensure_project_context(request)
    if current_project:
        products = current_project.get_recent_products(limit)
    else:
        products = Product.objects.order_by("-created_at")[:limit]
    # Return JSON response
```

### Template Security with Data Attributes

**Problem**: Dynamic JavaScript function names using template variables can be security risks.

**Wrong Approach**:
```html
<script>
function load_{{ container_id|default:'recentOrders' }}() {
    // Security risk: template variable in JS function name
}
</script>
```

**Correct Approach**:
```html
<div data-component="recent-orders" data-container-id="recentOrders">
<script>
document.querySelectorAll('[data-component="recent-orders"]').forEach(function(element) {
    const containerId = element.getAttribute('data-container-id');
    // Safe: no template variables in JavaScript code
});
</script>
```

### Project Context State Management

**Session Management**:
```python
# Set project context
def set_project_context(request, project_id):
    try:
        project = Project.objects.get(id=project_id, status="active")
        request.session["current_project_id"] = project.id
        messages.success(request, f"Switched to project: {project.name}")
    except Project.DoesNotExist:
        messages.error(request, "Project not found")
    
    next_url = request.GET.get("next", "main:order")
    return redirect(next_url)

# Clear project context  
def clear_project_context(request):
    if "current_project_id" in request.session:
        del request.session["current_project_id"]
    return redirect("main:projects")
```

**Template Integration**:
```html
<!-- Project context indicator with change link -->
<small>
    <span class="fw-medium">Project:</span> {{ current_project.name }}
    <span class="mx-1">-</span>
    {{ current_project.order_count }} orders - {{ current_project.product_count }} products
    <a href="{% url 'main:projects' %}" class="ms-2 text-decoration-none">
        <i class="bi bi-arrow-left-circle"></i>
    </a>
</small>
```

### Component Documentation Pattern

**Standard Documentation Format**:
```html
{% comment %}
Component Name

Purpose: Brief description of what the component does

Parameters:
- param_name (required/optional): Description, defaults to value
- another_param (optional): Description

Usage:
{% include 'path/to/component.html' %}
{% include 'path/to/component.html' with param="value" %}
{% endcomment %}
```

**Documentation Location**: `docs/template-components.md` with comprehensive parameter descriptions and usage examples.

### Testing Project-Aware Components

**Session Context in Tests**:
```python
def test_project_aware_view(self):
    # Set project context in session
    session = self.client.session
    session["current_project_id"] = self.project.id
    session.save()
    
    response = self.client.get(reverse("main:order"))
    self.assertContains(response, "Order for Test Project")
```

**Component Security Testing**:
```python
def test_no_inline_javascript_with_user_data(self):
    """Ensure templates don't include unsafe JavaScript with user data."""
    for template_path in self.get_all_templates():
        if self.has_javascript_with_template_vars(template_path):
            self.fail(f"{template_path} has potentially unsafe JavaScript")
```

## Local Considerations

### Art Factory Implementation
- **Removed legacy URL-based filtering**: Simplified views by removing `?project=123` support
- **Unified template blocks**: Replaced individual `page_title`/`page_description` blocks with integrated page header component
- **Component reusability**: Recent Products/Orders components can be reused across different pages with different configurations
- **Progressive enhancement**: Components work without JavaScript (show placeholder) but enhance with API data

### Performance Considerations
- **API-based components**: Allow for lazy loading and don't block initial page render
- **Session storage**: More efficient than repeated database queries for project context
- **Component caching**: Each component manages its own data loading and can implement caching

### Migration Strategy
1. **Maintain backward compatibility** during transition (support both URL and session)
2. **Update tests gradually** to use session-based context
3. **Remove legacy code** once all pages are migrated
4. **Document breaking changes** for any external API consumers

## Metadata
- **Last Updated**: 2025-06-15
- **Django Version**: 5.1+
- **Sources**: 
  - Art Factory project implementation (Issues #82)
  - Django session framework documentation
  - Bootstrap 5 component patterns
  - Template security best practices

## Implementation Checklist

For implementing project-aware pages:

### View Layer
- [ ] Use `get_project_aware_context()` helper
- [ ] Add appropriate `project_specifier` ("for", "of", "in")
- [ ] Remove legacy URL-parameter project filtering
- [ ] Simplify view logic by removing project dropdown data

### Template Layer  
- [ ] Remove hardcoded page title/description blocks
- [ ] Use reusable filtered content components
- [ ] Add project filter pills to show filtering state
- [ ] Ensure responsive design for mobile

### API Layer
- [ ] Add project filtering to data APIs
- [ ] Support both explicit project params and session context
- [ ] Return appropriate data based on project context

### Testing
- [ ] Update tests to use session-based project context
- [ ] Test both project and no-project scenarios
- [ ] Verify component security (no template vars in JS)
- [ ] Test responsive behavior

### Documentation
- [ ] Document new components in `template-components.md`
- [ ] Update any API documentation for new filtering behavior
- [ ] Add usage examples for future developers