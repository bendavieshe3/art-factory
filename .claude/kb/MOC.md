# Map of Content (MOC)

This file provides an overview of all knowledge base articles maintained by Claude Code's Local Knowledge Management system.

## Knowledge Base Structure

### Development Environment
- [Local System Information](./local-system-info.md) - macOS 15.5, Apple M4 Pro, Python 3.13.3 setup

### Programming Languages & Frameworks
- [Django Framework](./django.md) - Django 5.1/5.2 features, support timelines, upgrade recommendations
- [Django Channels](./django-channels.md) - WebSocket real-time functionality, ASGI architecture, best practices
- [Django Real-time Updates](./django-realtime-updates.md) - Polling vs WebSockets vs SSE, implementation patterns, best practices
- [Bootstrap 5 Django Integration](./bootstrap5-django-integration.md) - django-bootstrap5 package, forms, components, migration patterns

### Tools & Services
- [Claude Code](./claude-code.md) - CLI features, memory management, security, configuration, MCP server integration
- [GitHub CLI](./github-cli.md) - Issue management, project workflows, automation, productivity tips
- [GitHub Actions](./github-actions.md) - CI/CD workflows, Python/Django pipelines, linting, security scanning, troubleshooting
- [MCP (Model Context Protocol)](./mcp-model-context-protocol.md) - Protocol overview, available servers, Claude integration, development

### Local System Information
- [Local System Information](./local-system-info.md) - macOS development environment specifications and setup

### AI/ML Services & APIs
- [AI Image Generation APIs](./ai-image-generation-apis.md) - fal.ai, Replicate, CivitAI features and integration guide
- [Batch Generation APIs](./batch-generation-apis.md) - fal.ai and Replicate batch/multi-image generation parameters and implementation
- [Replicate Model Versioning](./replicate-model-versioning.md) - Version hash requirements, debugging 404 errors, implementation patterns
- [Fal.ai Base64 Images](./fal-ai-base64-images.md) - Handling base64-encoded image responses from certain fal.ai models
- [AI Model Naming Conventions](./ai-model-naming-conventions.md) - Best practices for consistent, user-friendly model naming across providers

### Development Practices
- [Django UI Patterns](./django-ui-patterns.md) - Toast notifications, CSS organization, JavaScript integration, UI testing
- [CSS Frameworks Comparison](./css-frameworks-comparison.md) - Tailwind, Bootstrap, Bulma analysis with Django integration considerations
- [Django Batch Generation Patterns](./django-batch-generation-patterns.md) - OneToMany relationships, worker architecture, UI/UX for batch controls
- [Django Test Isolation](./django-test-isolation.md) - Test independence, mocking external services, controlling background tasks
- [Django Fixtures vs Seed Data](./django-fixtures-vs-seed-data.md) - When to use fixtures vs management commands for data initialization
- [Universal Worker Architecture](./universal-worker-architecture.md) - Provider-agnostic worker pattern for simplified deployment and scaling
- [Django Template Testing Framework](./django-template-testing-framework.md) - Comprehensive template validation including inheritance, security, accessibility, and component consistency
- [Django Project Context Patterns](./django-project-context-patterns.md) - Session-based project context, contextual page headers, reusable filtered components, template security
- [Browser History Modal Patterns](./browser-history-modal-patterns.md) - Back button navigation for modals, History API usage, URL hash management, UX best practices

### Troubleshooting & Solutions
- [Replicate Model Versioning](./replicate-model-versioning.md) - Solving 404 errors with SDXL and other models requiring version hashes
- [SQLite Integer Limits](./sqlite-integer-limits.md) - Handling large seed values and preventing integer overflow errors

---

## Usage Notes

- This MOC is automatically maintained by the `/update-knowledge` command
- Articles are organized by topic area for easy navigation
- Each article follows a standard format with metadata, sources, and local considerations
- Knowledge is kept current through regular updates prioritizing frequently-changing topics

## Last Updated
2025-06-15 - Added Browser History Modal Patterns from Art Factory modal back button fix:
- Browser History Modal Patterns: Comprehensive guide on implementing proper back button navigation for modals using Browser History API. Covers URL hash management, popstate event handling, debugging techniques, and complete implementation patterns. Includes solution for common issue where pushState with same URL doesn't create navigable history entries.

2025-06-15 - Added Django Project Context Patterns from Art Factory project-aware UI implementation:
- Django Project Context Patterns: Comprehensive guide on session-based project context management, contextual page headers with project specifiers, reusable filtered content components, template security with data attributes, and component documentation patterns. Includes implementation from GitHub Issue #82 resolution.

2025-06-15 - Added Django Template Testing Framework from Art Factory template standardization work:
- Django Template Testing Framework: Comprehensive template validation framework covering inheritance validation, component consistency, security testing, accessibility compliance, and documentation validation. Includes implementation patterns, common issues/solutions, and integration with CI/CD pipelines.

2025-06-08 - Added GitHub Actions knowledge from CI failure investigation:
- GitHub Actions: Comprehensive guide covering CI/CD workflows, Python/Django pipelines, linting with flake8/black/isort, security scanning with bandit/safety, performance testing, and troubleshooting common failures. Includes specific solutions for deprecated actions, linting violations, and test environment configuration.

2025-06-04 - Added six key learnings from recent Art Factory development:
- SQLite Integer Limits: Solution for handling large seed values that exceed SQLite's integer range using safe_seed_value() method
- Fal.ai Base64 Images: Pattern for detecting and handling base64-encoded image responses from certain fal.ai models
- AI Model Naming Conventions: Best practices for user-friendly model names that include version numbers but exclude provider names
- Django Test Isolation: Comprehensive patterns for test independence, including DISABLE_AUTO_WORKER_SPAWN setting
- Universal Worker Architecture: Provider-agnostic worker pattern that simplifies deployment and improves resource utilization
- Django Fixtures vs Seed Data: Clear guidance on when to use fixtures (static data) vs management commands (dynamic data)

2025-06-03 - Added two critical articles from Art Factory debugging:
- Replicate Model Versioning: Discovered that SDXL and some other Replicate models require version hashes (e.g., `stability-ai/sdxl:7762fd...`) to avoid 404 errors
- Django Batch Generation Patterns: Comprehensive guide on implementing batch generation with OneToMany relationships, universal workers, and proper UI/UX separation of generation count vs batch size

2025-06-02 - Added five new articles:
- Django Real-time Updates: Comprehensive guide on polling vs WebSockets vs SSE implementation patterns
- GitHub CLI: Issue management, project workflows, and productivity tips from Art Factory experience  
- Bootstrap 5 Django Integration: Migration patterns, component usage, and django-bootstrap5 best practices
- MCP (Model Context Protocol): Overview of Anthropic's protocol for AI-tool integration, available servers, and Claude Desktop setup
- Batch Generation APIs: Detailed documentation of fal.ai and Replicate batch generation parameters for efficient multi-image creation