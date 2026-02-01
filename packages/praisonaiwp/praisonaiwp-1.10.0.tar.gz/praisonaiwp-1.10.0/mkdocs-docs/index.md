# PraisonAIWP

**AI-powered WordPress content management** via WP-CLI over SSH and Kubernetes.

<div class="grid cards" markdown>

- :rocket: **Simple**

    ---

    One-line commands for complex WordPress operations

- :robot: **AI-Powered**

    ---

    Generate content, detect duplicates, and optimize with AI

- :cloud: **Multi-Transport**

    ---

    SSH for traditional hosting, kubectl for Kubernetes

- :zap: **Fast**

    ---

    Parallel operations and efficient batch processing

</div>

## Quick Start

```bash
# Install
pip install praisonaiwp

# Initialize configuration
praisonaiwp init

# Create a post
praisonaiwp create "My First Post" --content "<p>Hello World!</p>"

# List posts
praisonaiwp list --type post
```

## Features

### Content Management
- **Create, update, delete posts** with Gutenberg block support
- **Automatic HTML to Gutenberg conversion**
- **Batch operations** for multiple posts
- **Search and find** content across your site

### AI Features
- **AI content generation** with OpenAI integration
- **Duplicate detection** to find similar content
- **Content optimization** suggestions

### Multi-Transport Support
- **SSH** for traditional hosting (Plesk, cPanel, VPS)
- **Kubernetes** for containerized WordPress (AKS, GKE, EKS)

### Administration
- Manage users, roles, and capabilities
- Control plugins and themes
- Database backup and restore
- Import/export content

## Installation

=== "pip"

    ```bash
    pip install praisonaiwp
    ```

=== "uv"

    ```bash
    uv pip install praisonaiwp
    ```

=== "pipx"

    ```bash
    pipx install praisonaiwp
    ```

## Next Steps

<div class="grid cards" markdown>

- [:material-rocket-launch: **Quick Start**](getting-started/quickstart.md)
- [:material-cog: **Configuration**](getting-started/configuration.md)
- [:material-kubernetes: **Kubernetes Setup**](getting-started/kubernetes.md)
- [:material-book: **Command Reference**](commands/index.md)

</div>
