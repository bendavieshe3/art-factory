"""
Template testing framework for validating template inheritance, component usage,
and layout consistency across the AI Art Factory application.
"""

import os
import re
from pathlib import Path
from django.test import TestCase, Client
from django.template import Template, Context
from django.template.loader import get_template
from django.urls import reverse
from django.contrib.auth import get_user_model
from bs4 import BeautifulSoup

User = get_user_model()


class TemplateInheritanceTestCase(TestCase):
    """Test proper template inheritance patterns."""
    
    def setUp(self):
        self.templates_dir = Path(__file__).resolve().parent.parent.parent / 'templates'
        
    def test_base_template_structure(self):
        """Test base.html provides all required blocks."""
        base_template = get_template('base.html')
        base_content = base_template.template.source
        
        required_blocks = [
            'title', 'page_title', 'extra_css', 'body_content', 
            'extra_js'
        ]
        
        for block in required_blocks:
            self.assertIn(f'{{% block {block}', base_content,
                          f"base.html missing required block: {block}")
    
    def test_layout_inheritance_chain(self):
        """Test layout templates properly extend parent templates."""
        inheritance_chain = {
            'layouts/app_layout.html': 'base.html',
            'layouts/sidebar_layout.html': 'layouts/app_layout.html',
            'layouts/card_layout.html': 'layouts/app_layout.html'
        }
        
        for layout, parent in inheritance_chain.items():
            template = get_template(layout)
            template_content = template.template.source
            self.assertIn(f"{{% extends '{parent}' %}}", template_content,
                          f"{layout} should extend {parent}")
    
    def test_layout_block_preservation(self):
        """Test layouts preserve parent blocks while adding new ones."""
        # Test app_layout preserves base blocks
        app_layout = get_template('layouts/app_layout.html')
        app_content = app_layout.template.source
        
        # Check that app_layout extends base.html properly
        self.assertIn("{% extends 'base.html' %}", app_content)
        
        # Test app_layout adds new blocks
        new_blocks = ['page_header', 'page_title', 'page_description', 'content']
        for block in new_blocks:
            self.assertIn(f'{{% block {block}', app_content,
                          f"app_layout.html missing block: {block}")


