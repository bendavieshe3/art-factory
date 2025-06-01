# Django UI Patterns and Best Practices

## Topics Covered
- Toast notification systems for Django applications
- CSS organization strategies for Django projects
- JavaScript integration patterns with Django templates
- UI testing approaches for Django frontend components
- Alert system replacements and user experience improvements

## Main Content

### Toast Notification System Implementation

**Problem**: Browser `alert()` calls are intrusive and block user interaction, creating poor UX.

**Solution**: Implement elegant toast notification system with:

```css
.toast-container {
    position: fixed;
    top: 20px;
    right: 20px;
    z-index: 1000;
    max-width: 400px;
}

.toast {
    background: white;
    border-radius: 8px;
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    transform: translateX(100%);
    transition: all 0.3s ease;
    opacity: 0;
}

.toast.show {
    transform: translateX(0);
    opacity: 1;
}
```

**JavaScript API Pattern**:
```javascript
window.Toast = {
    success: function(message, title = null, duration = 5000),
    error: function(message, title = null, duration = 7000),
    warning: function(message, title = null, duration = 6000),
    info: function(message, title = null, duration = 5000)
};
```

**Integration with Django AJAX**:
```javascript
.then(data => {
    if (data.success) {
        Toast.success(`Order #${data.order_id} placed successfully!`, 'Order Placed');
    } else {
        Toast.error(data.error || 'Unknown error occurred', 'Order Failed');
    }
})
```

### CSS Organization for Django Projects

**Current Pattern**: Inline styles in base.html template
- ✅ **Pros**: Single file, no external dependencies, fast initial development
- ❌ **Cons**: Hard to maintain, no component reusability, large template files

**Framework Decision Points**:
1. **Tailwind CSS**: Utility-first, highly customizable, good for rapid prototyping
2. **Bootstrap**: Component-based, mature ecosystem, faster initial development
3. **Custom CSS**: Full control, no external dependencies, requires more development time

### JavaScript Testing in Django

**Testing Toast Notifications**:
```python
def test_order_page_loads_with_toast_system(self):
    response = self.client.get('/')
    self.assertContains(response, 'toast-container')
    self.assertContains(response, 'window.Toast')
    self.assertNotContains(response, 'alert(')
```

**UI Integration Testing**:
- Test that templates load required JavaScript
- Verify CSS classes are present
- Check that old patterns (like `alert()`) are removed
- Validate API responses provide correct data for frontend

### Parameter Merging Pattern for Django APIs

**Problem**: Factory machine default parameters weren't being merged with user parameters.

**Solution**:
```python
# In views.py - merge defaults with user input
merged_parameters = machine.default_parameters.copy()
merged_parameters.update(order.base_parameters)

OrderItem.objects.create(
    order=order,
    prompt=order.prompt,
    parameters=merged_parameters,  # Includes safety checker settings
    status='pending'
)
```

**Testing Pattern**:
```python
@patch('main.tasks.process_order_items_async')
def test_successful_order_shows_success_toast(self, mock_process):
    # Test API provides correct data for toast notifications
    response = self.client.post('/api/place-order/', data=json.dumps(order_data))
    data = json.loads(response.content)
    self.assertIn('order_id', data)
    self.assertIn('message', data)
```

## Local Considerations

### Art Factory Project Specifics
- Using Django 5.2.1 with Python 3.13.3
- SQLite for development (handles BigIntegerField seed values with special handling)
- Background task processing using Django signals + threading
- AI provider integration (fal.ai, Replicate) with parameter validation

### Development Workflow Established
1. **Write tests first** for UI components
2. **Implement feature** with clean separation of concerns  
3. **Test in browser** for UX validation
4. **Commit with comprehensive messages** linking to issue resolution

### Performance Considerations
- Toast notifications use CSS transforms for smooth animations
- Auto-hide timers prevent notification accumulation
- Non-blocking UI patterns preferred over modal dialogs
- Background processing keeps UI responsive during AI generation

### Browser Compatibility
- CSS custom properties used sparingly for wider support
- JavaScript ES6+ features acceptable for modern development
- Graceful degradation for missing JavaScript support

## Metadata
- **Last Updated**: 2025-06-01
- **Version**: Django 5.2.1, Art Factory v1.0-dev
- **Sources**: 
  - Direct implementation experience in Art Factory project
  - Django 5.2 documentation patterns
  - Modern web UI best practices
  - Browser notification API alternatives