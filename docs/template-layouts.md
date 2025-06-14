# Template Layout Usage Guidelines

This document provides guidelines for selecting and using the appropriate Django template layout in the AI Art Factory application.

## Layout System Overview

The application uses a hierarchical layout system built on Django template inheritance:

```
base.html
└── layouts/
    ├── app_layout.html (extends base.html)
    ├── sidebar_layout.html (extends app_layout.html)
    └── card_layout.html (extends app_layout.html)
```

## Available Layouts

### 1. `layouts/app_layout.html` - Standard Application Layout

**When to use:**
- General-purpose pages with standard navigation
- Pages requiring full-width content area
- Dashboard and overview pages
- Form pages without complex sidebars
- Gallery and grid layouts

**Features:**
- Full-width responsive container (`container-fluid`)
- Top navigation bar with site branding
- Page header with title and optional description
- Django messages display area
- Toast notification system integration
- Flexible content block structure

**Block Structure:**
```django
{% block page_header %}
{% block page_title %}
{% block page_description %}
{% block content %}
```

**Example Pages:**
- Order form (`order.html`)
- Inventory gallery (`inventory.html`)
- Projects overview (`projects.html`)
- Production dashboard (`production.html`)
- Settings page (`settings.html`)

**Usage Example:**
```django
{% extends 'layouts/app_layout.html' %}

{% block page_title %}My Page Title{% endblock %}

{% block page_description %}
<p class="text-muted mb-0">Page description goes here</p>
{% endblock %}

{% block content %}
<!-- Your page content here -->
{% endblock %}
```

### 2. `layouts/sidebar_layout.html` - Two-Column Layout

**When to use:**
- Detail pages requiring supplementary information
- Pages with primary content and secondary metadata
- Complex forms with help/reference information
- Documentation or reference pages

**Features:**
- Two-column responsive layout (8/4 column split on lg+ screens)
- Extends `app_layout.html` (includes all standard features)
- Responsive stacking on smaller screens
- Dedicated blocks for main content and sidebar

**Block Structure:**
```django
{% block main_content %}    <!-- 8 columns on large screens -->
{% block sidebar_content %}  <!-- 4 columns on large screens -->
```

**Example Pages:**
- Product detail view (`product_detail.html`)

**Usage Example:**
```django
{% extends 'layouts/sidebar_layout.html' %}

{% block page_title %}Product Detail{% endblock %}

{% block main_content %}
<!-- Primary content (product image, description) -->
{% endblock %}

{% block sidebar_content %}
<!-- Metadata, actions, related information -->
{% endblock %}
```

### 3. `layouts/card_layout.html` - Card-Wrapped Layout

**When to use:**
- Single-focus interfaces
- Configuration forms
- Modal-like content
- Simple data entry pages
- Settings panels

**Features:**
- Bootstrap card wrapper with configurable styling
- Optional card header with icon and actions
- Flexible card body and footer blocks
- Extends `app_layout.html` (includes all standard features)

**Block Structure:**
```django
{% block card_header %}
{% block card_title %}
{% block card_actions %}
{% block card_content %}
{% block card_footer %}
```

**Context Variables:**
- `card_class` - Additional CSS classes for card element
- `card_title` - Card header title text
- `card_icon` - Bootstrap icon name for header
- `card_actions` - HTML for header action buttons
- `header_class` - Additional CSS classes for card header
- `body_class` - Additional CSS classes for card body

**Usage Example:**
```django
{% extends 'layouts/card_layout.html' %}

{% block page_title %}Settings{% endblock %}

<!-- Pass context variables for card configuration -->
{% block content %}
{% with card_title="API Configuration" card_icon="gear" %}
    {{ block.super }}
{% endwith %}
{% endblock %}

{% block card_content %}
<!-- Form or content goes here -->
{% endblock %}
```

## Layout Selection Decision Tree

