
# Local Knowledge Management Proposal

## Before Reading

Before reviewing this document, read and understand the following about Claude Code (which is you):

Claude Code (general): https://docs.anthropic.com/en/docs/claude-code/overview 
Claude Code Custom Slash Commands: https://docs.anthropic.com/en/docs/claude-code/tutorials#create-custom-slash-commands

## Terminology

In places this document may refer to Claude Code as simply 'Claude'. 

## Proposal

The following proposal is for a means whereby Claude code can update and reference a local knowledge store to optimise context size requirements, knowledge freshness, learnings and the specifics of the local environment. This knowledge management does not replace project documentation, and is soley design to assist Claude Code in the execution of its duties. 

THe proposal is called "Local Knowledge"

## Components

Local Knowledge is a Claude Code way-of-work consisting of a custom slash command (update-knowledge), inclusions in CLAUDE.md or other memory, and a dedicated repository of knowledge base articles writtin in markdown.

## Custom Slash Command: update-knowledge

The update-knowledge custom slash command 

## Knowledge Base

Local Knowledge uses a common directory ((project-relative): ./.claude/kb) to house a knowledge base.
- This knowledge base contains markdown files
- It is managed by Claude
- Each markdown article has:
  - A title
  - Topics covered
  - Main content - the majority of knowledge collected
  - Local considerations - where local experience differs from sources, it can be noted here for future troubleshooting and guiance.
  - A 'last updated' field - indicating the date the knowledge was last sourced
  - A 'version' field - relevant version for the content or known publishing date
  - A list of sources as URLs or descriptions

## MOC 

The MOC (Map of Content) is a special file in the knowledge base maintained by Claude that has a useful list of all knowledge articles as links with supporting information about the topics they cover. 

The MOC can contain nesting or structure required to split large topics out across multiple knowledge base articles. 

Claude includes the MOC in every request to understand its local knowledge without reading every file. 

## CLAUDE.md Inclusions

To ensure CLAUDE remains aware of the knowledge and knows to access it, special directives are entered into CLAUDE.md with basic instructions and including (using the '@' notation) the MOC.

### Example CLAUDE.md Inclusion 

This could be refined but indicates my idea for how an effective CLAUDE.md inclusion would look:

```
# For each request
@./.claude/kb/MOC.md
Use the Map of Content (MOC) to read knowledge related on the current request based on the user command and current context
```

The intention is for Claude to still run searches as normal during operation but have additonal latest knowledge and context to avoid some searches and better direct targeted searches. 

## Custom Slash Command: update-knowledge

update-knowledge is the custom slash command for updating and maintaining up-to-date local knowledge. It can be provided with and without an argument.

```
/update-knowledge [topic name, URL, file or description]
```

Generally, the following rules apply:

- without an argument: perform a general knowledge update (see below)
- with an argument: update a specific topic (see below)

### Important - Always know the current date

Because the purpose of the Local Knowledge is to maintain the latest information, it is important that Claude knows the current date regardless of the mode of operation. This is used in ensuring searches terms and search results are informed by this information. 

Run a command line utility to determine the date if not known.

### General Knowledge Update

If no argument is provided, Claude should update the knowledge base articles, prioritising those topics which change most frequently and have been updated the longest time ago.

- Claude should use their common on topics which change most frequently.
  -- For example AI tooling changes very frequently. Development methodologies do not

- Claude should use the last update field on the knowledge base articles to identify the articles which were updated longest ago. 

- Claude should also review the recent history of its output, especially techniques which have failed or topic it had to search to identity topics to create or add

See Updating Knowledge Base files below, and remember to update the MOC and reorganise knowledge if required.

### Specific Topic Update

- The command could take an argument to target a topic to specifically update or create
- The topic should be compared with the content of the MOC.md to determine if the topic exists in some form already. 
- If the topic is ambiguous or seems too broad, clarify the topic with the user
  - For example, if the user commands /update-knowledge scaffolding, Claude could question the user about whether they meant scaffolding in a particular framework or if they mean the building site practice. 

- The command should use sources (See below) to gather new and updated information to create new or to update knowledge base files as per below. 

### Re-organising

- Claude should keep the knowledge base organised and length of files manageable. If files are too big, they should be further split. 
  -- For example, the topic of MCP might be split into MCP (General), MCP (List of available services) and MCP (Installing in Claude Code)

### Updating Knowledge Base Files

- Resultant knowledge should be stored in the Knowledge Base (see above) following the rules for that area, including updating the last updated date, noting sources etc

- Don't include information which should be documentation for the current project. The scope should be limited to general information and how it is observed locally.

- In the case where sources conflict:
  - carefully disambiguate local knowledge (received from the user, current environment, recent history) which should be in that section. 
  Consider the nature of the source: A random blog has less authority than the source of the software vendor, unless heavily corroborated. 
  - If in doubt carefully record both versions, noting the conflict. 
    - Subsequent local information may invalidate the incorrect information

- More than one file can be updated depending on the breadth of the topic or the existing knowledge article structure. Generally avoid files of over 500 lines or 10 subtopics. 

- The Topic can be changed slightly or rephrased to fit existing knowledge articles.
  - For example, A request to update 'Python Language' should update a 'Python' article if already present (and referring to the programming language)

- The MOC.md file should be updated with new or updated files. This includes adding new articles in the correct place for the current MOC structure, which might be nested. 

- Claude should reorganise the knowledgebase, split files or create more granular topics if it makes sense to do so to keep the articles targetted and not bloated (see above)

### Sources

*Generally a commonsense interpretation of the argument can be used to direct Claude on where to source knowledge and what the topic is*

For example:
- If no context for a specific URL or file location is given in the argument, one or more web searches should be used. 
  - Claude should intelligently target searches for the local context; operating environment, project coding language(s), project type (E.g web) or other key targetting information to make sure the knowledge is useful or has the correct caveats
  - Sometimes a search might show that the topic is too broad or has more than one obvious meaning. If in doubt, ask the user.
  - See suggested research areas below for ideas of knowledge for a particular topic

- If the argument contains a file path, the file should be access as the source. The topic can be provided as a part of the argument or inferred from the content

- If the argument contains other phrasing it might refer to the history of the current conversation
  - Typically this is 'local information' - results and local experience which should be included in the relevant part of the knowledge article.
  - This phrases might imply that search should be used to find out more

- Some times the argument might imply Claude shoud gather additional local information using tools
  - For example 'current machine specs' implies Claude should try to gather the information using command line tools (or other tools available via MCP) to gather the information.

- Sometimes the argument will also suggest a topic and potentially a limitation of the information being sourced. 
  - This phrasing might be explicit or implied as `[topic] from [source]` or `[source] in [topic]`. See examples.


### Usage Examples

`/update-knowledge mcp servers` - update or create knowledge on MCP servers
`/update-knowledge` - perform a general update
`/update-knowledge that recent test error` - review the recent conversation for any test errors and add related knowledge, specifically about the commands or tools used and the failure message or code.
`/update-knowledge https://docs.anthropic.com/en/docs/claude-code/memory` - retrieve the page and update related topics
`/update-knowledge my computer specs in my computer` - run commands line tools to assess the current specifications as possible and add them to a knowledgebase article about My Computer
`/update-knowledge available mcp services in MCP` - source new knowledge about available MCP services and add it to the MCP topic (which might require a new subtopic)

## Suggested Research Areas 

The following research areas are suggested for any particular topic:
- General information/context
- latest updates and changes
- Different offerings available
- Significant updates and changes in the recent past
- Usage
- Best practice
- Relevance to current project or environment, including complexity, incompatibilities, risks, value