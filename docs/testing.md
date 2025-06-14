# Testing Strategy and Implementation Guide

## Overview

Art Factory maintains a comprehensive Django-first testing approach that balances thorough coverage with sustainable development practices. This document outlines our testing philosophy, current implementation, target state, and roadmap for continuous improvement.

## Current State Assessment

### Testing Infrastructure
- **Framework**: Django's built-in unittest framework (1550+ lines of tests)
- **Test Runner**: Custom `run_tests.sh` with categorized test suites and coverage support
- **Coverage**: Comprehensive coverage reporting with coverage.py (14.71% baseline)
- **Database**: In-memory SQLite for fast test execution
- **Configuration**: Dedicated `test_settings.py` with proper isolation

### Test Coverage Areas

**Excellent Coverage:**
- Core models (Order, OrderItem, Product, FactoryMachineDefinition)
- API endpoints with validation and error handling
- Worker system and batch processing
- UI integration (Bootstrap, notifications, dynamic parameters)
- Background task processing and retry mechanisms

**Well-Covered Areas:**
- Django signals and model lifecycle
- Management commands
- External API integration (mocked)
- End-to-end workflow testing
- Project management operations (CRUD, associations)

### Test Organization

Art Factory follows Django's standard test organization with descriptive naming for different test categories:

#### Core Test Files
```
main/
├── tests.py                          # Core Django test suite (1550+ lines)
│                                     # Contains: ModelTestCase, ViewTestCase, SignalTestCase, 
│                                     #          TaskTestCase, ManagementCommandTestCase,
│                                     #          IntegrationTestCase, BatchGenerationTestCase
│
├── test_worker_system.py            # Worker system integration tests
├── test_dynamic_parameters.py       # Dynamic parameter handling (unit tests)
├── test_bootstrap_integration.py    # Bootstrap 5 UI integration tests
├── test_ui_notifications.py         # Toast notification system tests
├── test_async_processing.py         # Async processing and retry tests
├── test_negative_prompts.py         # Negative prompt functionality tests
├── test_batch_generation.py         # Batch generation integration tests
├── test_sdxl_fix.py                 # SDXL model fix validation tests
│
├── test_template_framework.py       # Template inheritance and component tests
├── test_template_validation.py      # Template syntax and consistency validation
└── test_template_suite.py           # Comprehensive template testing runner
```

#### Test Categories
- **Unit Tests**: Fast, isolated tests for business logic (test_dynamic_parameters.py, test_negative_prompts.py)
- **Integration Tests**: Tests that combine multiple components (test_bootstrap_integration.py, test_worker_system.py, test_async_processing.py)
- **UI Tests**: Frontend component and interaction tests (test_ui_notifications.py, test_bootstrap_integration.py)
- **System Tests**: End-to-end workflow validation (test_batch_generation.py, test_sdxl_fix.py)
- **Template Tests**: Template inheritance, component usage, and validation (test_template_framework.py, test_template_validation.py)

#### Management Commands
```
main/management/commands/
└── test_fal.py                      # Test utility for fal.ai integration
```

### Project Management Tests

The project management system includes comprehensive tests covering:

**Core Project Operations:**
- Test project CRUD operations (create, read, update, delete)
- Test order-project associations  
- Test product count denormalization via signals
- Test featured product management
- Test project status transitions
- Test bulk operations on projects

**Integration Tests:**
- Test project filtering in inventory views
- Test project context in order creation
- Test batch product assignment to projects
- Test project deletion with cascading behavior
- Test project count updates on product/order changes

**Test Files:**
- `test_batch_project_assignment.py` - Tests for batch product project inheritance
- `test_inventory_project_filtering.py` - Tests for inventory filtering by project
- General project tests in main test suite

## Target State Vision

### Quality Standards
- **Coverage Target**: 95%+ line coverage, 90%+ branch coverage
- **Performance**: Full test suite executes in <2 minutes
- **Reliability**: Zero flaky tests, deterministic execution
- **Maintainability**: 50% reduction in test setup duplication

### Testing Pyramid
1. **Unit Tests (70%)**: Fast, isolated tests for business logic
2. **Integration Tests (20%)**: API endpoints, database interactions
3. **End-to-End Tests (10%)**: Complete user workflows

### Technology Stack Evolution
- **Core**: Maintain Django TestCase framework (Django-first philosophy)
- **Enhancement**: Add coverage.py, Factory Boy, Hypothesis
- **CI/CD**: GitHub Actions with automated coverage reporting
- **Performance**: django-silk for profiling, locust for load testing

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2)
**Priority: Critical**

