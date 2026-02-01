# Quick Start

Get started with PraisonAIWP in 5 minutes.

## 1. Configure Your Server

Initialize the configuration:

```bash
praisonaiwp init
```

This creates `~/.praisonaiwp/config.yaml`. Edit it with your server details:

```yaml
default_server: my-server
servers:
  my-server:
    hostname: example.com
    username: admin
    key_file: ~/.ssh/id_ed25519
    wp_path: /var/www/wordpress
    php_bin: /usr/bin/php
    wp_cli: /usr/local/bin/wp
```

## 2. Test Connection

```bash
praisonaiwp list --limit 5
```

If successful, you'll see your WordPress posts listed.

## 3. Create Your First Post

```bash
praisonaiwp create "My First Post" \
  --content "<h2>Hello World</h2><p>This is my first post created with PraisonAIWP!</p>" \
  --status publish
```

!!! tip "HTML Auto-Conversion"
    HTML content is automatically converted to Gutenberg blocks. You don't need to write raw block markup!

## 4. List Posts

```bash
# List all published posts
praisonaiwp list --status publish

# List pages
praisonaiwp list --type page

# JSON output for scripting
praisonaiwp --json list --limit 10
```

## 5. Update a Post

```bash
# Update post title
praisonaiwp update 123 --post-title "Updated Title"

# Update post content
praisonaiwp update 123 --post-content "<p>New content here</p>"
```

## 6. Search for Content

```bash
# Find posts containing a keyword
praisonaiwp find "wordpress"
```

## Next Steps

- [Configuration Guide](configuration.md) - Advanced server configuration
- [Content Commands](../commands/create.md) - Create posts with all options
- [AI Features](../commands/ai.md) - Generate content with AI
- [Examples](../examples.md) - Real-world usage examples
