# Art Factory

[![CI](https://github.com/bendavieshe3/art-factory/actions/workflows/django.yml/badge.svg)](https://github.com/bendavieshe3/art-factory/actions/workflows/django.yml)
[![codecov](https://codecov.io/gh/bendavieshe3/art-factory/branch/main/graph/badge.svg)](https://codecov.io/gh/bendavieshe3/art-factory)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Django 5.2+](https://img.shields.io/badge/django-5.2+-green.svg)](https://www.djangoproject.com/)
[![License](https://img.shields.io/badge/license-TBD-lightgrey.svg)](LICENSE)

A Django-first web application for managing AI-generated art using multiple providers like fal.ai, Replicate, and civitai.

## Project Status

✅ **v0.1 MVP Released** - Core image generation functionality with comprehensive error handling and batch processing.

## Documentation

- [Vision & Purpose](docs/vision.md) - Project goals and value proposition
- [Domain Concepts](docs/concepts.md) - Core business model and entities  
- [Features](docs/features.md) - Functional requirements and development phases
- [User Experience](docs/ux.md) - Interface requirements and interaction patterns
- [Technical Requirements](docs/requirements.md) - Architecture and deployment constraints
- [Technical Design](docs/design.md) - Detailed implementation architecture

## Features

### Core Functionality
- **AI Image Generation**: Create images using fal.ai and Replicate models (FLUX, SDXL, and more)
- **Batch Processing**: Generate multiple images efficiently with provider batch capabilities
- **Model-Specific Parameters**: Dynamic forms that adapt to each AI model's requirements
- **Order Management**: Track generation requests with real-time status updates
- **Inventory Management**: Download, view, and delete generated images with bulk operations

### User Experience
- **Responsive Design**: Bootstrap 5-based UI that works on desktop and mobile
- **Real-time Notifications**: Toast notifications and status updates for operations
- **Preview System**: Live updates of generated images with metadata
- **Error Handling**: User-friendly error messages with automatic retry capabilities

### Technical Features
- **Provider Flexibility**: Easy integration with multiple AI providers
- **Background Processing**: Worker-based system for handling generation tasks
- **Comprehensive Logging**: Detailed logging for debugging and monitoring
- **Test Coverage**: 44% test coverage with comprehensive error scenario testing

## Prerequisites

- Python 3.11+
- Django 5.2+
- Internet connection for AI provider APIs
- fal.ai and/or Replicate API keys

## Quick Start

### Installation

1. **Clone and setup environment**:
```bash
git clone https://github.com/bendavieshe3/art-factory.git
cd art-factory

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

2. **Configure environment variables**:
Create a `.env` file in the project root with your API keys:
```bash
# Required for fal.ai provider
FAL_API_KEY=your_fal_api_key_here

# Required for Replicate provider  
REPLICATE_API_TOKEN=your_replicate_token_here

# Django settings
SECRET_KEY=your_secret_key_here
DEBUG=True
```

3. **Setup database and run**:
```bash
# Run database migrations
python manage.py migrate

# Load sample factory machine definitions
python manage.py load_seed_data

# Start the development server
python manage.py runserver
```

4. **Access the application**:
- Open http://127.0.0.1:8000 in your browser
- Navigate to "Production" to create your first image generation order
- Monitor progress in "Orders" and view results in "Inventory"

## Development

This project follows Django-first principles:
- Leverage Django's built-in features and conventions
- Start simple, add complexity only when needed
- Use Django admin for debugging and data management
- Fat models with business logic close to data

### Testing and Quality Assurance

Art Factory maintains high code quality through automated testing and continuous integration:

- **Comprehensive Test Suite**: 1550+ lines of tests covering models, views, APIs, and workflows
- **Coverage Reporting**: Target 90% code coverage with detailed reports
- **Multi-Python Testing**: Automated testing on Python 3.11 and 3.12
- **Code Quality**: Automated linting with flake8, formatting with black, and security scanning
- **Performance Monitoring**: Test suite performance benchmarking (<2 minutes target)

```bash
# Run tests locally
./run_tests.sh all

# Run tests with coverage
./run_tests.sh all --coverage

# Run specific test categories  
./run_tests.sh models
./run_tests.sh integration
```

### CI/CD Pipeline

Every push and pull request triggers automated:
- Multi-version Python testing (3.11, 3.12)
- Code quality checks (linting, formatting, security)
- Coverage analysis with quality gates
- Performance benchmarking
- Artifact generation for failed builds

## Architecture

Art Factory uses a factory abstraction pattern with these core entities:

### Core Models
- **Products**: Generated media files with metadata (dimensions, seeds, provider info)
- **Orders**: User requests containing base parameters and production line specification
- **Order Items**: Individual product creation tasks derived from orders (supports batch generation)
- **Factory Machine Definitions**: AI model configurations with parameter schemas and defaults
- **Workers**: Background processing system for handling generation tasks

### Key Components
- **Factory Machines**: Provider-specific implementations (SyncFalFactoryMachine, SyncReplicateFactoryMachine)
- **Error Handling**: Comprehensive error categorization with retry strategies and user-friendly messaging
- **Smart Workers**: Autonomous worker system with batch processing and graceful failure handling
- **Parameter Management**: Dynamic form generation based on model-specific schemas

## License

*To be determined*

## Legacy Implementation

The previous implementation is backed up in `art-factory-old/` for reference and asset extraction.