#### 1.1 Coverage Reporting
```bash
pip install coverage
```
- Implement comprehensive coverage tracking
- Add coverage badges and reporting to CI/CD
- Establish coverage thresholds to prevent regression

#### 1.2 Resource Management Fixes
**Critical Issue**: File system and worker cleanup
- Add `tearDown()` methods for file cleanup
- Implement proper worker lifecycle management
- Fix memory leaks from mock data accumulation

#### 1.3 CI/CD Pipeline
- GitHub Actions workflow for automated testing
- Coverage integration with Codecov
- Test result formatting and trend analysis

### Phase 2: Quality Enhancement (Weeks 3-4)
**Priority: High**

#### 2.1 Test Data Management
```bash
pip install factory-boy
```
- Replace repetitive `setUp()` methods with Factory Boy
- Create reusable test data factories
- Reduce test maintenance burden

#### 2.2 Security Testing
- Add parameter injection attack tests
- Validate authentication/authorization flows
- Test safety checker bypass prevention

#### 2.3 Performance Baseline
```bash
pip install django-silk
```
- Add development profiling with django-silk
- Establish performance benchmarks
- Monitor database query performance

### Phase 3: Advanced Capabilities (Weeks 5-8)
**Priority: Medium**

#### 3.1 Property-Based Testing
```bash
pip install hypothesis[django]
```
- Edge case discovery for parameter validation
- Prompt processing robustness testing
- Unexpected input combination testing

#### 3.2 Load Testing
```bash
pip install locust
```
- Worker system stress testing
- Concurrent order processing validation
- API endpoint performance under load

#### 3.3 Enhanced Test Organization
- Test tagging for better categorization
- Snapshot testing for UI components
- Contract testing for external APIs

## Testing Guidelines

### Test Structure Standards

#### File Organization
- **Main test file**: `main/tests.py` for core functionality
- **Specialized files**: `test_[feature].py` for specific features
- **Naming convention**: Clear, descriptive test method names
- **Documentation**: Docstrings explaining test purpose

#### Test Class Organization
```python
class ModelTestCase(TestCase):
    """Test core model functionality and relationships."""
    
    def setUp(self):
        # Minimal, focused test data setup
        self.workers_to_cleanup = []  # Track resources for cleanup
        self.created_files = []
        pass
    
    def tearDown(self):
        # Explicit cleanup of files, workers, etc.
        for worker in self.workers_to_cleanup:
            try:
                if hasattr(worker, 'graceful_exit'):
                    worker.graceful_exit("Test cleanup")
            except Exception:
                pass
        
        # Clean up any Worker model instances
        Worker.objects.all().delete()
        
        super().tearDown()
    
    def test_specific_behavior(self):
        """Test one specific behavior with clear assertions."""
        pass
```

#### Resource Management Guidelines
- **Worker Cleanup**: Always add SmartWorker instances to `self.workers_to_cleanup`
- **File Cleanup**: Use temporary directories from test_settings.py
- **Dynamic PIDs**: Use `get_test_pid()` instead of hardcoded values
- **Database Cleanup**: Use `Worker.objects.all().delete()` in tearDown
- **Error Handling**: Wrap cleanup in try/except to prevent test failures

### Mock and Isolation Standards

#### External Service Mocking
```python
@patch('fal_client.submit')
@patch('httpx.Client.get')
def test_image_generation(self, mock_get, mock_submit):
    """Always mock external API calls for isolation."""
    mock_submit.return_value = Mock(get=lambda: {'images': [...]})
    # Test implementation
```

#### Database Isolation
- Use Django's `TestCase` for automatic transaction rollback
- In-memory SQLite for fast execution
- No shared state between test methods

#### File System Isolation
```python
@override_settings(MEDIA_ROOT=tempfile.mkdtemp())
def test_file_operations(self):
    """Use temporary directories for file operations."""
    # Test implementation
```

### Performance Testing Standards

#### Load Testing Scenarios
1. **Concurrent Orders**: 10+ simultaneous order submissions
2. **Batch Processing**: Large quantity orders (50+ items)
3. **Worker Scaling**: Multiple workers processing orders
4. **API Stress**: High-frequency API requests

#### Performance Benchmarks
- Order processing: <2 seconds per item
- API response time: <200ms for standard requests
- Database queries: <10 queries per request
- Memory usage: <500MB for batch operations

