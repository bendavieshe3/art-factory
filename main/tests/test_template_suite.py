"""
Comprehensive template testing suite for AI Art Factory.
Runs all template-related tests and provides detailed reporting.
"""

import os
import sys
import unittest
from pathlib import Path
from django.test import TestCase
from django.test.utils import setup_test_environment, teardown_test_environment
from django.conf import settings

# Import all template test modules
from .test_template_framework import (
    TemplateInheritanceTestCase,
    ComponentConsistencyTestCase,
    TemplateRenderingTestCase,
    TemplateAccessibilityTestCase,
    TemplateSecurityTestCase,
    ComponentDocumentationTestCase
)

from .test_template_validation import (
    TemplateSyntaxValidationTestCase,
    TemplateConsistencyTestCase as ValidationConsistencyTestCase,
    TemplateDependencyTestCase,
    TemplatePerformanceTestCase,
    TemplateMaintenanceTestCase
)


class TemplateTestRunner:
    """Custom test runner for template tests with detailed reporting."""
    
    def __init__(self, verbosity=2):
        self.verbosity = verbosity
        self.results = {
            'passed': 0,
            'failed': 0,
            'errors': 0,
            'skipped': 0,
            'warnings': []
        }
    
    def run_all_tests(self):
        """Run all template tests and generate report."""
        print("=" * 70)
        print("AI ART FACTORY - TEMPLATE TESTING SUITE")
        print("=" * 70)
        print()
        
        # Setup Django test environment
        setup_test_environment()
        
        try:
            # Create test suite
            loader = unittest.TestLoader()
            suite = unittest.TestSuite()
            
            # Test categories
            test_categories = {
                'Template Framework Tests': [
                    TemplateInheritanceTestCase,
                    ComponentConsistencyTestCase,
                    TemplateRenderingTestCase,
                    TemplateAccessibilityTestCase,
                    TemplateSecurityTestCase,
                    ComponentDocumentationTestCase
                ],
                'Template Validation Tests': [
                    TemplateSyntaxValidationTestCase,
                    ValidationConsistencyTestCase,
                    TemplateDependencyTestCase,
                    TemplatePerformanceTestCase,
                    TemplateMaintenanceTestCase
                ]
            }
            
            # Run tests by category
            for category_name, test_cases in test_categories.items():
                print(f"\n{category_name}")
                print("-" * len(category_name))
                
                category_suite = unittest.TestSuite()
                for test_case in test_cases:
                    tests = loader.loadTestsFromTestCase(test_case)
                    category_suite.addTests(tests)
                
                # Run category tests
                runner = unittest.TextTestRunner(
                    verbosity=self.verbosity,
                    stream=sys.stdout
                )
                result = runner.run(category_suite)
                
                # Update results
                self.results['passed'] += result.testsRun - len(result.failures) - len(result.errors)
                self.results['failed'] += len(result.failures)
                self.results['errors'] += len(result.errors)
                self.results['skipped'] += len(result.skipped)
            
            # Generate summary report
            self._generate_report()
            
        finally:
            teardown_test_environment()
    
    def _generate_report(self):
        """Generate detailed test report."""
        print("\n" + "=" * 70)
        print("TEMPLATE TEST SUMMARY")
        print("=" * 70)
        
        total_tests = sum([
            self.results['passed'],
            self.results['failed'],
            self.results['errors'],
            self.results['skipped']
        ])
        
        print(f"\nTotal Tests Run: {total_tests}")
        print(f"Passed: {self.results['passed']} ✓")
        print(f"Failed: {self.results['failed']} ✗")
        print(f"Errors: {self.results['errors']} ⚠")
        print(f"Skipped: {self.results['skipped']} ○")
        
        if self.results['warnings']:
            print("\nWarnings:")
            for warning in self.results['warnings']:
                print(f"  - {warning}")
        
        # Calculate success rate
        if total_tests > 0:
            success_rate = (self.results['passed'] / total_tests) * 100
            print(f"\nSuccess Rate: {success_rate:.1f}%")
            
            if success_rate == 100:
                print("\n✅ All template tests passed!")
            elif success_rate >= 80:
                print("\n⚠️  Most template tests passed, but some issues need attention.")
            else:
                print("\n❌ Significant template issues detected. Please fix failing tests.")
        
        print("\n" + "=" * 70)


class TemplateLintCommand:
    """Command-line interface for template linting."""
    
    @staticmethod
    def run(args=None):
        """Run template linting with optional arguments."""
        import argparse
        
        parser = argparse.ArgumentParser(
            description='Run template tests for AI Art Factory'
        )
        parser.add_argument(
            '--category',
            choices=['framework', 'validation', 'all'],
            default='all',
            help='Test category to run'
        )
        parser.add_argument(
            '--verbosity',
            type=int,
            choices=[0, 1, 2],
            default=2,
            help='Test output verbosity'
        )
        parser.add_argument(
            '--fail-fast',
            action='store_true',
            help='Stop on first failure'
        )
        
        args = parser.parse_args(args)
        
        # Run appropriate tests
        if args.category == 'all':
            runner = TemplateTestRunner(verbosity=args.verbosity)
            runner.run_all_tests()
        else:
            # Run specific category
            loader = unittest.TestLoader()
            suite = unittest.TestSuite()
            
            if args.category == 'framework':
                test_cases = [
                    TemplateInheritanceTestCase,
                    ComponentConsistencyTestCase,
                    TemplateRenderingTestCase,
                    TemplateAccessibilityTestCase,
                    TemplateSecurityTestCase,
                    ComponentDocumentationTestCase
                ]
            elif args.category == 'validation':
                test_cases = [
                    TemplateSyntaxValidationTestCase,
                    ValidationConsistencyTestCase,
                    TemplateDependencyTestCase,
                    TemplatePerformanceTestCase,
                    TemplateMaintenanceTestCase
                ]
            
            for test_case in test_cases:
                tests = loader.loadTestsFromTestCase(test_case)
                suite.addTests(tests)
            
            runner = unittest.TextTestRunner(
                verbosity=args.verbosity,
                failfast=args.fail_fast
            )
            runner.run(suite)


# Django management command integration
class Command:
    """Django management command for template testing."""
    
    help = 'Run template tests and validation'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--category',
            choices=['framework', 'validation', 'all'],
            default='all',
            help='Test category to run'
        )
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Attempt to fix issues automatically (where possible)'
        )
    
    def handle(self, *args, **options):
        category = options.get('category', 'all')
        fix_issues = options.get('fix', False)
        
        if fix_issues:
            print("Auto-fix mode enabled (where supported)")
            # Future: Implement auto-fix functionality
        
        runner = TemplateTestRunner()
        runner.run_all_tests()


def main():
    """Main entry point for running template tests."""
    # Check if Django is configured
    if not settings.configured:
        import django
        os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'ai_art_factory.test_settings')
        django.setup()
    
    # Run tests
    runner = TemplateTestRunner()
    runner.run_all_tests()


if __name__ == '__main__':
    main()