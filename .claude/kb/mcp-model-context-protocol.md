# MCP (Model Context Protocol)

## Topics Covered
- Protocol overview and architecture
- Available MCP servers
- Claude AI integration
- Popular server categories
- Installation and configuration
- Development tools integration

## Main Content

### What is MCP?

The Model Context Protocol (MCP) is an open-source protocol developed by Anthropic and released in November 2024. It provides a standardized way for AI models to interact with external data sources and tools through secure, two-way connections.

### Architecture

MCP follows a client-server model with three key components:

**MCP Hosts**
- Programs where AI models operate (e.g., Claude Desktop, VS Code)
- Maintain connections with MCP servers
- Handle routing between AI models and servers

**MCP Clients**
- Systems that connect to MCP servers
- Manage authentication and connection lifecycle
- Route requests between hosts and servers

**MCP Servers**
- Lightweight programs exposing specific capabilities
- Can run locally or remotely (remote in development)
- Provide tools and resources to AI models

### Available MCP Servers

As of 2025, there are over 5,000 active MCP servers available through various directories:

**Major Directories**
- **PulseMCP** (pulsemcp.com/servers) - 4540+ servers, updated daily
- **mcp.so** - Community-driven platform for discovering servers
- **mcpservers.org** - Categorized collection of servers
- **cursor.directory/mcp** - Focused on developer tools

### Popular Server Categories

**Development Tools**
- GitHub - Repository management, issues, PRs
- Git - Version control operations
- IDEs and code editors integration

**Databases**
- PostgreSQL, MySQL, SQLite
- Supabase, BigQuery, Redis
- Universal database servers supporting multiple types
- SQL execution, schema exploration, migrations

**Filesystem Operations**
- Local file read/write/delete
- Directory management
- File search and metadata
- Available in multiple languages (Go, Java, Python)

**Business Tools**
- Google Drive - Document management
- Slack - Team communication
- Airtable - Database operations
- Email and calendar integration

**Specialized Services**
- Web scraping (Puppeteer)
- API integrations
- Data analysis tools
- Custom business logic

### Claude AI Integration

**Desktop App Support**
- All Claude.ai plans support MCP servers
- Available for macOS and Windows
- Configure via JSON configuration file
- Claude for Work supports enterprise testing

**Configuration Example**
```json
{
  "mcpServers": {
    "filesystem": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-filesystem", "/path/to/allowed/directory"]
    },
    "github": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-github"],
      "env": {
        "GITHUB_PERSONAL_ACCESS_TOKEN": "your_token_here"
      }
    }
  }
}
```

### Development SDKs

**Available SDKs**
- TypeScript/JavaScript (official)
- Python (official)
- Go (community)
- C# (.NET) (community)
- Java/Quarkus (community)

**Basic Server Implementation (Python)**
```python
from mcp import Server, Tool

server = Server("my-server")

@server.tool()
async def read_file(path: str) -> str:
    """Read a file from the filesystem"""
    with open(path, 'r') as f:
        return f.read()

server.run()
```

### VS Code Integration

MCP servers enhance GitHub Copilot's capabilities:
- Connect any MCP-compatible server
- Use in agentic coding workflows
- Local and remote server support
- Easy testing and development

### Industry Adoption

**Early Adopters**
- Block - Internal systems integration
- Apollo - Data access tools
- Development tool companies: Zed, Replit, Codeium, Sourcegraph

**Significant Milestone**
- March 2025: OpenAI officially adopted MCP
- Integration across ChatGPT desktop app
- Growing ecosystem support

### Current Limitations

1. **Desktop Only** - Currently limited to desktop hosts
2. **Local Execution** - Most servers run locally (remote in development)
3. **Early Stage** - Protocol still evolving
4. **Security** - Careful configuration needed for data access

### Future Development

- Remote server hosting capabilities
- Enterprise deployment toolkits
- Expanded language SDKs
- Standardized authentication methods
- Enhanced security features

## Local Considerations

### macOS Setup
- Install Claude Desktop from claude.ai
- Configuration file: `~/Library/Application Support/Claude/claude_desktop_config.json`
- Use Homebrew for Node.js: `brew install node`
- NPX works out of the box for server installation

### Common Use Cases
- Local file manipulation for coding projects
- Database queries during development
- Git operations without leaving Claude
- API testing and integration

### Security Best Practices
- Limit filesystem access to specific directories
- Use environment variables for sensitive tokens
- Review server permissions before installation
- Keep servers updated regularly

### Troubleshooting
- Check Claude Desktop logs for connection issues
- Verify Node.js/Python installation for servers
- Ensure proper JSON formatting in config
- Test servers independently before Claude integration

## Metadata
- **Last Updated**: 2025-06-02
- **Version**: MCP v1.0 (November 2024 release)
- **Sources**: 
  - https://www.anthropic.com/news/model-context-protocol
  - https://modelcontextprotocol.io/
  - https://github.com/modelcontextprotocol/servers
  - https://www.pulsemcp.com/servers
  - https://mcp.so/