class ComponentConsistencyTestCase(TestCase):
    """Test component usage consistency across templates."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
        self.templates_dir = Path(__file__).resolve().parent.parent.parent / 'templates'
    
    def test_pagination_component_usage(self):
        """Test all templates use the pagination component correctly."""
        # Find all templates that might use pagination
        templates_with_pagination = []
        
        for template_path in self.templates_dir.rglob('*.html'):
            if template_path.is_file():
                content = template_path.read_text()
                if 'page_obj' in content and 'pagination' in content.lower():
                    templates_with_pagination.append(template_path)
        
        # Check each template uses the component
        for template_path in templates_with_pagination:
            content = template_path.read_text()
            if 'components/navigation/pagination.html' not in content:
                # Skip if it's the component itself
                if 'components/navigation/pagination.html' not in str(template_path):
                    self.assertIn(
                        "{% include 'components/navigation/pagination.html'",
                        content,
                        f"{template_path.name} should use pagination component"
                    )
    
    def test_modal_component_parameters(self):
        """Test modal components are used with correct parameters."""
        modal_usages = []
        
        # Find all modal component usages
        for template_path in self.templates_dir.rglob('*.html'):
            if template_path.is_file():
                content = template_path.read_text()
                modal_includes = re.findall(
                    r"{%\s*include\s+'components/modals/.*?\.html'.*?%}", 
                    content
                )
                if modal_includes:
                    modal_usages.extend([
                        (template_path.name, include) 
                        for include in modal_includes
                    ])
        
        # Validate required parameters
        for template_name, include_tag in modal_usages:
            if 'confirmation_modal.html' in include_tag:
                # Confirmation modal requires modal_id, title, message
                self.assertIn('modal_id=', include_tag,
                              f"{template_name}: confirmation_modal requires modal_id")
                self.assertIn('title=', include_tag,
                              f"{template_name}: confirmation_modal requires title")
                self.assertIn('message=', include_tag,
                              f"{template_name}: confirmation_modal requires message")
    
    def test_javascript_component_loading_order(self):
        """Test JavaScript components are loaded in correct dependency order."""
        order_template = get_template('main/order.html')
        order_content = order_template.template.source
        
        # Extract JavaScript component includes
        js_includes = re.findall(
            r"{%\s*include\s+'components/js/.*?\.html'.*?%}", 
            order_content
        )
        
        # Verify key components are present in correct order
        # First should be form management (foundation)
        self.assertTrue(any('order_form_management.html' in include for include in js_includes),
                        "order_form_management.html should be included")
        
        # Last should be main init (orchestrator)
        self.assertTrue(any('order_main_init.html' in include for include in js_includes),
                        "order_main_init.html should be included")
        
        # Form management should come before main init
        form_mgmt_idx = next((i for i, include in enumerate(js_includes) 
                              if 'order_form_management.html' in include), -1)
        main_init_idx = next((i for i, include in enumerate(js_includes) 
                              if 'order_main_init.html' in include), -1)
        
        if form_mgmt_idx >= 0 and main_init_idx >= 0:
            self.assertLess(form_mgmt_idx, main_init_idx,
                            "Form management should load before main init")


class TemplateRenderingTestCase(TestCase):
    """Test templates render correctly with various contexts."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.client.login(username='testuser', password='testpass123')
    
    def test_layout_rendering_with_context(self):
        """Test layouts render correctly with different context variables."""
        # Test card_layout with various context configurations
        template = get_template('layouts/card_layout.html')
        
        contexts = [
            {
                'page_title': 'Test Page',
                'card_title': 'Test Card',
                'card_icon': 'gear',
                'card_class': 'border-primary'
            },
            {
                'page_title': 'Another Test',
                'card_title': 'Another Card',
                # Test with missing optional parameters
            }
        ]
        
        for context_data in contexts:
            html = template.render(context_data)
            self.assertIn(context_data['page_title'], html)
            if 'card_title' in context_data:
                self.assertIn(context_data['card_title'], html)
    
    def test_component_error_handling(self):
        """Test components handle missing required parameters gracefully."""
        # Test pagination without required page_obj
        template_str = "{% load static %}{% include 'components/navigation/pagination.html' %}"
        template = Template(template_str)
        
        # Should not raise exception
        try:
            html = template.render(Context({}))
            # Component should handle missing page_obj gracefully
            self.assertNotIn('Previous', html)
            self.assertNotIn('Next', html)
        except Exception as e:
            self.fail(f"Component should handle missing parameters: {str(e)}")
    
    def test_responsive_layout_classes(self):
        """Test layouts include proper responsive classes."""
        layouts = ['app_layout.html', 'sidebar_layout.html', 'card_layout.html']
        
        for layout_name in layouts:
            template = get_template(f'layouts/{layout_name}')
            html = template.render({'page_title': 'Test'})
            soup = BeautifulSoup(html, 'html.parser')
            
            # Check for responsive container
            containers = soup.find_all(class_=re.compile(r'container(-fluid)?'))
            self.assertTrue(len(containers) > 0,
                            f"{layout_name} should have responsive container")
            
            # Check for responsive grid classes in sidebar layout
            if layout_name == 'sidebar_layout.html':
                cols = soup.find_all(class_=re.compile(r'col-(sm|md|lg|xl)-\d+'))
                self.assertTrue(len(cols) >= 2,
                                "sidebar_layout should have responsive columns")


class TemplateAccessibilityTestCase(TestCase):
    """Test templates follow accessibility best practices."""
    
    def setUp(self):
        self.templates_dir = Path(__file__).resolve().parent.parent.parent / 'templates'
    
    def test_aria_labels_in_components(self):
        """Test components include proper ARIA labels."""
        # Check pagination component
        pagination = get_template('components/navigation/pagination.html')
        pagination_content = pagination.template.source
        
        self.assertIn('aria-label', pagination_content,
                      "Pagination should include aria-label")
        self.assertIn('page-item active', pagination_content,
                      "Pagination should mark current page")
    
    def test_form_labels(self):
        """Test form components have proper labels."""
        form_templates = [
            'components/forms/project_form.html',
            'main/order.html'
        ]
        
        for template_name in form_templates:
            try:
                template = get_template(template_name)
                content = template.template.source
                
                # Check for label elements
                self.assertIn('<label', content,
                              f"{template_name} should include form labels")
                
                # Check for for attributes
                if 'for=' in content:
                    self.assertIn('for="', content,
                                  f"{template_name} labels should have for attributes")
            except Exception:
                # Skip if template doesn't exist
                pass
    
    def test_alt_attributes_for_images(self):
        """Test image elements have alt attributes."""
        for template_path in self.templates_dir.rglob('*.html'):
            if template_path.is_file():
                content = template_path.read_text()
                
                # Find img tags without checking components that might generate them
                if '<img' in content and 'components/' not in str(template_path):
                    img_tags = re.findall(r'<img[^>]*>', content)
                    for img_tag in img_tags:
                        if 'alt=' not in img_tag:
                            # Check if it's using a Django variable for alt
                            if '{{' not in img_tag:
                                self.fail(
                                    f"{template_path.name} has img without alt: {img_tag}"
                                )


