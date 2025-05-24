# Claude Code

## Topics Covered
- Core features and capabilities
- CLI commands and usage patterns
- Custom slash commands creation and management
- Memory management system
- Security and permissions
- Configuration and settings
- Installation and setup

## Main Content

### Overview

Claude Code is an agentic coding tool that operates directly in your terminal, understands your codebase, and helps you code faster through natural language commands. It's designed as a comprehensive development assistant that can edit files, fix bugs, run tests, and handle various development workflows.

**Key Definition:**
"Claude Code is an agentic coding tool that lives in your terminal, understands your codebase, and helps you code faster through natural language commands."

### Core Capabilities

**File Operations:**
- Edit files and fix bugs across entire codebase
- Automatic codebase exploration without manual file addition
- Create, modify, and delete files with context awareness
- Handle multiple file operations in single requests

**Development Workflow:**
- Execute and fix tests, linting, and build commands
- Search git history and resolve merge conflicts
- Create commits and pull requests
- Answer questions about code architecture and logic
- Browse documentation via web search

**Integration Features:**
- Direct terminal operation
- Maintains project structure awareness
- Works with existing development tools
- Enterprise platform support (Amazon Bedrock, Google Vertex AI)

### CLI Commands and Usage

**Installation:**
```bash
npm install -g @anthropic-ai/claude-code
```

**Main Interaction Modes:**
- **Interactive mode**: `claude` - Start REPL session
- **One-shot mode**: `claude -p "query"` - Run single command and exit
- **Continue mode**: `claude -c` - Resume most recent conversation

**Essential CLI Commands:**
```bash
# Basic usage
claude                    # Start interactive session
claude -p "query"         # Run single query
claude -c                 # Continue last conversation

# Configuration
claude config            # Configure settings
claude config list       # List all settings
claude config get <key>  # View specific setting
claude config set <key> <value>  # Change setting

# Maintenance
claude update             # Update to latest version
```

**Important CLI Flags:**
- `--print` or `-p`: Print response without interactive mode
- `--output-format`: Specify response format (text/json/stream-json)
- `--verbose`: Enable detailed logging
- `--model`: Set specific AI model for session
- `--global`: Apply config changes globally

**Slash Commands (Interactive Mode):**
- `/help`: Get usage help
- `/clear`: Clear conversation history
- `/config`: View/modify configuration
- `/review`: Request code review
- `/vim`: Enter Vim-like editing mode
- `/memory`: Edit memory files
- `/allowed-tools`: Configure tool permissions

**Special Features:**
- `#` prefix: Quickly add memories
- `\` or Option+Enter: Multiline input
- Vim mode: Basic navigation and editing commands

### Custom Slash Commands

Claude Code supports creating custom slash commands through markdown templates stored in specific directories. These allow teams and individuals to standardize workflows and create reusable prompt templates.

**Command Types:**

**1. Project-Specific Commands:**
- **Location**: `.claude/commands/` directory
- **Scope**: Available to entire project team
- **Version Control**: Can be checked into git for team sharing
- **Usage**: `/project:command-name`

**2. Personal Commands:**
- **Location**: `~/.claude/commands/` directory  
- **Scope**: Available across all user's projects
- **Usage**: `/user:command-name`

**Command Creation:**

**Basic Structure:**
```bash
# Create project command
echo "Your prompt template here" > .claude/commands/command-name.md

# Create personal command
echo "Your prompt template here" > ~/.claude/commands/command-name.md
```

**Using $ARGUMENTS Placeholder:**
Commands can include `$ARGUMENTS` to accept parameters from the command invocation:

```markdown
# .claude/commands/fix-issue.md
Find and fix issue #$ARGUMENTS.

