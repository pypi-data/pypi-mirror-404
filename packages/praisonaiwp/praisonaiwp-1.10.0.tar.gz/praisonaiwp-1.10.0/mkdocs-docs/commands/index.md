# Commands Overview

PraisonAIWP provides 50+ commands for WordPress management.

## Command Structure

```bash
praisonaiwp [OPTIONS] COMMAND [ARGS]
```

### Global Options

| Option | Description |
|--------|-------------|
| `--server NAME` | Use specific server from config |
| `--json` | Output in JSON format for scripting |
| `--version` | Show version |
| `--help` | Show help |

## Content Management

| Command | Description |
|---------|-------------|
| [`create`](create.md) | Create posts |
| [`update`](update.md) | Update posts |
| [`list`](list.md) | List posts |
| [`find`](find.md) | Search content |

## AI Features

| Command | Description |
|---------|-------------|
| [`ai`](ai.md) | AI content generation |
| [`duplicate`](duplicate.md) | Detect duplicate content |

## Media & Taxonomy

| Command | Description |
|---------|-------------|
| [`media`](media.md) | Upload and manage media |
| [`category`](category.md) | Manage categories |
| [`term`](term.md) | Manage taxonomy terms |

## Administration

| Command | Description |
|---------|-------------|
| [`user`](user.md) | Manage users |
| [`plugin`](plugin.md) | Manage plugins |
| [`theme`](theme.md) | Manage themes |
| [`option`](option.md) | Manage options |

## Database

| Command | Description |
|---------|-------------|
| [`backup`](backup.md) | Backup and restore |
| [`export`](export.md) | Export content |
| [`search-replace`](search-replace.md) | Search and replace |

## Advanced

| Command | Description |
|---------|-------------|
| [`mcp`](mcp.md) | MCP protocol server |
| [`core`](core.md) | WordPress core |
| [`cache`](cache.md) | Cache management |

## Quick Examples

```bash
# Create a post
praisonaiwp create "My Post" --content "<p>Hello!</p>"

# List recent posts
praisonaiwp list --limit 10 --status publish

# Find content
praisonaiwp find "keyword"

# Generate content with AI
praisonaiwp ai generate "Write about AI"

# Backup database
praisonaiwp backup create
```
