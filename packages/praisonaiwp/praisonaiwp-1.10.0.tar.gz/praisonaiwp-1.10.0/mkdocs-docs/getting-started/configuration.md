# Configuration

PraisonAIWP uses a YAML configuration file to manage server connections.

## Configuration File Location

```
~/.praisonaiwp/config.yaml
```

## Initialize Configuration

```bash
praisonaiwp init
```

## Configuration Structure

```yaml
default_server: my-server
version: '2.0'

servers:
  my-server:
    # Website URL (for URL routing)
    website: https://example.com
    description: "My WordPress site"
    
    # SSH connection
    hostname: example.com
    username: admin
    key_file: ~/.ssh/id_ed25519
    port: 22
    
    # WordPress paths
    wp_path: /var/www/wordpress
    php_bin: /usr/bin/php
    wp_cli: /usr/local/bin/wp

settings:
  auto_backup: true
  auto_route: true
  log_level: INFO
  parallel_threshold: 10
  parallel_workers: 10
  retry_attempts: 3
  ssh_timeout: 30
```

## Server Configuration Options

### SSH Transport (Default)

| Option | Required | Description |
|--------|----------|-------------|
| `hostname` | Yes | Server hostname or IP |
| `username` | No | SSH username (uses SSH config if not set) |
| `key_file` | No | Path to SSH private key |
| `port` | No | SSH port (default: 22) |
| `ssh_host` | No | SSH config host alias |
| `wp_path` | Yes | WordPress installation path |
| `php_bin` | No | PHP binary path (default: php) |
| `wp_cli` | No | WP-CLI path (default: /usr/local/bin/wp) |

### Kubernetes Transport

See [Kubernetes Setup](kubernetes.md) for detailed instructions.

```yaml
servers:
  my-k8s-site:
    transport: kubernetes
    pod_selector: app=wordpress
    namespace: default
    container: wordpress
    wp_path: /var/www/html
    php_bin: /usr/local/bin/php
    wp_cli: wp
```

## Multiple Servers

```yaml
servers:
  production:
    website: https://example.com
    hostname: prod.example.com
    wp_path: /var/www/wordpress
    
  staging:
    website: https://staging.example.com
    hostname: staging.example.com
    wp_path: /var/www/wordpress
    
  local:
    website: http://localhost:8080
    ssh_host: local-wp
    wp_path: /var/www/html
```

### Using Different Servers

```bash
# Use default server
praisonaiwp list

# Use specific server
praisonaiwp --server staging list

# Or specify by URL
praisonaiwp list --url https://staging.example.com
```

## SSH Config Integration

You can reference `~/.ssh/config` hosts:

```yaml
servers:
  my-server:
    ssh_host: my-alias  # Uses ~/.ssh/config settings
    wp_path: /var/www/wordpress
```

Your `~/.ssh/config`:
```
Host my-alias
    HostName example.com
    User admin
    IdentityFile ~/.ssh/id_ed25519
```

## Environment Variables

Override config with environment variables:

```bash
export WP_HOSTNAME=example.com
export WP_SSH_USER=admin
export WP_PATH=/var/www/wordpress
export WP_PHP_BIN=/usr/bin/php
export WP_CLI_BIN=/usr/local/bin/wp
```

## Plesk Servers

For Plesk-hosted WordPress:

```yaml
servers:
  plesk-site:
    hostname: server.example.com
    username: subscription_user
    key_file: ~/.ssh/id_ed25519
    wp_path: /var/www/vhosts/example.com/httpdocs
    php_bin: /opt/plesk/php/8.3/bin/php
    wp_cli: /usr/local/bin/wp
```
