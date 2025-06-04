# Notification System Documentation

This directory contains the enhanced notification system for AI Art Factory, providing consistent toast notifications and error banners across the application.

## Components

### 1. Toast System (`toast_system.html`)

A comprehensive toast notification system with Bootstrap 5 integration.

#### Features
- **Responsive Design**: Adapts to mobile (bottom) and desktop (top-right)
- **Accessibility**: Screen reader announcements and ARIA attributes
- **Progressive Enhancement**: Works with and without JavaScript
- **Consistent Styling**: Bootstrap-compatible colors and typography
- **Progress Support**: Optional progress bars for long operations
- **Auto-dismissal**: Configurable timeouts with persistent option

#### API Reference

```javascript
// Basic usage
ToastNotification.show(message, type, options)

// Convenience methods
ToastNotification.success("Order completed successfully!")
ToastNotification.error("Failed to save settings", "Error", { persistent: true })
ToastNotification.warning("Connection unstable", "Warning", { duration: 10000 })
ToastNotification.info("New features available", "Info")

// Advanced usage with progress
const toastId = ToastNotification.show("Uploading...", "info", { 
    progress: true, 
    persistent: true 
});
ToastNotification.updateProgress(toastId, 50); // Update to 50%

// Backward compatibility
Toast.success("Still works!")
showToast('success', 'Legacy function works too!')
```

#### Options Object
```javascript
{
    title: "Custom Title",          // Override default title
    duration: 5000,                 // Auto-hide delay (0 for persistent)
    persistent: false,              // Don't auto-hide
    progress: false,                // Show progress bar
    icon: "bi-custom-icon"          // Custom Bootstrap icon
}
```

### 2. Error Banner (`error_banner.html`)

Reusable error banner component with expandable details and action buttons.

#### Features
- **Expandable Details**: Collapsible technical information
- **Action Buttons**: Custom action buttons for error resolution
- **Multiple Types**: Error, warning, info variants
- **Responsive Layout**: Mobile-optimized layout
- **Screen Reader Support**: Proper ARIA announcements

#### API Reference

```javascript
// Basic usage
ErrorBanner.showError('errorBanner', "Failed to load data")

// With description and details
ErrorBanner.showError('errorBanner', "Network Error", {
    description: "Unable to connect to the server",
    details: "HTTP 500: Internal Server Error\nStack trace...",
    duration: 10000  // Auto-hide after 10 seconds
})

// With action buttons
ErrorBanner.showError('errorBanner', "Upload failed", {
    actions: [
        {
            text: "Retry",
            icon: "bi-arrow-clockwise",
            class: "btn-outline-primary",
            handler: () => retryUpload()
        },
        {
            text: "Cancel",
            class: "btn-outline-secondary", 
            handler: () => cancelUpload()
        }
    ]
})

// Different types
ErrorBanner.showWarning('warningBanner', "Quota almost exceeded")
ErrorBanner.showInfo('infoBanner', "Maintenance scheduled")

// Backward compatibility
showErrorBanner("Error message", "Technical details")
```

#### Template Usage
```html
{% include 'components/notifications/error_banner.html' with banner_id='myErrorBanner' %}
```

## Integration

### In Templates

```html
<!-- Base template automatically includes toast system -->
{% extends 'layouts/app_layout.html' %}

<!-- Include error banner where needed -->
{% include 'components/notifications/error_banner.html' with banner_id='pageErrorBanner' %}
```

### In JavaScript

```javascript
// Form submission example
fetch('/api/submit-form', { method: 'POST', body: formData })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            ToastNotification.success("Form submitted successfully!");
        } else {
            ErrorBanner.showError('formErrorBanner', data.error, {
                description: "Please correct the issues and try again",
                details: JSON.stringify(data.errors, null, 2)
            });
        }
    })
    .catch(error => {
        ToastNotification.error("Network error occurred", "Connection Failed", {
            persistent: true
        });
    });
```

## Design Patterns

### When to Use Toasts vs Banners

**Use Toasts for:**
- Success confirmations
- Non-critical information
- Temporary status updates
- Background operation results

**Use Error Banners for:**
- Form validation errors
- Critical system errors
- Errors requiring user action
- Page-level error states

### Toast Types and Durations

| Type | Duration | Use Case |
|------|----------|----------|
| Success | 5s | Confirmations, completions |
| Info | 5s | General information, tips |
| Warning | 6s | Cautionary messages |
| Error | 7s | Non-critical errors |
| Persistent | ∞ | Critical errors, user action required |

### Color Scheme

All components use Bootstrap 5 CSS custom properties for consistent theming:

- **Success**: `--bs-success` (Green)
- **Error/Danger**: `--bs-danger` (Red) 
- **Warning**: `--bs-warning` (Yellow)
- **Info**: `--bs-info` (Blue)

## Accessibility

### Screen Reader Support
- Automatic ARIA announcements
- Proper `role` attributes (`alert` for errors, `status` for info)
- `aria-live` regions for dynamic content

### Keyboard Navigation
- Error banner details are keyboard accessible
- Focus management for interactive elements
- Skip links for repetitive notifications

### Motion Sensitivity
- Respects `prefers-reduced-motion` settings
- Graceful degradation for animation-disabled environments

## Browser Compatibility

- **Modern Browsers**: Full feature support
- **IE11**: Basic functionality (graceful degradation)
- **Mobile Browsers**: Responsive layout adaptations
- **Screen Readers**: NVDA, JAWS, VoiceOver tested

## Testing

Components include comprehensive test coverage in:
- `main/test_ui_notifications.py` - Python/Django tests
- `main/test_bootstrap_integration.py` - Bootstrap integration tests

Run tests with:
```bash
python manage.py test main.test_ui_notifications
```

## Migration Notes

### From Legacy System
The enhanced system maintains backward compatibility:

```javascript
// Old API still works
Toast.success("message")
showToast('success', 'message') 
showErrorBanner("error", "details")

// But new API is preferred
ToastNotification.success("message")
ErrorBanner.showError('bannerId', "error", { details: "details" })
```

### Breaking Changes
- Toast container positioning changed from `top: 20px` to Bootstrap standard
- Mobile toast positioning moved from top-right to bottom
- Some CSS classes renamed for Bootstrap compatibility

## Future Enhancements

Planned improvements:
- [ ] Queue management for multiple notifications
- [ ] Notification persistence across page reloads
- [ ] Integration with WebSocket for real-time notifications
- [ ] Custom notification sounds (with user preference)
- [ ] Notification history/log viewer