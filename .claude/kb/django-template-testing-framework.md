# Django Template Testing Framework

## Topics Covered
- Template inheritance validation
- Component consistency testing
- Template security testing
- Accessibility compliance testing
- Template documentation validation
- Django template syntax validation
- Performance testing for templates

## Main Content

### Overview

A comprehensive template testing framework for Django applications that validates template inheritance, component usage, security, accessibility, and consistency. This framework was developed for the AI Art Factory project to ensure template quality and maintainability.

### Framework Architecture

The template testing framework consists of three main modules:

1. **test_template_framework.py** - Core template testing functionality
   - Template inheritance validation
   - Component consistency checks
   - Rendering tests with various contexts
   - Accessibility compliance
   - Security best practices
   - Component documentation validation

2. **test_template_validation.py** - Template syntax and structure validation
   - Django template syntax validation
   - Block and tag matching verification
   - Template consistency across similar pages
   - Static file and URL reference validation
   - Performance considerations
   - Template maintenance checks

3. **test_template_suite.py** - Comprehensive test runner and reporting
   - Categorized test execution
   - Detailed reporting with success metrics
   - Command-line interface for selective testing
   - Django management command integration

### Key Testing Categories

#### 1. Template Inheritance Testing
```python
class TemplateInheritanceTestCase(TestCase):
    def test_base_template_structure(self):
        """Test base.html provides all required blocks."""
        base_template = get_template('base.html')
        base_content = base_template.template.source
        
        required_blocks = ['title', 'page_title', 'extra_css', 'body_content', 'extra_js']
        for block in required_blocks:
            self.assertIn(f'{{% block {block}', base_content)
```

#### 2. Component Consistency Testing
- Validates that all templates use standardized components
- Checks component parameter usage
- Verifies JavaScript component loading order
- Tests component error handling

#### 3. Security Testing
```python
def test_csrf_token_in_forms(self):
    """Test all forms include CSRF token."""
    # Validates all POST forms have {% csrf_token %}
    
def test_no_inline_javascript_with_user_data(self):
    """Test templates don't include unsafe inline JavaScript."""
    # Checks for unescaped user data in script tags
```

#### 4. Accessibility Testing
- ARIA labels and attributes validation
- Form label associations
- Alt attributes for images
- Keyboard navigation support

#### 5. Performance Testing
- Identifies excessive template includes
- Detects deep HTML nesting
- Validates efficient template structure

### Implementation Patterns

#### Running Template Tests
```bash
# Run all template tests via Django
python manage.py test main.tests.test_template_framework --settings=ai_art_factory.test_settings
python manage.py test main.tests.test_template_validation --settings=ai_art_factory.test_settings

# Run template test suite with detailed reporting
python main/tests/test_template_suite.py

# Run specific test categories
python main/tests/test_template_suite.py --category framework
python main/tests/test_template_suite.py --category validation
```

#### Test Output Example
```
======================================================================
AI ART FACTORY - TEMPLATE TESTING SUITE
======================================================================

Template Framework Tests
------------------------
✓ Template inheritance chain validated
✓ Component usage consistency verified
✓ Accessibility standards met
✓ Security best practices followed

Template Validation Tests
-------------------------
✓ All templates have valid syntax
✓ Block and tag matching correct
✓ URL references properly namespaced
✓ Static file references valid

======================================================================
TEMPLATE TEST SUMMARY
======================================================================

Total Tests Run: 45
Passed: 45 ✓
Failed: 0 ✗
Errors: 0 ⚠
Skipped: 0 ○

Success Rate: 100.0%

✅ All template tests passed!
======================================================================
```

### Common Issues and Solutions

#### 1. F-string Syntax Errors in Regex Patterns
**Problem**: F-strings with curly braces in regex patterns cause syntax errors
```python
# Invalid
start_pattern = rf'{%\s*{start_tag}\s+'
```

**Solution**: Escape curly braces properly
```python
# Valid
start_pattern = rf'{{\%\s*{start_tag}\s+'
```

#### 2. Template Context Type Errors
**Problem**: Passing Django Context object instead of dictionary
```python
# Invalid
html = template.render(Context(context_data))
```

**Solution**: Pass dictionary directly
```python
# Valid
html = template.render(context_data)
```

#### 3. Component Documentation Completeness
**Problem**: Test fails when components aren't documented
**Solution**: Maintain comprehensive component documentation in `docs/template-components.md`

### Best Practices

1. **Test Organization**
   - Keep template tests separate from functional tests
   - Use descriptive test method names
   - Group related tests in test cases

2. **Component Testing**
   - Test components with various parameter combinations
   - Validate error handling for missing parameters
   - Ensure components work in different contexts

3. **Documentation**
   - Document all components with parameters and examples
   - Keep documentation synchronized with implementation
   - Include usage examples for each component

4. **Performance Considerations**
   - Limit template include depth
   - Avoid excessive nesting
   - Use template caching where appropriate

## Local Considerations

### Django Version Compatibility
- Framework tested with Django 5.1+
- Uses Django's built-in TestCase framework
- Compatible with Django's template engine

### Dependencies
- BeautifulSoup4 for HTML parsing in tests
- Standard Django test framework
- No additional test runners required

### Integration with CI/CD
- Tests can be included in GitHub Actions workflows
- Fast execution suitable for CI pipelines
- Clear output for debugging failures

## Metadata
- **Last Updated**: 2025-06-15
- **Version**: 1.0
- **Sources**: 
  - AI Art Factory implementation experience
  - Django testing documentation
  - Web accessibility standards (WCAG)
  - Django security best practices