```
Is this a detail page for a specific item (product, order, etc.)?
├─ YES: Does it need supplementary information panel?
│  ├─ YES: Use sidebar_layout.html
│  └─ NO: Use app_layout.html
└─ NO: Is this a focused, single-purpose interface?
   ├─ YES: Use card_layout.html
   └─ NO: Use app_layout.html
```

## Component Integration

All layouts include integration with:

### Core Components
- **Navigation**: Consistent site navigation with active page indicators
- **Toast System**: Global toast notification system
- **Product Viewer Modal**: Site-wide product viewing modal
- **Django Messages**: Server-side message display

### CSS/JS Dependencies
- **Bootstrap 5.3.3**: Complete CSS framework
- **Bootstrap Icons**: Icon font for UI elements
- **Product Components CSS**: Custom styling for product-related components
- **Product Viewer Modal CSS**: Modal-specific styling

## Best Practices

### 1. Layout Consistency
- Use the same layout for related pages (e.g., all listing pages use `app_layout.html`)
- Maintain consistent page header patterns
- Follow established block naming conventions

### 2. Responsive Design
- All layouts are responsive and mobile-friendly
- Test layouts at different screen sizes
- Use appropriate Bootstrap grid classes

### 3. Context Variables
- Pass layout-specific context variables from views when needed
- Use meaningful variable names that match the layout's expectations
- Document any custom context variables in view comments

### 4. Block Organization
- Keep blocks focused and single-purpose
- Use descriptive block names
- Avoid deeply nested block overrides

### 5. Performance Considerations
- Layouts include optimized CSS/JS loading
- Use component templates to avoid code duplication
- Leverage Django's template caching where appropriate

## Common Patterns

### Page Header Pattern
```django
{% block page_title %}{{ object.name }}{% endblock %}

{% block page_description %}
<p class="text-muted mb-0">{{ object.description }}</p>
{% endblock %}
```

### Breadcrumb Integration
```django
{% block page_header %}
<nav aria-label="breadcrumb">
    <ol class="breadcrumb">
        <li class="breadcrumb-item"><a href="{% url 'main:home' %}">Home</a></li>
        <li class="breadcrumb-item active">{{ page_title }}</li>
    </ol>
</nav>
{{ block.super }}
{% endblock %}
```

### Conditional Layout Elements
```django
{% block content %}
{% if user_has_permission %}
    <!-- Content for authorized users -->
{% else %}
    <!-- Limited content or login prompt -->
{% endif %}
{% endblock %}
```

## Migration Guide

### Converting from Direct base.html Extension
```django
<!-- OLD -->
{% extends 'base.html' %}

<!-- NEW -->
{% extends 'layouts/app_layout.html' %}
<!-- Remove manual navigation, header, and container markup -->
```

### Converting to Sidebar Layout
```django
<!-- OLD -->
{% extends 'layouts/app_layout.html' %}
{% block content %}
<div class="row">
    <div class="col-lg-8"><!-- main --></div>
    <div class="col-lg-4"><!-- sidebar --></div>
</div>
{% endblock %}

<!-- NEW -->
{% extends 'layouts/sidebar_layout.html' %}
{% block main_content %}<!-- main -->{% endblock %}
{% block sidebar_content %}<!-- sidebar -->{% endblock %}
```

## Testing Layout Changes

When modifying layouts or switching between layouts:

1. **Visual Testing**: Test at multiple screen sizes (mobile, tablet, desktop)
2. **Functional Testing**: Verify all interactive elements work correctly
3. **Template Tests**: Run Django template tests to ensure proper inheritance
4. **Component Tests**: Verify component integration still functions
5. **Cross-Page Testing**: Check that layout changes don't break related pages

## Related Documentation

- `docs/design.md` - Frontend Architecture (Section 5)
- `docs/ux.md` - User Experience requirements
- `docs/testing.md` - Testing standards for templates
- `templates/components/` - Reusable component documentation