### Security Testing Requirements

#### Input Validation
- Parameter injection attack prevention
- SQL injection protection
- Cross-site scripting (XSS) prevention
- File upload validation

#### Authentication & Authorization
- Proper session management
- API key protection
- Access control validation
- Safety checker enforcement

## Continuous Integration

Art Factory uses GitHub Actions for automated testing, quality assurance, and deployment. The CI/CD pipeline ensures code quality and prevents regressions.

### GitHub Actions Workflow

The CI pipeline runs on every push and pull request with the following jobs:

#### 1. Test Job
- **Multi-Python Testing**: Tests against Python 3.11 and 3.12
- **Django System Check**: Validates Django configuration
- **Migration Check**: Ensures migrations are valid
- **Test Execution**: Runs full test suite with coverage
- **Coverage Reporting**: Uploads to Codecov with artifacts

#### 2. Lint Job
- **Syntax Check**: Critical error detection with flake8
- **Code Formatting**: Black formatting validation
- **Import Sorting**: isort validation

#### 3. Security Job
- **Dependency Scanning**: Safety check for known vulnerabilities
- **Static Analysis**: Bandit security scan

#### 4. Performance Job
- **Execution Time**: Ensures test suite completes in <2 minutes
- **Performance Benchmarking**: Tracks execution time trends

### Quality Gates

#### Coverage Requirements
- **Current Target**: 45% line coverage (gradual improvement)
- **Long-term Goal**: 90% line coverage
- **Patch Coverage**: 60% for new code
- **Reporting**: Codecov integration with PR comments

#### Performance Standards
- **Test Suite**: Maximum 2 minutes execution time
- **Individual Tests**: No single test over 30 seconds
- **Memory Usage**: Maximum 500MB for batch operations

#### Security Requirements
- **No Critical Vulnerabilities**: Safety check must pass
- **Static Analysis**: Bandit security scan must pass
- **Secret Detection**: No hardcoded secrets in codebase

### Configuration Files

#### `.github/workflows/django.yml`
Main CI workflow with comprehensive testing, linting, and security checks.

#### `.flake8`
```ini
[flake8]
max-line-length = 127
max-complexity = 10
exclude = venv, __pycache__, .git, htmlcov, logs, migrations, .github
ignore = E203, W503, E501
```

#### `pyproject.toml`
```toml
[tool.black]
line-length = 127
target-version = ['py311', 'py312']

[tool.isort]
profile = "black"
multi_line_output = 3
line_length = 127
```

#### `.codecov.yml`
```yaml
coverage:
  status:
    project:
      default:
        target: 45%
        threshold: 2%
    patch:
      default:
        target: 60%
        threshold: 5%
```

### Local Development Workflow

#### Pre-commit Checks
Before committing, run these commands locally:

```bash
# Run all tests with coverage
./run_tests.sh all --coverage

# Check code formatting
black --check .
isort --check-only .

# Run linting
flake8 .

# Security scan
safety check
bandit -r . -x venv/,htmlcov/,logs/
```

#### Setting Up Pre-commit Hooks
```bash
# Install development dependencies
pip install -r requirements.txt

# Run formatting tools
black .
isort .

# Verify all checks pass
./run_tests.sh all --coverage
flake8 .
```

### CI/CD Best Practices

#### Branch Protection
- **Required Status Checks**: All CI jobs must pass
- **Coverage Requirements**: Must meet coverage thresholds
- **Review Requirements**: Pull requests require review
- **Up-to-date Branches**: Must be current with target branch

#### Artifact Management
- **Coverage Reports**: HTML reports uploaded for failed builds
- **Test Logs**: Available for debugging test failures
- **Performance Metrics**: Execution time tracking

#### Deployment Pipeline
- **Staging**: Automatic deployment to staging on main branch
- **Production**: Manual deployment after review
- **Rollback**: Automated rollback on failure detection

### Monitoring and Alerts

#### Codecov Integration
- **PR Comments**: Coverage reports in pull requests
- **Status Badges**: Real-time coverage display in README
- **Trend Analysis**: Coverage changes over time

#### Performance Monitoring
- **Execution Time**: Test suite performance tracking
- **Memory Usage**: Resource consumption monitoring
- **Failure Analysis**: Automatic failure classification

### Troubleshooting CI Issues

#### Common Failures
1. **Test Failures**: Check test logs in artifacts
2. **Coverage Drop**: Review Codecov report for missing coverage
3. **Linting Issues**: Run flake8 locally to identify problems
4. **Security Alerts**: Check Safety/Bandit reports

