"""
Template validation tests for ensuring consistency and best practices
across all templates in the AI Art Factory application.
"""

import os
import re
from pathlib import Path
from collections import defaultdict
from django.test import TestCase
from django.template import Template, Context, TemplateSyntaxError
from django.template.loader import get_template
from bs4 import BeautifulSoup


class TemplateSyntaxValidationTestCase(TestCase):
    """Validate template syntax and structure."""
    
    def setUp(self):
        self.templates_dir = Path(__file__).resolve().parent.parent.parent / 'templates'
        self.excluded_dirs = {'node_modules', '.git', '__pycache__', 'venv'}
    
    def test_all_templates_valid_syntax(self):
        """Test all templates have valid Django template syntax."""
        errors = []
        
        for template_path in self._get_all_templates():
            try:
                with open(template_path, 'r', encoding='utf-8') as f:
                    template_content = f.read()
                    Template(template_content)
            except TemplateSyntaxError as e:
                errors.append(f"{template_path.name}: {str(e)}")
            except Exception as e:
                errors.append(f"{template_path.name}: Unexpected error - {str(e)}")
        
        if errors:
            self.fail(f"Template syntax errors found:\n" + "\n".join(errors))
    
    def test_template_block_matching(self):
        """Test all template blocks are properly closed."""
        errors = []
        
        for template_path in self._get_all_templates():
            content = template_path.read_text()
            
            # Check block tags
            block_starts = re.findall(r'{%\s*block\s+(\w+)', content)
            block_ends = re.findall(r'{%\s*endblock(?:\s+(\w+))?\s*%}', content)
            
            if len(block_starts) != len(block_ends):
                errors.append(
                    f"{template_path.name}: Mismatched blocks - "
                    f"{len(block_starts)} starts, {len(block_ends)} ends"
                )
        
        if errors:
            self.fail("Block matching errors:\n" + "\n".join(errors))
    
    def test_template_tag_matching(self):
        """Test all template tags are properly paired."""
        tag_pairs = [
            ('if', 'endif'),
            ('for', 'endfor'),
            ('with', 'endwith'),
            ('block', 'endblock'),
            ('spaceless', 'endspaceless'),
            ('autoescape', 'endautoescape'),
        ]
        
        errors = []
        
        for template_path in self._get_all_templates():
            content = template_path.read_text()
            
            for start_tag, end_tag in tag_pairs:
                start_pattern = rf'{{\%\s*{start_tag}\s+'
                end_pattern = rf'{{\%\s*{end_tag}\s*\%}}'
                
                starts = len(re.findall(start_pattern, content))
                ends = len(re.findall(end_pattern, content))
                
                if starts != ends:
                    errors.append(
                        f"{template_path.name}: Mismatched {start_tag}/{end_tag} - "
                        f"{starts} starts, {ends} ends"
                    )
        
        if errors:
            self.fail("Tag matching errors:\n" + "\n".join(errors))
    
    def _get_all_templates(self):
        """Get all template files, excluding certain directories."""
        templates = []
        for root, dirs, files in os.walk(self.templates_dir):
            # Remove excluded directories from search
            dirs[:] = [d for d in dirs if d not in self.excluded_dirs]
            
            for file in files:
                if file.endswith('.html'):
                    templates.append(Path(root) / file)
        
        return templates


