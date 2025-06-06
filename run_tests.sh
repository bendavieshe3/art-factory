#!/bin/bash

# Art Factory Test Runner
# Runs comprehensive test suite with proper environment setup and coverage

set -e  # Exit on any error

echo "🧪 Art Factory Test Suite"
echo "========================="

# Parse coverage option
COVERAGE_MODE="off"
if [[ "$*" == *"--coverage"* ]]; then
    COVERAGE_MODE="on"
    # Remove --coverage from arguments
    set -- "${@/--coverage/}"
fi

# Check if virtual environment is activated
if [[ "$VIRTUAL_ENV" == "" ]]; then
    echo "⚠️  Virtual environment not activated. Activating venv..."
    source venv/bin/activate
fi

# Check if Django is installed
if ! python -c "import django" 2>/dev/null; then
    echo "❌ Django not found. Please install dependencies first:"
    echo "   pip install -r requirements.txt"
    exit 1
fi

# Check if coverage is installed when needed
if [[ "$COVERAGE_MODE" == "on" ]] && ! python -c "import coverage" 2>/dev/null; then
    echo "❌ Coverage not found. Installing coverage..."
    pip install coverage==7.6.9
fi

echo "✅ Environment ready"
if [[ "$COVERAGE_MODE" == "on" ]]; then
    echo "📊 Coverage collection enabled"
fi
echo ""

# Function to run tests with or without coverage
run_test_command() {
    local test_paths="$1"
    local verbosity="${2:-1}"
    
    if [[ "$COVERAGE_MODE" == "on" ]]; then
        coverage run --append manage.py test $test_paths --settings=ai_art_factory.test_settings -v "$verbosity"
    else
        python manage.py test $test_paths --settings=ai_art_factory.test_settings -v "$verbosity"
    fi
}

# Initialize coverage if enabled
if [[ "$COVERAGE_MODE" == "on" ]]; then
    echo "🧹 Cleaning previous coverage data..."
    coverage erase
fi

# Run different test suites based on argument
case "${1:-all}" in
    "quick")
        echo "🏃 Running quick tests (excluding integration)..."
        run_test_command "main.tests.ModelTestCase main.tests.ViewTestCase main.tests.SignalTestCase" 1
        ;;
    "models")
        echo "🏗️  Running model tests..."
        run_test_command "main.tests.ModelTestCase" 2
        ;;
    "views")
        echo "🌐 Running view tests..."
        run_test_command "main.tests.ViewTestCase" 2
        ;;
    "signals")
        echo "📡 Running signal tests..."
        run_test_command "main.tests.SignalTestCase" 2
        ;;
    "tasks")
        echo "⚙️  Running task tests..."
        run_test_command "main.tests.TaskTestCase" 2
        ;;
    "commands")
        echo "🔧 Running management command tests..."
        run_test_command "main.tests.ManagementCommandTestCase" 2
        ;;
    "integration")
        echo "🔄 Running integration tests..."
        run_test_command "main.tests.IntegrationTestCase" 2
        ;;
    "batch")
        echo "🎯 Running batch generation tests..."
        run_test_command "main.tests.BatchGenerationTestCase" 2
        ;;
    "all")
        echo "🚀 Running full test suite..."
        run_test_command "main" 1
        ;;
    "coverage")
        echo "📊 Running coverage-only tests..."
        COVERAGE_MODE="on"
        run_test_command "main" 1
        ;;
    *)
        echo "Usage: $0 [quick|models|views|signals|tasks|commands|integration|batch|all|coverage] [--coverage]"
        echo ""
        echo "Test suites:"
        echo "  quick       - Models, views, and signals (fast)"
        echo "  models      - Django model tests"
        echo "  views       - Web view and API tests"
        echo "  signals     - Django signal tests"
        echo "  tasks       - Background task tests"
        echo "  commands    - Management command tests"
        echo "  integration - End-to-end workflow tests"
        echo "  batch       - Batch generation tests"
        echo "  all         - Complete test suite (default)"
        echo "  coverage    - Run all tests with coverage enabled"
        echo ""
        echo "Options:"
        echo "  --coverage  - Enable coverage collection for any test suite"
        exit 1
        ;;
esac

echo ""
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
    
    # Generate coverage reports if coverage was enabled
    if [[ "$COVERAGE_MODE" == "on" ]]; then
        echo ""
        echo "📊 Generating coverage reports..."
        
        # Terminal report
        echo "📋 Coverage Summary:"
        coverage report --show-missing
        
        # HTML report
        echo ""
        echo "🌐 Generating HTML coverage report..."
        coverage html
        echo "✅ HTML report generated in htmlcov/index.html"
        
        # XML report for CI/CD
        coverage xml
        echo "✅ XML report generated in coverage.xml"
        
        # Check coverage threshold
        echo ""
        echo "🎯 Coverage threshold check:"
        if coverage report --fail-under=90 > /dev/null 2>&1; then
            echo "✅ Coverage meets 90% threshold"
        else
            echo "⚠️  Coverage below 90% threshold"
            coverage report --fail-under=90
        fi
    fi
else
    echo "❌ Some tests failed"
    exit 1
fi