Follow these steps:
1. Use `gh issue view $ARGUMENTS` to get issue details
2. Understand the problem described in the ticket
3. Locate relevant code in our codebase
4. Implement a solution that addresses the root cause
5. Add appropriate tests
6. Prepare a concise PR description
```

**Usage**: `/project:fix-issue 1234` replaces `$ARGUMENTS` with "1234"

**Organizational Structure:**
Commands can be organized in subdirectories:
```
.claude/commands/
├── frontend/
│   ├── component.md     # Becomes /project:frontend:component
│   └── test.md         # Becomes /project:frontend:test
├── backend/
│   └── api.md          # Becomes /project:backend:api
└── debug.md            # Becomes /project:debug
```

**Example Command Templates:**

**Security Review Command:**
```markdown
# ~/.claude/commands/security-review.md
Review this code for security vulnerabilities, focusing on:
- Input validation and sanitization
- Authentication and authorization
- SQL injection prevention
- XSS protection
- Sensitive data handling

$ARGUMENTS
```

**Test Generation Command:**
```markdown
# .claude/commands/generate-tests.md
Generate comprehensive test cases for the following function/component:

$ARGUMENTS

Include:
- Unit tests for core functionality
- Edge case testing
- Error handling scenarios
- Integration tests if applicable
```

**Documentation Command:**
```markdown
# .claude/commands/document.md
Create comprehensive documentation for:

$ARGUMENTS

Include:
- Purpose and overview
- Parameters and return values
- Usage examples
- Integration notes
```

**Best Practices:**

**1. Standardization:**
- Use consistent naming conventions
- Include clear step-by-step instructions
- Standardize output formats across team

**2. Parameterization:**
- Use `$ARGUMENTS` for flexible, reusable commands
- Design commands to handle various input types
- Include fallback instructions when arguments are missing

**3. Team Collaboration:**
- Check project commands into version control
- Document command purposes in team README
- Regular review and update of command templates

**4. Common Use Cases:**
- Debugging workflows and log analysis
- Code review and security audits
- Test case generation
- Documentation creation
- Issue tracking and resolution
- Component scaffolding

**Known Issues (2024-2025):**
- Command discovery issues in some environments
- Potential conflicts with MCP server configurations
- `.claude` directory may be ignored in some IDE configurations

**Troubleshooting:**
- Ensure `.claude/commands/` directory is not in `.gitignore`
- Restart Claude Code session after adding new commands
- Check file permissions on command directories
- Verify markdown file syntax and encoding

### Memory Management System

Claude Code provides three memory locations for persistent context:

**1. Project Memory (`./CLAUDE.md`):**
- Team-shared instructions for project architecture
- Workflows and development patterns
- Project-specific coding standards
- Automatically loaded when Claude Code launches

**2. User Memory (`~/.claude/CLAUDE.md`):**
- Personal preferences across all projects
- Coding style preferences
- Tooling shortcuts and workflows
- Global development patterns

**3. Project Memory (Local) - Deprecated:**
- Previously used for personal project-specific preferences
- Functionality moved to other memory types

**Memory Features:**
- Import other files using `@path/to/import` syntax
- Support for relative and absolute paths
- Recursive imports (maximum 5 hops)
- Quick memory addition with `#` prefix
- Direct editing via `/memory` command

**Best Practices:**
- Be specific in memory instructions
- Use structured markdown format
- Periodically review and update memories
- Separate project-wide from personal preferences

### Security and Permissions

**Permission System:**
- Tiered permission levels for different tool types
- Explicit approval required for sensitive operations
- Configurable via `/allowed-tools` or settings
- Default-deny approach for risky operations

**Security Safeguards:**
- Protection against prompt injection
- Context-aware analysis of commands
- Input sanitization for all operations
- Command blocklist (blocks `curl`, `wget`, etc.)

**Network Requirements:**
- api.anthropic.com (API communication)
- statsig.anthropic.com (analytics)
- sentry.io (error reporting)

**Development Container Security:**
- Multi-layered security approach
- Precise access control
- Default-deny network policy
- Startup verification of firewall rules
- Isolated development environment