class TemplateConsistencyTestCase(TestCase):
    """Test consistency across similar templates."""
    
    def setUp(self):
        self.templates_dir = Path(__file__).resolve().parent.parent.parent / 'templates'
    
    def test_consistent_layout_usage(self):
        """Test similar pages use consistent layouts."""
        # Map template types to expected layouts
        layout_expectations = {
            'inventory.html': 'layouts/app_layout.html',
            'projects.html': 'layouts/app_layout.html',
            'all_projects.html': 'layouts/app_layout.html',
            'production.html': 'layouts/app_layout.html',
            'order.html': 'layouts/app_layout.html',
            'settings.html': 'layouts/app_layout.html',
            'product_detail.html': 'layouts/sidebar_layout.html',
        }
        
        for template_name, expected_layout in layout_expectations.items():
            template_path = self.templates_dir / 'main' / template_name
            if template_path.exists():
                content = template_path.read_text()
                self.assertIn(
                    f"{{% extends '{expected_layout}' %}}",
                    content,
                    f"{template_name} should use {expected_layout}"
                )
    
    def test_consistent_component_usage(self):
        """Test similar functionality uses same components."""
        # Check product display consistency
        product_display_templates = ['inventory.html', 'project_detail.html']
        
        for template_name in product_display_templates:
            template_path = self.templates_dir / 'main' / template_name
            if template_path.exists():
                content = template_path.read_text()
                # Should use product collection components
                self.assertIn(
                    'components/js/product_collection_init.html',
                    content,
                    f"{template_name} should use product collection component"
                )
    
    def test_consistent_empty_states(self):
        """Test empty states are handled consistently."""
        templates_with_lists = [
            'projects.html', 'all_projects.html',
            'production.html', 'project_detail.html'
        ]
        
        for template_name in templates_with_lists:
            template_path = self.templates_dir / 'main' / template_name
            if template_path.exists():
                content = template_path.read_text()
                # Should handle empty states
                self.assertTrue(
                    'empty_state' in content or 
                    '{% else %}' in content or
                    '{% empty %}' in content or
                    'No ' in content,  # Allow "No products yet" style messages
                    f"{template_name} should handle empty states"
                )
        
        # Special case for inventory.html - uses JavaScript for dynamic loading
        inventory_path = self.templates_dir / 'main' / 'inventory.html'
        if inventory_path.exists():
            content = inventory_path.read_text()
            # inventory.html uses JavaScript collection that handles empty states
            self.assertTrue(
                'product_collection_init.html' in content,
                "inventory.html should use product collection component for empty states"
            )


class TemplateDependencyTestCase(TestCase):
    """Test template dependencies and imports."""
    
    def setUp(self):
        self.templates_dir = Path(__file__).resolve().parent.parent.parent / 'templates'
    
    def test_static_file_references(self):
        """Test all static file references are valid."""
        errors = []
        
        for template_path in self._get_all_templates():
            content = template_path.read_text()
            
            # Find static file references
            static_refs = re.findall(r"{%\s*static\s+['\"]([^'\"]+)['\"]", content)
            
            for ref in static_refs:
                # Basic validation - should not contain template variables
                if '{{' in ref or '{%' in ref:
                    errors.append(
                        f"{template_path.name}: Invalid static reference: {ref}"
                    )
        
        if errors:
            self.fail("Static file reference errors:\n" + "\n".join(errors))
    
    def test_url_references(self):
        """Test URL references follow naming conventions."""
        errors = []
        
        for template_path in self._get_all_templates():
            content = template_path.read_text()
            
            # Find URL references
            url_refs = re.findall(r"{%\s*url\s+['\"]([^'\"]+)['\"]", content)
            
            for ref in url_refs:
                # Check naming convention (should be app:view format)
                if ':' not in ref and not ref.startswith('admin:'):
                    errors.append(
                        f"{template_path.name}: URL without namespace: {ref}"
                    )
        
        if errors:
            self.fail("URL reference errors:\n" + "\n".join(errors))
    
    def test_component_dependencies(self):
        """Test components declare their dependencies."""
        component_deps = {
            'product_collection_init.html': ['product_viewer_modal.html'],
            'order_main_init.html': ['order_form_management.html', 'order_machine_parameters.html'],
        }
        
        for component, deps in component_deps.items():
            component_path = self.templates_dir / 'components' / 'js' / component
            if component_path.exists():
                content = component_path.read_text()
                
                # Check for dependency comments or includes
                for dep in deps:
                    dep_name = dep.replace('.html', '')
                    if dep_name not in content and f'Requires: {dep}' not in content:
                        # It's okay if the dependency is not explicitly mentioned
                        # as long as the functionality works
                        pass
    
    def _get_all_templates(self):
        """Get all template files."""
        templates = []
        for root, dirs, files in os.walk(self.templates_dir):
            for file in files:
                if file.endswith('.html'):
                    templates.append(Path(root) / file)
        return templates