#### Debug Commands
```bash
# Local test debugging
./run_tests.sh all --verbosity=2

# Coverage analysis
coverage run --rcfile=.coveragerc manage.py test --settings=ai_art_factory.test_settings
coverage report --show-missing
coverage html

# Performance profiling
time ./run_tests.sh all
```

## Test Organization Best Practices

### Naming Conventions
- **test_*.py**: Files containing Django test cases
- **Test case naming**: Descriptive names indicating the component being tested
- **Test method naming**: `test_<specific_behavior>` pattern

### File Organization Principles
1. **Keep related tests together**: UI tests, worker tests, etc. in separate files
2. **Use descriptive file names**: `test_bootstrap_integration.py` vs `test_ui.py`
3. **Follow Django conventions**: All test files in the main app directory
4. **Separate test categories**: Unit tests focus on single components, integration tests on component interaction

### Test File Management
- **Temporary files**: Automatically ignored via .gitignore patterns
- **Log files**: Test execution logs are temporary and not committed
- **Import consistency**: All test files use absolute imports (`from main.models import ...`)

## Template Testing Framework

Art Factory includes a comprehensive template testing framework that validates template inheritance, component usage, accessibility, security, and consistency across the application.

### Template Test Organization

The template testing framework consists of three main modules:

1. **test_template_framework.py**: Core template testing functionality
   - Template inheritance validation
   - Component consistency checks
   - Rendering tests with various contexts
   - Accessibility compliance
   - Security best practices
   - Component documentation validation

2. **test_template_validation.py**: Template syntax and structure validation
   - Django template syntax validation
   - Block and tag matching
   - Template consistency across similar pages
   - Static file and URL reference validation
   - Performance considerations
   - Template maintenance checks

3. **test_template_suite.py**: Comprehensive test runner and reporting
   - Categorized test execution
   - Detailed reporting with success metrics
   - Command-line interface for selective testing
   - Django management command integration

### Running Template Tests

```bash
# Run all template tests via Django
python manage.py test main.tests.test_template_framework --settings=ai_art_factory.test_settings
python manage.py test main.tests.test_template_validation --settings=ai_art_factory.test_settings

# Run template test suite with detailed reporting
python main/tests/test_template_suite.py

# Run specific template test categories
python main/tests/test_template_suite.py --category framework
python main/tests/test_template_suite.py --category validation

# Run with custom verbosity
python main/tests/test_template_suite.py --verbosity 1
```

### Template Testing Categories

#### 1. Inheritance Tests
- Validates proper template inheritance chain (base.html → layouts → pages)
- Ensures required blocks are preserved
- Checks for proper block.super usage
- Validates layout selection consistency

#### 2. Component Tests
- Ensures all templates use standardized components
- Validates component parameter usage
- Checks JavaScript component loading order
- Tests component error handling

#### 3. Accessibility Tests
- Validates ARIA labels and attributes
- Ensures form labels are properly associated
- Checks alt attributes for images
- Tests keyboard navigation support

#### 4. Security Tests
- Validates CSRF token inclusion in forms
- Checks for unsafe inline JavaScript
- Tests proper escaping of user data
- Validates authentication requirements

#### 5. Performance Tests
- Identifies excessive template includes
- Detects deep HTML nesting
- Checks for render performance issues
- Validates caching opportunities

#### 6. Documentation Tests
- Ensures all components are documented
- Validates parameter documentation completeness
- Checks for usage examples
- Tests documentation accuracy

### Template Best Practices Enforced

1. **Consistent Layout Usage**: Similar pages must use the same layout
2. **Component Reuse**: Common UI patterns must use shared components
3. **Proper Inheritance**: Templates must follow the established hierarchy
4. **Security First**: All forms must include CSRF tokens
5. **Accessibility**: All interactive elements must be keyboard accessible
6. **Performance**: Avoid excessive nesting and includes

### Template Testing Output

The template test suite provides detailed reporting:

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

## Test Execution

### Local Development
```bash
# Full test suite
./run_tests.sh all

# Quick tests (excluding integration)
./run_tests.sh quick

# Specific test categories
./run_tests.sh models
./run_tests.sh views
./run_tests.sh integration

# Template tests
python manage.py test main.tests.test_template_framework --settings=ai_art_factory.test_settings
python manage.py test main.tests.test_template_validation --settings=ai_art_factory.test_settings

# Coverage testing (recommended)
./run_tests.sh coverage           # Run all tests with coverage
./run_tests.sh models --coverage  # Run specific tests with coverage
./run_tests.sh all --coverage     # Run all tests with coverage

# Manual coverage commands
coverage run manage.py test --settings=ai_art_factory.test_settings
coverage report --show-missing
coverage html
```

