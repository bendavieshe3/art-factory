#!/bin/bash

# Art Factory Test Runner
# Runs comprehensive test suite with proper environment setup

set -e  # Exit on any error

echo "🧪 Art Factory Test Suite"
echo "========================="

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

echo "✅ Environment ready"
echo ""

# Run different test suites based on argument
case "${1:-all}" in
    "quick")
        echo "🏃 Running quick tests (excluding integration)..."
        python manage.py test main.tests.ModelTestCase main.tests.ViewTestCase main.tests.SignalTestCase --settings=ai_art_factory.test_settings -v 1
        ;;
    "models")
        echo "🏗️  Running model tests..."
        python manage.py test main.tests.ModelTestCase --settings=ai_art_factory.test_settings -v 2
        ;;
    "views")
        echo "🌐 Running view tests..."
        python manage.py test main.tests.ViewTestCase --settings=ai_art_factory.test_settings -v 2
        ;;
    "signals")
        echo "📡 Running signal tests..."
        python manage.py test main.tests.SignalTestCase --settings=ai_art_factory.test_settings -v 2
        ;;
    "tasks")
        echo "⚙️  Running task tests..."
        python manage.py test main.tests.TaskTestCase --settings=ai_art_factory.test_settings -v 2
        ;;
    "commands")
        echo "🔧 Running management command tests..."
        python manage.py test main.tests.ManagementCommandTestCase --settings=ai_art_factory.test_settings -v 2
        ;;
    "integration")
        echo "🔄 Running integration tests..."
        python manage.py test main.tests.IntegrationTestCase --settings=ai_art_factory.test_settings -v 2
        ;;
    "batch")
        echo "🎯 Running batch generation tests..."
        python manage.py test main.tests.BatchGenerationTestCase --settings=ai_art_factory.test_settings -v 2
        ;;
    "all")
        echo "🚀 Running full test suite..."
        python manage.py test main.tests --settings=ai_art_factory.test_settings -v 1
        ;;
    *)
        echo "Usage: $0 [quick|models|views|signals|tasks|commands|integration|batch|all]"
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
        exit 1
        ;;
esac

echo ""
if [ $? -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed"
    exit 1
fi