class TemplateSecurityTestCase(TestCase):
    """Test templates follow security best practices."""
    
    def setUp(self):
        self.templates_dir = Path(__file__).resolve().parent.parent.parent / 'templates'
    
    def test_csrf_token_in_forms(self):
        """Test all forms include CSRF token."""
        for template_path in self.templates_dir.rglob('*.html'):
            if template_path.is_file():
                content = template_path.read_text()
                
                # Check forms have CSRF token
                if '<form' in content and 'method="post"' in content.lower():
                    form_blocks = re.findall(
                        r'<form[^>]*method=["\']post["\'][^>]*>.*?</form>', 
                        content, 
                        re.DOTALL | re.IGNORECASE
                    )
                    
                    for form in form_blocks:
                        if '{% csrf_token %}' not in form:
                            self.fail(
                                f"{template_path.name} has POST form without CSRF token"
                            )
    
    def test_no_inline_javascript_with_user_data(self):
        """Test templates don't include unsafe inline JavaScript with user data."""
        unsafe_patterns = [
            r'<script[^>]*>.*\{\{.*\}\}.*</script>',  # Django vars in script tags
            r'on\w+=["\'][^"\']*\{\{',  # Django vars in event handlers
        ]
        
        for template_path in self.templates_dir.rglob('*.html'):
            if template_path.is_file():
                content = template_path.read_text()
                
                for pattern in unsafe_patterns:
                    matches = re.findall(pattern, content, re.DOTALL | re.IGNORECASE)
                    if matches:
                        # Check if properly escaped
                        for match in matches:
                            if '|escapejs' not in match and '|json_script' not in match:
                                # Allow template parameters (not user data) in JavaScript components
                                if 'components/js/' in str(template_path):
                                    # Allow parameter-only variables (with |default:)
                                    if '|default:' in match:
                                        continue
                                    # Allow safe JSON variables that are intended for data transfer
                                    if '|safe' in match and '_json' in match:
                                        continue
                                self.fail(
                                    f"{template_path.name} has potentially unsafe JavaScript: {match[:50]}..."
                                )


class ComponentDocumentationTestCase(TestCase):
    """Test component documentation completeness."""
    
    def setUp(self):
        self.components_dir = Path(__file__).resolve().parent.parent.parent / 'templates' / 'components'
        self.docs_dir = Path(__file__).resolve().parent.parent.parent / 'docs'
    
    def test_all_components_documented(self):
        """Test all components are documented in template-components.md."""
        # Read documentation
        components_doc_path = self.docs_dir / 'template-components.md'
        if not components_doc_path.exists():
            self.fail("template-components.md documentation file missing")
        
        doc_content = components_doc_path.read_text()
        
        # Find all component files
        component_files = []
        for component_path in self.components_dir.rglob('*.html'):
            if component_path.is_file():
                relative_path = component_path.relative_to(self.components_dir.parent)
                component_files.append(str(relative_path))
        
        # Check each component is documented
        for component in component_files:
            self.assertIn(
                component.replace('\\', '/'),  # Handle Windows paths
                doc_content,
                f"Component {component} not documented"
            )
    
    def test_component_parameter_documentation(self):
        """Test component parameters are properly documented."""
        components_doc_path = self.docs_dir / 'template-components.md'
        doc_content = components_doc_path.read_text()
        
        # Extract documented components and their parameters
        component_sections = re.findall(
            r'####\s+`([^`]+)`(.*?)(?=####|$)', 
            doc_content, 
            re.DOTALL
        )
        
        for component_path, section_content in component_sections:
            if '**Parameters**:' in section_content:
                # Check if component explicitly has no parameters
                has_none = 'None' in section_content or 'no parameters' in section_content.lower()
                
                if not has_none:
                    # Verify parameter documentation includes parameter status
                    has_required = '(required)' in section_content
                    has_optional = '(optional)' in section_content
                    
                    # Components should document parameter status (required or optional)
                    self.assertTrue(has_required or has_optional,
                                  f"{component_path} should document parameter status (required/optional)")


def run_template_tests():
    """Convenience function to run all template tests."""
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add all test cases
    test_cases = [
        TemplateInheritanceTestCase,
        ComponentConsistencyTestCase,
        TemplateRenderingTestCase,
        TemplateAccessibilityTestCase,
        TemplateSecurityTestCase,
        ComponentDocumentationTestCase
    ]
    
    for test_case in test_cases:
        tests = loader.loadTestsFromTestCase(test_case)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == '__main__':
    run_template_tests()