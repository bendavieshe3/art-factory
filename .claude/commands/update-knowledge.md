# Update Knowledge Base

Update or create knowledge base articles for the specified topic.

## Usage
```
/update-knowledge [topic name, URL, file or description]
```

## Instructions

You are implementing the Local Knowledge Management system. Follow these steps:

### 1. Determine Current Date
First, get the current date using a command line utility since knowledge freshness is critical.

### 2. Parse the Arguments
- **No argument**: Perform general knowledge update (prioritize frequent-change topics + oldest updates)
- **With argument**: Parse for topic, URL, file path, conversation reference, or system info request

### 3. Check Existing Knowledge
- Read `.claude/kb/MOC.md` to understand current knowledge structure
- Determine if the topic exists or needs creation
- For ambiguous topics, clarify with the user

### 4. Gather Information
Based on argument type:
- **Topic name**: Web search with local context (OS, project language, etc.)
- **URL**: Fetch and process the content
- **File path**: Read the specified file
- **Conversation reference**: Review recent conversation history
- **System info**: Use command-line tools to gather local system information

### 5. Review Recent History (for general updates)
Check recent conversation history for:
- Failed techniques or commands
- Topics that required web searches
- Local learnings that should be captured

### 6. Create/Update Knowledge Articles
Follow this structure for each article:
```markdown
# [Title]

## Topics Covered
- Topic 1
- Topic 2

## Main Content
[Primary knowledge content]

## Local Considerations
[Environment-specific notes, differences from general sources, troubleshooting]

## Metadata
- **Last Updated**: [Current date]
- **Version**: [Relevant version or publication date]
- **Sources**: 
  - [URL or description]
  - [URL or description]
```

### 7. Handle Conflicts
- Prioritize: vendor docs > corroborated sources > random blogs
- For local knowledge: trust user/environment info over general sources
- When uncertain: record both versions noting the conflict

### 8. Manage File Size
- Split files exceeding 500 lines or 10 subtopics
- Example: "MCP" → "MCP (General)", "MCP (Available Services)", "MCP (Claude Code Setup)"

### 9. Update MOC
- Add new articles in appropriate sections
- Update existing entries if reorganized
- Maintain clear navigation structure

### 10. Scope Guidelines
- **Include**: General information, best practices, version info, local environment specifics
- **Exclude**: Project-specific documentation (belongs in main docs/)
- **Focus**: Information that helps with future development tasks

### Research Areas to Cover
For any topic, consider researching:
- General information/context
- Latest updates and changes
- Available options/offerings
- Recent significant changes
- Usage patterns and best practices
- Local environment relevance (compatibility, complexity, risks, value)

### Example Argument Patterns
- `mcp servers` → Research MCP servers generally
- `that recent test error` → Extract learnings from conversation
- `https://docs.example.com` → Process specific URL
- `my computer specs in my computer` → Gather system info via CLI
- `available mcp services in MCP` → Research and add to MCP topic

Remember: This knowledge base augments your capabilities across sessions. Focus on information that will be valuable for future development work in this environment.