**Security Recommendations:**
- Review suggested commands before approval
- Avoid piping untrusted content to Claude
- Verify proposed changes to critical files
- Report suspicious behavior immediately

### Configuration and Settings

**Configuration Hierarchy:**
1. Enterprise policies: `/Library/Application Support/ClaudeCode/policies.json`
2. User settings: `~/.claude/settings.json`
3. Project settings: `.claude/settings.json`

**Key Configurable Options:**
- Theme selection and appearance
- Notification channels and methods
- Auto-updater status and behavior
- Tool and command permissions
- Environment variables
- Bash command timeouts
- API key generation scripts

**Configuration Management:**
```bash
# View configurations
claude config list              # All settings
claude config get <key>         # Specific setting

# Modify configurations
claude config set <key> <value> # Local setting
claude config set --global <key> <value>  # Global setting
```

**Advanced Features:**
- Fine-grained tool permissions
- Custom notification methods (terminal bell, system notifications)
- Environment-specific configurations
- Shareable project configurations

### Enterprise Integration

**Supported Platforms:**
- Amazon Bedrock integration
- Google Vertex AI support
- Direct API connections
- Secure, compliant deployments

**Enterprise Features:**
- Centralized policy management
- Audit logging capabilities
- Role-based access controls
- Integration with existing security frameworks

## Local Considerations

**For Art Factory Project:**
- CLAUDE.md already exists with project-specific instructions
- Memory system well-suited for Django development patterns
- Security permissions appropriate for web development
- CLI integration supports Django workflow commands

**Development Workflow Integration:**
- Use for Django management commands
- Integrate with git workflow for commits/PRs
- Leverage for testing and linting automation
- Utilize for database migration management

**Custom Slash Commands for Art Factory:**
Create project-specific commands for common Django workflows:
```bash
# Django model commands
echo "Create a Django model for: $ARGUMENTS. Include appropriate fields, relationships, and Meta options." > .claude/commands/django/model.md

# API endpoint commands  
echo "Create a Django REST API endpoint for $ARGUMENTS. Include serializer, viewset, and URL configuration." > .claude/commands/django/api.md

# Migration commands
echo "Create and apply Django migration for: $ARGUMENTS. Handle data migration if needed." > .claude/commands/django/migrate.md

# Test commands
echo "Generate Django tests for: $ARGUMENTS. Include model tests, view tests, and API tests." > .claude/commands/django/test.md
```

**AI Provider Integration Commands:**
```bash
# Provider testing
echo "Test AI provider integration for $ARGUMENTS. Verify API connectivity, parameter handling, and error cases." > .claude/commands/ai/test-provider.md

# Model configuration
echo "Configure AI model parameters for $ARGUMENTS. Include parameter validation and documentation." > .claude/commands/ai/configure-model.md
```

**Optimization Opportunities:**
- Configure project-specific memory for Django patterns
- Set up tool permissions for development workflow
- Use slash commands for common Django operations
- Leverage web search for Django documentation
- Create Art Factory-specific command templates

**Best Practices for This Environment:**
- Keep CLAUDE.md updated with project evolution
- Use memory system for Django-specific patterns
- Configure appropriate permissions for development tools
- Regular review of security settings
- Maintain project slash commands in version control

## Metadata
- **Last Updated**: 2025-05-24
- **Version**: Current as of May 2025
- **Sources**: 
  - https://docs.anthropic.com/en/docs/claude-code/overview
  - https://docs.anthropic.com/en/docs/claude-code/cli-usage
  - https://docs.anthropic.com/en/docs/claude-code/memory
  - https://docs.anthropic.com/en/docs/claude-code/security
  - https://docs.anthropic.com/en/docs/claude-code/settings
  - https://docs.anthropic.com/en/docs/claude-code/tutorials
  - https://www.anthropic.com/engineering/claude-code-best-practices
  - GitHub issues and community discussions
  - Official Claude Code documentation