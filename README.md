# Art Factory

A Django-first web application for managing AI-generated art using multiple providers like fal.ai, Replicate, and civitai.

## Project Status

🏗️ **Currently in development** - Starting fresh with a Django-first architecture based on comprehensive documentation.

## Documentation

- [Vision & Purpose](docs/vision.md) - Project goals and value proposition
- [Domain Concepts](docs/concepts.md) - Core business model and entities  
- [Features](docs/features.md) - Functional requirements and development phases
- [User Experience](docs/ux.md) - Interface requirements and interaction patterns
- [Technical Requirements](docs/requirements.md) - Architecture and deployment constraints
- [Technical Design](docs/design.md) - Detailed implementation architecture

## Prerequisites

- Python 3.9+
- Django 5.1+
- Internet connection for AI provider APIs

## Quick Start

*Coming soon - Django project setup in progress*

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run Django setup
python manage.py migrate
python manage.py runserver
```

## Development

This project follows Django-first principles:
- Leverage Django's built-in features and conventions
- Start simple, add complexity only when needed
- Use Django admin for debugging and data management
- Fat models with business logic close to data

## Architecture

Art Factory uses a factory abstraction pattern with these core entities:
- **Products**: Generated media files (images, videos, audio) with metadata
- **Orders**: User requests containing parameters and production specifications
- **Factory Machines**: Provider-specific implementations for generating products
- **Providers**: External AI services (fal.ai, Replicate, civitai)
- **Projects**: Organization mechanism for related work

## License

*To be determined*

## Legacy Implementation

The previous implementation is backed up in `art-factory-old/` for reference and asset extraction.