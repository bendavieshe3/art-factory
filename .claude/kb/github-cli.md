# GitHub CLI (gh)

## Topics Covered
- Issue management commands
- Project management
- Workflow automation
- Productivity tips and aliases
- Best practices for 2024

## Main Content

### Core Issue Management

**Creating Issues**
```bash
# Create issue with interactive prompts
gh issue create

# Create with flags
gh issue create --title "[BUG] Title" --body "Description" --label "bug,high"

# With milestone and assignee
gh issue create --title "Feature" --milestone "v0.2" --assignee @me
```

**Listing and Viewing**
```bash
# List all open issues
gh issue list

# Filter by labels, state, milestone
gh issue list --label "bug" --state all --milestone "v0.1 MVP"

# View specific issue
gh issue view 123

# List with custom limit
gh issue list --limit 50
```

**Managing Issues**
```bash
# Edit issue
gh issue edit 123 --title "New title" --add-label "critical"

# Close/reopen
gh issue close 123
gh issue reopen 123

# Add comment
gh issue comment 123 --body "Progress update"

# Delete issue
gh issue delete 123
```

### Project Management

**Project Commands (Generally Available)**
```bash
# List projects
gh project list

# View project
gh project view PROJECT_NUMBER

# Create project item from issue
gh project item-add PROJECT_NUMBER --issue ISSUE_NUMBER

# Update item status
gh project item-edit --project PROJECT_NUMBER --id ITEM_ID --field Status --value "In Progress"
```

**Authentication for Projects**
```bash
# Check auth status and scopes
gh auth status

# Re-authenticate with project scope
gh auth login --scopes project
```

### Pull Request Management

**Creating PRs**
```bash
# Interactive creation
gh pr create

# With flags
gh pr create --title "Title" --body "Description" --base main --head feature-branch

# Draft PR
gh pr create --draft

# With reviewers
gh pr create --reviewer user1,user2
```

**PR Operations**
```bash
# List PRs
gh pr list

# Check PR status
gh pr checks

# View PR
gh pr view 123

# Checkout PR locally
gh pr checkout 123

# Merge PR
gh pr merge 123 --squash --delete-branch
```

### Workflow Automation

**GitHub Actions Integration**
```bash
# List workflows
gh workflow list

# View workflow runs
gh workflow view WORKFLOW_NAME

# Run workflow manually
gh workflow run WORKFLOW_NAME

# View run details
gh run list
gh run view RUN_ID
```

**Automation Patterns**
- Auto-move issues to "Done" when closed
- Assign team members based on labels
- Update project boards on PR merge
- Trigger deployments from CLI

### Productivity Features

**Aliases**
```bash
# Create aliases
gh alias set pv 'pr view'
gh alias set iv 'issue view'
gh alias set bugs 'issue list --label bug'

# List aliases
gh alias list

# Delete alias
gh alias delete ALIAS_NAME
```

**Common Aliases**
```bash
# Quick PR creation with conventional commit
gh alias set pr-feat 'pr create --title "feat: $1" --body "$2"'

# List my assigned issues
gh alias set my-issues 'issue list --assignee @me'

# Recent closed issues
gh alias set recent-closed 'issue list --state closed --limit 10'
```

### Advanced Usage

**JSON Output and Filtering**
```bash
# Get JSON output
gh issue list --json number,title,state

# With jq filtering
gh issue list --json number,title,labels | jq '.[] | select(.labels[].name == "bug")'

# Export to CSV
gh issue list --json number,title,state | jq -r '.[] | [.number, .title, .state] | @csv'
```

**Multi-Repository Operations**
```bash
# Clone repository
gh repo clone owner/repo

# Fork repository
gh repo fork owner/repo --clone

# Create repository
gh repo create my-project --public --clone

# View repository
gh repo view owner/repo --web
```

### Extensions

**Popular Extensions**
- `gh-dash`: Terminal dashboard for PRs/issues
- `gh-copilot`: GitHub Copilot in CLI
- `gh-actions-cache`: Manage Actions cache

**Installing Extensions**
```bash
# Install extension
gh extension install dlvhdr/gh-dash

# List installed
gh extension list

# Update extensions
gh extension upgrade --all
```

## Local Considerations

### Art Factory Workflow
```bash
# Common issue creation pattern
gh issue create --title "[ENHANCEMENT] Feature name" \
  --body "Description" \
  --label "enhancement,ui/order-page,medium" \
  --milestone "v0.2 Polish"

# Checking implementation status
gh issue list --milestone "v0.1 MVP" --state open

# Quick PR for features
gh pr create --title "Implement feature (Issue #N)" \
  --body "Closes #N"
```

### macOS Specific
- Install via Homebrew: `brew install gh`
- Keychain integration for auth tokens
- Works well with iTerm2/Terminal
- No known compatibility issues

### Team Workflows
- Use issue templates in `.github/ISSUE_TEMPLATE/`
- Standardize labels across repositories
- Create project automation rules
- Use milestones for release planning

## Metadata
- **Last Updated**: 2025-06-02
- **Version**: gh version 2.40+
- **Sources**: 
  - https://cli.github.com/manual/
  - https://www.analyticsvidhya.com/blog/2024/01/github-cli/
  - https://commerce.nearform.com/blog/2024/the-pragmatic-programmers-guide-to-github-cli
  - Art Factory project experience