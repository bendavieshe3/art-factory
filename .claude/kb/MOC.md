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
- [MCP (Model Context Protocol)](./mcp-model-context-protocol.md) - Protocol overview, available servers, Claude integration, development

### Local System Information
- [Local System Information](./local-system-info.md) - macOS development environment specifications and setup

### AI/ML Services & APIs
- [AI Image Generation APIs](./ai-image-generation-apis.md) - fal.ai, Replicate, CivitAI features and integration guide
- [Batch Generation APIs](./batch-generation-apis.md) - fal.ai and Replicate batch/multi-image generation parameters and implementation
- [Replicate Model Versioning](./replicate-model-versioning.md) - Version hash requirements, debugging 404 errors, implementation patterns

### Development Practices
- [Django UI Patterns](./django-ui-patterns.md) - Toast notifications, CSS organization, JavaScript integration, UI testing
- [CSS Frameworks Comparison](./css-frameworks-comparison.md) - Tailwind, Bootstrap, Bulma analysis with Django integration considerations
- [Django Batch Generation Patterns](./django-batch-generation-patterns.md) - OneToMany relationships, worker architecture, UI/UX for batch controls

### Troubleshooting & Solutions
- [Replicate Model Versioning](./replicate-model-versioning.md) - Solving 404 errors with SDXL and other models requiring version hashes

---

## Usage Notes

- This MOC is automatically maintained by the `/update-knowledge` command
- Articles are organized by topic area for easy navigation
- Each article follows a standard format with metadata, sources, and local considerations
- Knowledge is kept current through regular updates prioritizing frequently-changing topics

## Last Updated
2025-06-03 - Added two critical articles from Art Factory debugging:
- Replicate Model Versioning: Discovered that SDXL and some other Replicate models require version hashes (e.g., `stability-ai/sdxl:7762fd...`) to avoid 404 errors
- Django Batch Generation Patterns: Comprehensive guide on implementing batch generation with OneToMany relationships, universal workers, and proper UI/UX separation of generation count vs batch size

2025-06-02 - Added five new articles:
- Django Real-time Updates: Comprehensive guide on polling vs WebSockets vs SSE implementation patterns
- GitHub CLI: Issue management, project workflows, and productivity tips from Art Factory experience  
- Bootstrap 5 Django Integration: Migration patterns, component usage, and django-bootstrap5 best practices
- MCP (Model Context Protocol): Overview of Anthropic's protocol for AI-tool integration, available servers, and Claude Desktop setup
- Batch Generation APIs: Detailed documentation of fal.ai and Replicate batch generation parameters for efficient multi-image creation