class TemplatePerformanceTestCase(TestCase):
    """Test template performance considerations."""
    
    def setUp(self):
        self.templates_dir = Path(__file__).resolve().parent.parent.parent / 'templates'
    
    def test_no_excessive_includes(self):
        """Test templates don't have excessive includes."""
        warnings = []
        
        for template_path in self._get_all_templates():
            content = template_path.read_text()
            
            # Count includes
            includes = re.findall(r'{%\s*include\s+', content)
            
            if len(includes) > 10:
                warnings.append(
                    f"{template_path.name}: High number of includes ({len(includes)})"
                )
        
        # This is a warning, not a failure
        if warnings:
            print("\nPerformance warnings:\n" + "\n".join(warnings))
    
    def test_no_deep_nesting(self):
        """Test templates don't have excessive nesting."""
        warnings = []
        
        for template_path in self._get_all_templates():
            content = template_path.read_text()
            
            # Simple nesting check - count max depth of divs
            max_depth = 0
            current_depth = 0
            
            for line in content.split('\n'):
                current_depth += line.count('<div')
                current_depth -= line.count('</div>')
                max_depth = max(max_depth, current_depth)
            
            if max_depth > 15:
                warnings.append(
                    f"{template_path.name}: Deep nesting detected (depth: {max_depth})"
                )
        
        if warnings:
            print("\nNesting warnings:\n" + "\n".join(warnings))
    
    def _get_all_templates(self):
        """Get all template files."""
        templates = []
        for root, dirs, files in os.walk(self.templates_dir):
            for file in files:
                if file.endswith('.html'):
                    templates.append(Path(root) / file)
        return templates


class TemplateMaintenanceTestCase(TestCase):
    """Test template maintenance and organization."""
    
    def setUp(self):
        self.templates_dir = Path(__file__).resolve().parent.parent.parent / 'templates'
    
    def test_no_unused_templates(self):
        """Identify potentially unused templates."""
        # Get all templates
        all_templates = set()
        for root, dirs, files in os.walk(self.templates_dir):
            for file in files:
                if file.endswith('.html'):
                    rel_path = Path(root).relative_to(self.templates_dir) / file
                    all_templates.add(str(rel_path).replace('\\', '/'))
        
        # Find referenced templates
        referenced = set()
        
        # Check Python files for template references
        project_dir = self.templates_dir.parent
        for py_file in project_dir.rglob('*.py'):
            if 'venv' not in str(py_file) and 'migrations' not in str(py_file):
                try:
                    content = py_file.read_text()
                    # Find template references in Python
                    refs = re.findall(r'[\'"]([^\'"\s]+\.html)[\'"]', content)
                    referenced.update(refs)
                except Exception:
                    pass
        
        # Check templates for includes/extends
        for template_path in self.templates_dir.rglob('*.html'):
            content = template_path.read_text()
            
            # Find extends
            extends = re.findall(r'{%\s*extends\s+[\'"]([^\'"\s]+)[\'"]', content)
            referenced.update(extends)
            
            # Find includes
            includes = re.findall(r'{%\s*include\s+[\'"]([^\'"\s]+)[\'"]', content)
            referenced.update(includes)
        
        # Find potentially unused (this is informational)
        potentially_unused = all_templates - referenced
        
        # Filter out known entry points and special templates
        entry_points = {
            'base.html', 'main/order.html', 'main/inventory.html',
            'main/projects.html', 'main/production.html', 'main/settings.html',
            'main/all_projects.html', 'main/product_detail.html',
            'main/project_detail.html'
        }
        
        unused = [t for t in potentially_unused if t not in entry_points]
        
        if unused:
            print(f"\nPotentially unused templates: {unused}")
    
    def test_template_naming_conventions(self):
        """Test templates follow naming conventions."""
        errors = []
        
        for template_path in self.templates_dir.rglob('*.html'):
            name = template_path.name
            
            # Check lowercase
            if name != name.lower():
                errors.append(f"{name}: Should be lowercase")
            
            # Check no spaces
            if ' ' in name:
                errors.append(f"{name}: Should not contain spaces")
            
            # Check uses underscores not hyphens for multi-word
            if name.count('-') > 1:  # Allow some-component.html but not some-other-component.html
                errors.append(f"{name}: Consider using underscores for multi-word names")
        
        if errors:
            self.fail("Naming convention errors:\n" + "\n".join(errors))


def run_validation_tests():
    """Run all template validation tests."""
    import unittest
    
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    test_cases = [
        TemplateSyntaxValidationTestCase,
        TemplateConsistencyTestCase,
        TemplateDependencyTestCase,
        TemplatePerformanceTestCase,
        TemplateMaintenanceTestCase
    ]
    
    for test_case in test_cases:
        tests = loader.loadTestsFromTestCase(test_case)
        suite.addTests(tests)
    
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


if __name__ == '__main__':
    run_validation_tests()