"""Transport factory for PraisonAIWP

Provides unified transport creation based on server configuration.
Supports both SSH (default) and Kubernetes transports.
"""

from typing import Optional, Union

from praisonaiwp.utils.logger import get_logger

logger = get_logger(__name__)


def get_transport(config, server_name: Optional[str] = None):
    """
    Factory function to create the appropriate transport manager
    based on server configuration.

    Args:
        config: Config instance
        server_name: Server name from config (optional, uses default if not provided)

    Returns:
        SSHManager or KubernetesManager instance

    Example config for SSH (default):
        servers:
          my-server:
            hostname: example.com
            username: admin
            wp_path: /var/www/wordpress

    Example config for Kubernetes:
        servers:
          praison-ai:
            transport: kubernetes
            pod_selector: app=php-nginx
            namespace: default
            container: wb-php
            wp_path: /var/www/pa/web
    """
    server_config = config.get_server(server_name)
    transport_type = server_config.get("transport", "ssh").lower()

    if transport_type == "kubernetes" or transport_type == "k8s":
        from praisonaiwp.core.kubernetes_manager import KubernetesManager
        
        logger.info(f"Using Kubernetes transport for server: {server_name or 'default'}")
        return KubernetesManager(
            pod_name=server_config.get("pod_name"),
            pod_selector=server_config.get("pod_selector"),
            namespace=server_config.get("namespace", "default"),
            container=server_config.get("container"),
            context=server_config.get("context"),
            timeout=server_config.get("timeout", 30),
        )
    else:
        # Default to SSH transport
        from praisonaiwp.core.ssh_manager import SSHManager
        
        logger.debug(f"Using SSH transport for server: {server_name or 'default'}")
        return SSHManager.from_config(config, server_config.get('hostname', server_name))


# Type alias for transport managers
TransportManager = Union["SSHManager", "KubernetesManager"]
