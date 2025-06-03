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
- **CSS Framework**: Bootstrap 5 with django-bootstrap5 package
- **Frontend Approach**: Django templates + JavaScript with Bootstrap components

### To Be Determined
- **Real-time Communication**: Options include Django Channels (WebSockets), Server-Sent Events, or polling
- **Background Tasks**: Options include Celery, Django-RQ, or Django's async views
- **Task Queue Backend**: Redis, PostgreSQL, or in-memory for development

### CSS Framework Decision (Bootstrap 5)

**Rationale**: Bootstrap 5 was chosen based on three key criteria:
1. **Understandability/Simplicity**: Clear, semantic class names that translate well from user instructions
2. **UI Widget Availability**: Comprehensive component library (cards, modals, forms, navigation)
3. **Dense Desktop Interface Support**: Excellent for compact, desktop-like applications

**Implementation Notes**:
- Use `django-bootstrap5` package for form integration
- Preserve custom components (like toast notifications) when Bootstrap alternatives are inferior
- Leverage Bootstrap's responsive grid system and utility classes
- Follow Bootstrap's semantic HTML patterns for accessibility

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
pip install fal-client      # AI provider client
pip install replicate       # Replicate API client
pip install python-decouple # .env file support
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
# In Terminal 2 - Set up API keys
cp .env.example .env
# Edit .env file with your actual API keys from:
# - fal.ai: https://fal.ai/dashboard/keys  
# - Replicate: https://replicate.com/account/api-tokens
# - CivitAI: https://civitai.com/user/account (optional)

# Create admin user
python manage.py createsuperuser
# Recommended: username=admin, email=admin@example.com, password=admin123

# Load factory machine seed data
python manage.py load_seed_data
```

### Development Cycle
1. Make code changes (models, views, templates)
2. Run migrations if models changed: `python manage.py makemigrations && python manage.py migrate`
3. Django auto-reloads development server
4. Refresh browser to test changes
5. Run tests: `python manage.py test`
6. Commit when feature works: `git add . && git commit -m "description"`

### AI Generation Workflow
1. **Place Orders**: Use web interface at http://127.0.0.1:8000/ to create orders
2. **Automatic Processing**: AI generation starts immediately in the background
3. **View Results**: Check inventory at http://127.0.0.1:8000/inventory/ for generated images  
4. **Monitor Status**: Orders automatically update from "pending" → "processing" → "completed"

**Note**: Generation happens automatically when orders are placed. No manual commands needed!

### NSFW Safety Checkers
All AI models have NSFW safety checkers **disabled by default** to prevent false positives that result in blank/black images. Safety checkers often incorrectly flag innocent content as inappropriate, leading to censored outputs. If you need safety checking enabled, you can add `"enable_safety_checker": true` to the parameters when placing an order.

## Known Issues & Bugs

### Critical Bugs
- **Non-SDXL Model Orders Failing**: Orders for non-SDXL models (like Flux models) are currently broken, likely due to parameter mismatch between model types. Different model architectures expect different parameter schemas and defaults.

### Technical Debt
- **Provider-Based Product Storage**: Current product storage by provider is not scalable. Need combined product storage system.
- **Missing Model-Specific Defaults**: Parameter defaults are generic rather than model-specific, causing compatibility issues with different model architectures.

### Enhancement Backlog
- Real-time order progress feedback
- Inventory interface optimization (compact cards, sidebar details)
- Model catalog expansion with favorites management
- Order page layout improvements

## Development Commands

**Note:** Always activate the virtual environment before running Django commands.

```bash
# Activate virtual environment first
source venv/bin/activate

# Development server
python manage.py runserver

# Testing
python manage.py test                    # Run all tests
python manage.py test main.tests         # Run app-specific tests  
python manage.py test main.tests.ModelTestCase  # Run specific test class
python manage.py test -v 2               # Verbose test output
python manage.py test --keepdb           # Reuse test database (faster)

# Database operations
python manage.py makemigrations
python manage.py migrate

# Administrative
python manage.py createsuperuser
python manage.py shell
python manage.py collectstatic

# Data management
python manage.py load_seed_data          # Load factory machine definitions

# Worker system (autonomous processing)
python manage.py worker_status           # Show current worker and queue status
python manage.py run_worker              # Manually run a single worker (debugging)
python manage.py run_foreman             # Manually run foreman process (debugging)

# Legacy order processing (for emergencies)
python manage.py process_pending_orders  # Retry stuck/pending orders
python manage.py process_pending_orders --retry-failed  # Also retry failed orders
python manage.py monitor_orders          # Show current order processing status
python manage.py simple_process          # Process pending orders manually (legacy)

# Debugging and monitoring  
python manage.py debug_orders            # Show recent order status and failures
python manage.py debug_orders --order-id 123  # Debug specific order
python manage.py debug_orders --failed-only    # Show only failed orders

# Development utilities
pip freeze > requirements.txt           # Update requirements file

# Load seed data (reset existing)
python manage.py load_seed_data --reset

# Process pending AI generation orders (manual/debugging only)
python manage.py simple_process

# Process specific order item (manual/debugging only) 
python manage.py simple_process --order-item-id 1
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
- Always commit tested work locally to git
- Check into source code locally before pushing to remote repositories

## Project Management & Issue Handling

### GitHub Issues Workflow

**CRITICAL**: Use todowriter to plan our sessions, but refer to and update Github issues as we progress. Close and reference Github issues using references in commit messages that are pushed to the remote repository where possible. Don't push to the remote repository with the user's permission.

**When to Use GitHub Issues vs TodoWrite**:
- **GitHub Issues**: ALL project development tasks, bugs, enhancements, features
- **TodoWrite Tool**: ONLY for conversation-specific ephemeral tasks (e.g., "read these 3 files", "check this function")

**Issue Creation Process**:
1. **Check existing issues** before creating duplicates: `gh issue list`
2. **Review milestones** to understand project priorities: `gh issue list --milestone "v0.1 MVP"`
3. **Use appropriate templates** (.github/ISSUE_TEMPLATE/) for consistency
4. **Apply correct labels** for priority, type, and component
5. **ALWAYS reference milestone** (v0.1 MVP, v0.2 Polish, etc.) when creating issues

## (Rest of the file remains unchanged)