### Test Categories
- **quick**: Models, views, signals (fast feedback)
- **models**: Django model tests
- **views**: Web view and API tests
- **signals**: Django signal tests
- **tasks**: Background task tests
- **commands**: Management command tests
- **integration**: End-to-end workflow tests
- **batch**: Batch generation tests

## Coverage Reporting

### Overview
Art Factory uses coverage.py for comprehensive test coverage analysis. Coverage reporting helps identify untested code and maintain quality standards.

### Current Coverage Status
- **Baseline Coverage**: 14.71% (as of coverage implementation)
- **Target Coverage**: 90% line coverage, 85% branch coverage
- **Quality Threshold**: 90% required for CI/CD pass

### Coverage Configuration
Coverage is configured via `.coveragerc` with the following key settings:
- **Source**: All project files excluding migrations, tests, and vendor code
- **Reporting**: Shows missing line numbers and generates multiple formats
- **HTML Output**: Detailed reports in `htmlcov/` directory
- **XML Output**: CI/CD compatible format in `coverage.xml`

### Running Coverage
```bash
# Recommended: Use test runner with coverage
./run_tests.sh coverage                 # Full suite with coverage
./run_tests.sh models --coverage        # Specific test with coverage

# Direct coverage commands
coverage run manage.py test --settings=ai_art_factory.test_settings
coverage report --show-missing          # Terminal report
coverage html                          # HTML report (htmlcov/index.html)
coverage xml                           # XML report (coverage.xml)

# Coverage validation
coverage report --fail-under=90        # Check if coverage meets threshold
```

### Coverage Reports
1. **Terminal Report**: Quick summary with missing line numbers
2. **HTML Report**: Interactive browsable report at `htmlcov/index.html`
3. **XML Report**: Machine-readable format for CI/CD integration

### Coverage Analysis Guidelines
- **Focus Areas**: Prioritize coverage for core business logic and models
- **Exclude**: Don't worry about 100% coverage for Django admin, migrations, or settings
- **Critical Paths**: Ensure all API endpoints and worker processes have coverage
- **Edge Cases**: Use coverage gaps to identify missing test scenarios

### Current Coverage Gaps
Based on baseline analysis, the following areas need attention:
- **Views** (11.33%): API endpoints and UI views need comprehensive testing
- **Workers** (0%): Background worker system needs test coverage
- **Tasks** (0%): Async task processing needs testing
- **Management Commands** (0%): CLI commands need validation testing
- **Factory Machines** (0%): Core production logic needs coverage

### Coverage Improvement Strategy
1. **Phase 1**: Focus on models and core business logic (target 60%)
2. **Phase 2**: Add view and API endpoint coverage (target 75%)
3. **Phase 3**: Comprehensive worker and task coverage (target 90%)

## Dependencies and Requirements

### Core Testing Dependencies
```txt
# Current (Django built-in + coverage)
django>=5.1
coverage==7.6.9

# Phase 1 Complete
# ✅ Coverage reporting implemented

# Phase 2 Additions
factory-boy==3.3.1
django-silk==5.1.0

# Phase 3 Additions
hypothesis[django]==6.108.5
locust==2.29.1
```

### Optional Enhancements
```txt
# If pytest migration considered
pytest==8.3.2
pytest-django==4.8.0
pytest-cov==5.0.0

# Advanced testing
mutmut==2.4.3  # Mutation testing
```

## Maintenance and Evolution

### Regular Reviews
- **Monthly**: Test coverage analysis and gap identification
- **Quarterly**: Performance benchmark review
- **Per Release**: Security test validation
- **Annual**: Testing strategy and technology evaluation

### Metrics Tracking
- Test execution time trends
- Coverage percentage over time
- Flaky test incidents
- Security test effectiveness

### Technology Evaluation
The project maintains a Django-first philosophy while selectively adopting complementary testing technologies that enhance rather than replace Django's strengths. All additions must align with Django conventions and project maintainability goals.

---

This testing strategy ensures sustainable development velocity through comprehensive automation while maintaining code quality and preventing regressions as the Art Factory platform evolves.