# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Art Factory is a Django-first web application for managing AI-generated art using various providers like fal.ai, Replicate, and civitai. The project commits to leveraging Django's mature ecosystem and established patterns to minimize architectural complexity and accelerate development.

## Documentation Structure

The project documentation is organized into focused files:

- **vision.md**: Project purpose, value proposition, and target user
- **concepts.md**: Core domain model and business concepts
- **features.md**: Functional requirements and implementation phases
- **ux.md**: User interface requirements and interaction patterns
- **requirements.md**: Technical requirements and deployment constraints
- **design.md**: Detailed technical architecture (implementation-specific)

## Architecture

### Core Domain Concepts

The application follows a factory abstraction pattern:

- **Products**: Generated media files (images, videos, audio) with metadata
- **Orders**: User requests containing base parameters and production line specification
- **Order Items**: Individual product creation tasks derived from orders
- **Factory Machines**: Provider-specific implementations for generating products
- **Providers**: External AI services (fal.ai, Replicate, civitai)
- **Parameter Sets**: Flexible JSON-based parameter handling for different models

### Component Hierarchy

**Product Factory Inheritance:**
- BaseProductFactory (common validation/infrastructure)
- ProviderProductFactory (provider-specific setup)
- ModelModalityProductFactory (modality-specific logic)
- ModelSpecificFactory (model-specific parameters)

### Key Features

- Smart parameter expansion with token interpolation
- Real-time updates (implementation approach TBD)
- Template and favorites system
- Project organization and management
- Background task processing for production workflows

## Technology Stack

### Core (Committed)
- **Backend Framework**: Django 5.1+
- **Database**: SQLite (development) → PostgreSQL (production migration path)
- **ORM**: Django ORM (built-in)
- **Development Server**: Django's built-in development server

### To Be Determined
- **Real-time Communication**: Options include Django Channels (WebSockets), Server-Sent Events, or polling
- **Background Tasks**: Options include Celery, Django-RQ, or Django's async views
- **Frontend Approach**: Django templates + JavaScript vs. more sophisticated SPA approach
- **CSS Framework**: Tailwind, Bootstrap, or custom CSS
- **Task Queue Backend**: Redis, PostgreSQL, or in-memory for development

## Development Environment Setup

### Virtual Environment
The project uses Python's built-in venv for dependency isolation:

```bash
# Create virtual environment (one time setup)
python3 -m venv venv

# Activate virtual environment (each session)
source venv/bin/activate

# Deactivate when done
deactivate
```

### Dependencies
```bash
# Install Django and project dependencies
pip install django
pip install fal-client  # AI provider client
```

## Development Workflow

### Terminal Setup
Use **two terminal windows/tabs** for efficient development:

**Terminal 1 - Development Server:**
```bash
cd /Volumes/Ceres/data/Projects/art-factory
source venv/bin/activate
python manage.py runserver
# Keep this running - Django auto-reloads on file changes
```

**Terminal 2 - Development Commands:**
```bash
cd /Volumes/Ceres/data/Projects/art-factory
source venv/bin/activate
# Use for migrations, testing, git commands, etc.
```

### Browser Setup
Keep these browser windows open during development:
- **Main Application**: http://127.0.0.1:8000/
- **Admin Portal**: http://127.0.0.1:8000/admin/
- **Auto-refresh** both when making changes

### Initial Setup (One-time)
```bash
# In Terminal 2 - Create admin user
python manage.py createsuperuser
# Recommended: username=admin, email=admin@example.com, password=admin123
```

### Development Cycle
1. Make code changes (models, views, templates)
2. Run migrations if models changed: `python manage.py makemigrations && python manage.py migrate`
3. Django auto-reloads development server
4. Refresh browser to test changes
5. Run tests: `python manage.py test`
6. Commit when feature works: `git add . && git commit -m "description"`

## Development Commands

**Note:** Always activate the virtual environment before running Django commands.

```bash
# Activate virtual environment first
source venv/bin/activate

# Development server
python manage.py runserver

# Database operations
python manage.py makemigrations
python manage.py migrate

# Testing
python manage.py test

# Administrative
python manage.py createsuperuser
python manage.py shell
python manage.py collectstatic

# Create requirements file
pip freeze > requirements.txt
```

## Code Organization Patterns

### Models
- Organized as package under `main/models/`
- Separate files for related model groups
- Fat models approach with business logic in model classes

### Views
- Split by section: `[section]_views.py`
- API views separated from template views
- Choose between Django's function-based views or class-based views based on complexity

### Templates
- Base template with section-specific extensions
- Partial templates for reusable components
- Leverage Django's template inheritance and inclusion patterns

### URLs
- Complete pages: `/<section>/`
- HTML partials: `/partials/<resource>/<action>/`
- JSON API: `/api/<resource>/`
- Resource pages: `/<resource>/<id>/`

### Real-time Updates (Architecture TBD)
- Consider Django signals for internal events
- Evaluate Django Channels for WebSocket communication
- Alternative: Server-Sent Events or AJAX polling
- Event naming convention: `(entity)_(verb)` pattern

## Implementation Guidelines

### Parameter Handling
- Use JSON fields for flexible parameter storage
- Validate parameters against ParameterSpec definitions
- Support interpolation and expansion for smart tokens

### Frontend Approach (TBD)
- Option 1: Django templates + minimal JavaScript
- Option 2: Django + modern JavaScript components
- Option 3: Django API + SPA frontend
- Prefer server-side rendering with progressive enhancement

### Database Design
- All models include standard Django fields (id, created/modified timestamps)
- Use Django's JSONField for flexible parameter storage
- Fat models approach with business logic in model classes
- Leverage Django ORM's relationship management

### Error Handling
- Use Django's built-in logging framework
- Leverage Django's exception handling and error pages
- Consider custom error views for user-friendly messages

## Development Principles

### Django-First Approach
- Leverage Django's conventions and built-in features
- Prefer Django ecosystem solutions over external alternatives
- Start simple, add complexity only when needed
- Use Django admin for debugging and data management

### Architecture Guidelines
- Fat models with business logic close to data
- Backwards compatibility not prioritized (favor removing legacy code)
- Choose established patterns over novel approaches
- Minimize non-obvious technical decisions
- Preserve domain concepts while being flexible on implementation

### Documentation-Driven Development
- Well-organized, focused documentation in separate concerns
- Clear separation between vision, domain concepts, features, and technical requirements
- Avoid premature technical specification
- Progressive refinement based on actual implementation needs

### Performance Strategy
- Database optimization using Django ORM best practices
- Efficient file handling for generated media
- Caching strategy using Django's cache framework

## Development Workflow Guidelines

- Always verify accomplishments with tests
- Update documentation to reflect changes
- Check into source code locally before pushing to remote repositories

## Local Knowledge Management

@./.claude/kb/MOC.md

For each request, use the Map of Content (MOC) to identify relevant knowledge articles that may inform your response. Read knowledge related to the current request based on the user command and project context. This knowledge base contains environment-specific information, best practices, and current technical information to supplement your responses without requiring web searches.