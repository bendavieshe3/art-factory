# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Art Factory is a Django-first web application for managing AI-generated art using various providers like fal.ai, Replicate, and civitai. The project commits to leveraging Django's mature ecosystem and established patterns to minimize architectural complexity and accelerate development.

## Session Start
@.claude/MOC.md

## Development Flow (Github Issue or Enchancement)
1. Check local repository for uncommited files - if any STOP
2. Read Github issue
3. Review design documents in ./docs
4. Review related source code
5. Check if the issue is unclear, or the design needs updating - if so STOP
6. Create a plan and present to the user for approval
7. Create tests for the requirement (should fail)
8. Implement all or a logical part of the change
9. Run tests for the change (should pass)
10. Commit changes locally (use issue #)
11. All issue requirements met? if not, revise and continue plan
12. Run all tests
13. Update documentation under ./docs
14. If all pass, push to remote repository
15. Suggest remaining work to be made into github issues

## Documentation Structure

The project documentation is organized into focused files:

- **vision.md**: Project purpose, value proposition, and target user
- **concepts.md**: Core domain model and business concepts
- **features.md**: Functional requirements and implementation phases
- **ux.md**: User interface requirements and interaction patterns
- **requirements.md**: Technical requirements and deployment constraints
- **design.md**: Detailed technical architecture (implementation-specific)
- **testing.md**: Testing strategy, standards, and implementation roadmap

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

## Coding Standards and CI Requirements

Based on our CI pipeline configuration (flake8, black, isort), follow these standards to minimize linting issues:

### Import Organization
- **Order**: stdlib → django → third-party → local imports
- **No wildcard imports** in application code (exception: `models/__init__.py` for Django models)
- **Remove unused imports** immediately
- **Module-level imports** must be at the top of the file (before any code)

### Code Formatting
- **Line length**: Maximum 127 characters (configured in pyproject.toml)
- **Use Black** for automatic formatting: `black .`
- **Arithmetic operators**: Always use spaces around operators (`i + 1`, not `i+1`)
- **F-strings**: Only use f-strings when actually interpolating variables (`f"Hello {name}"`, not `f"Hello"`)

### Code Quality
- **Cyclomatic complexity**: Keep functions under 10 (current limit allows up to ~12)
- **Unused variables**: Remove or prefix with `_` if intentionally unused
- **Test variables**: Document why variables are created but not used in tests

### Django-Specific
- **Settings imports**: Use specific imports, not `from django.conf import settings` unless needed
- **Model imports**: The `models.py` and `models/__init__.py` files use wildcard imports by design
- **Test settings**: `test_settings.py` imports from main settings with `from .settings import *`

### CI Pipeline Commands
```bash
# Before committing, run:
source venv/bin/activate
python -m black .                    # Auto-format code
python -m flake8                     # Check linting
python manage.py test --settings=ai_art_factory.test_settings  # Run tests
```

### Current Acceptable Violations
- **Wildcard imports (F403)**: Allowed in `models/__init__.py` and `test_settings.py`
- **Cyclomatic complexity**: 9 functions exceed limit but are tracked in Issue #55
- **Some test variables**: May be kept for test structure even if unused

## Memory Notes

- Always read ./.claude/kb/MOC.md at the start of each session to understand local knowledge
- The github remote repository is https://github.com/bendavieshe3/art-factory
- We are running in a virtual environment you need to activate first before running python code

## (Rest of the file remains unchanged)