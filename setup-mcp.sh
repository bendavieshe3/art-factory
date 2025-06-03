  #!/bin/bash
  # setup-mcp.sh

  # Install Node if needed
  which node || brew install node

  # Install MCP servers globally to avoid npx issues
  echo "Installing MCP servers globally..."
  npm install -g @modelcontextprotocol/server-sqlite
  npm install -g @modelcontextprotocol/server-puppeteer
  npm install -g @modelcontextprotocol/server-git
  npm install -g @modelcontextprotocol/server-github

  # Add essential servers using global installations
  echo "Adding MCP servers to Claude..."
  claude mcp add sqlite -- mcp-server-sqlite ./db.sqlite3
  claude mcp add browser -- mcp-server-puppeteer
  claude mcp add git -- mcp-server-git --repository .

  # Add GitHub (you'll need to set your token)
  echo "To add GitHub server, run:"
  echo "claude mcp add github -e GITHUB_PERSONAL_ACCESS_TOKEN=your_token -- mcp-server-github"