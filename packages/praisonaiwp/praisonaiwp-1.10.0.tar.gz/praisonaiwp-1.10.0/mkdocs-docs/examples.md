# Examples

Real-world usage examples for PraisonAIWP.

## Content Workflows

### Publish a Blog Post

```bash
praisonaiwp create "10 Tips for Productivity" \
  --content "$(cat article.html)" \
  --category "Lifestyle" \
  --tags "productivity,tips,work" \
  --status publish \
  --featured-image cover.jpg
```

### Batch Update Posts

```bash
# Update all drafts to pending review
for id in $(praisonaiwp list --status draft --field ID --format csv); do
  praisonaiwp update $id --post-status pending
done
```

### Schedule Posts

```bash
praisonaiwp create "Future Post" \
  --content "<p>Coming soon!</p>" \
  --status future \
  --date "2024-12-25 09:00:00"
```

## AI-Powered Workflows

### Generate and Publish

```bash
# Generate content
content=$(praisonaiwp ai generate "Write a 500-word article about renewable energy")

# Create post with generated content
praisonaiwp create "Renewable Energy Guide" \
  --content "$content" \
  --category "Environment" \
  --status draft
```

### Find Duplicates Before Publishing

```bash
# Check for similar content
praisonaiwp duplicate check "My new article title and content..."
```

## Multi-Site Management

### Sync Content Between Sites

```bash
# Export from production
praisonaiwp --server production export --type post --output posts.xml

# Import to staging
praisonaiwp --server staging import posts.xml
```

### Compare Sites

```bash
# List plugins on both
echo "=== Production ===" && praisonaiwp --server production plugin list
echo "=== Staging ===" && praisonaiwp --server staging plugin list
```

## Database Operations

### Backup Before Changes

```bash
# Create backup
praisonaiwp backup create --name "pre-migration-$(date +%Y%m%d)"

# Make changes
praisonaiwp search-replace "http://old-domain.com" "https://new-domain.com" --dry-run

# If looks good, run for real
praisonaiwp search-replace "http://old-domain.com" "https://new-domain.com"
```

### Domain Migration

```bash
# Search and replace URLs
praisonaiwp search-replace "https://staging.example.com" "https://example.com" \
  --all-tables \
  --precise

# Flush cache
praisonaiwp cache flush

# Flush rewrite rules
praisonaiwp rewrite flush
```

## Scripting with JSON

### Get Post Data

```bash
# Get post as JSON
post=$(praisonaiwp --json list --include 123)
title=$(echo "$post" | jq -r '.[0].post_title')
echo "Title: $title"
```

### Automation Script

```python
import subprocess
import json

def get_posts(status="publish", limit=10):
    result = subprocess.run(
        ["praisonaiwp", "--json", "list", f"--status={status}", f"--limit={limit}"],
        capture_output=True,
        text=True
    )
    return json.loads(result.stdout)

posts = get_posts()
for post in posts:
    print(f"{post['ID']}: {post['post_title']}")
```

## Kubernetes Examples

### Deploy and Verify

```bash
# After deploying WordPress to K8s
praisonaiwp --server my-k8s-site help

# Create test post
praisonaiwp --server my-k8s-site create "Test Post" \
  --content "<p>Deployment test</p>" \
  --status draft
```

### Check Site Health

```bash
# Core version
praisonaiwp --server my-k8s-site core version

# Plugin status
praisonaiwp --server my-k8s-site plugin list --status active

# Database status
praisonaiwp --server my-k8s-site db check
```

## MCP Integration

### Start MCP Server

```bash
# For AI tool integration (e.g., Claude)
praisonaiwp mcp serve
```

### Use with AI Assistants

Configure your AI assistant to use the MCP server for WordPress operations:

```json
{
  "tools": [
    {
      "name": "praisonaiwp",
      "command": "praisonaiwp mcp serve"
    }
  ]
}
```
