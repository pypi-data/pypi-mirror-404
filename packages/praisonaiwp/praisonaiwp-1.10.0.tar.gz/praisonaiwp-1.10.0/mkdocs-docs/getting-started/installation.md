# Installation

## Requirements

- Python 3.9+
- SSH access to your WordPress server (for SSH transport)
- kubectl configured (for Kubernetes transport)
- WP-CLI installed on the remote server

## Install PraisonAIWP

=== "pip"

    ```bash
    pip install praisonaiwp
    ```

=== "uv"

    ```bash
    uv pip install praisonaiwp
    ```

=== "pipx (recommended for CLI)"

    ```bash
    pipx install praisonaiwp
    ```

=== "From source"

    ```bash
    git clone https://github.com/MervinPraison/praisonaiwp.git
    cd praisonaiwp
    pip install -e .
    ```

## Verify Installation

```bash
praisonaiwp --version
```

## Install WP-CLI on Remote Server

If WP-CLI is not installed on your WordPress server:

```bash
# Download WP-CLI
curl -O https://raw.githubusercontent.com/wp-cli/builds/gh-pages/phar/wp-cli.phar

# Make executable
chmod +x wp-cli.phar

# Move to path
sudo mv wp-cli.phar /usr/local/bin/wp

# Verify
wp --info
```

## Next Steps

- [Quick Start Guide](quickstart.md) - Create your first post
- [Configuration](configuration.md) - Set up server connections
- [Kubernetes Setup](kubernetes.md) - For Kubernetes-hosted WordPress
