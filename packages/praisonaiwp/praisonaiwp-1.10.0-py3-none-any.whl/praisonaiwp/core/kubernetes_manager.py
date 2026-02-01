"""Kubernetes connection management for PraisonAIWP

Provides kubectl exec transport for WordPress installations running in Kubernetes.
"""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional, Tuple

from praisonaiwp.utils.exceptions import SSHConnectionError
from praisonaiwp.utils.logger import get_logger

logger = get_logger(__name__)


class KubernetesManager:
    """Manages Kubernetes pod connections for WordPress operations
    
    Uses kubectl exec for command execution and kubectl cp for file transfers.
    Provides the same interface as SSHManager for seamless integration.
    """

    def __init__(
        self,
        pod_name: Optional[str] = None,
        pod_selector: Optional[str] = None,
        namespace: str = "default",
        container: Optional[str] = None,
        context: Optional[str] = None,
        timeout: int = 30,
    ):
        """
        Initialize Kubernetes Manager

        Args:
            pod_name: Specific pod name to connect to
            pod_selector: Label selector to find pod (e.g., "app=wordpress")
            namespace: Kubernetes namespace (default: "default")
            container: Container name within the pod (optional)
            context: Kubernetes context to use (optional, uses current context)
            timeout: Command timeout in seconds
        """
        self.pod_name = pod_name
        self.pod_selector = pod_selector
        self.namespace = namespace
        self.container = container
        self.context = context
        self.timeout = timeout
        self._connected = False
        self._resolved_pod = None

        logger.debug(
            f"KubernetesManager initialized: pod={pod_name}, "
            f"selector={pod_selector}, namespace={namespace}, container={container}"
        )

    def _build_kubectl_base(self) -> list:
        """Build base kubectl command with context and namespace"""
        cmd = ["kubectl"]
        if self.context:
            cmd.extend(["--context", self.context])
        cmd.extend(["-n", self.namespace])
        return cmd

    def _resolve_pod_name(self) -> str:
        """Resolve pod name from selector if not directly specified"""
        if self._resolved_pod:
            return self._resolved_pod

        if self.pod_name:
            self._resolved_pod = self.pod_name
            return self._resolved_pod

        if not self.pod_selector:
            raise SSHConnectionError(
                "Either pod_name or pod_selector must be specified"
            )

        # Use kubectl to get pod name from selector
        cmd = self._build_kubectl_base()
        cmd.extend([
            "get", "pods",
            "-l", self.pod_selector,
            "-o", "jsonpath={.items[0].metadata.name}",
            "--field-selector", "status.phase=Running"
        ])

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=True
            )
            self._resolved_pod = result.stdout.strip()
            if not self._resolved_pod:
                raise SSHConnectionError(
                    f"No running pods found with selector: {self.pod_selector}"
                )
            logger.info(f"Resolved pod name: {self._resolved_pod}")
            return self._resolved_pod
        except subprocess.TimeoutExpired:
            raise SSHConnectionError(
                f"Timeout resolving pod with selector: {self.pod_selector}"
            )
        except subprocess.CalledProcessError as e:
            raise SSHConnectionError(
                f"Failed to resolve pod: {e.stderr}"
            )

    def connect(self) -> "KubernetesManager":
        """
        Verify kubectl access to the pod

        Returns:
            Self for chaining

        Raises:
            SSHConnectionError: If connection verification fails
        """
        try:
            pod_name = self._resolve_pod_name()
            
            # Test connectivity with a simple command
            cmd = self._build_kubectl_base()
            cmd.extend(["exec", pod_name])
            if self.container:
                cmd.extend(["-c", self.container])
            cmd.extend(["--", "echo", "connected"])

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )

            if result.returncode != 0:
                raise SSHConnectionError(
                    f"Failed to connect to pod {pod_name}: {result.stderr}"
                )

            self._connected = True
            logger.info(f"Connected to Kubernetes pod: {pod_name}")
            return self

        except subprocess.TimeoutExpired:
            raise SSHConnectionError(
                f"Connection timeout to pod in namespace {self.namespace}"
            )
        except Exception as e:
            raise SSHConnectionError(f"Kubernetes connection failed: {e}")

    def execute(self, command: str) -> Tuple[str, str]:
        """
        Execute command in the Kubernetes pod

        Args:
            command: Command to execute

        Returns:
            Tuple of (stdout, stderr)

        Raises:
            SSHConnectionError: If not connected or execution fails
        """
        if not self._connected:
            self.connect()

        pod_name = self._resolve_pod_name()
        
        cmd = self._build_kubectl_base()
        cmd.extend(["exec", pod_name])
        if self.container:
            cmd.extend(["-c", self.container])
        cmd.extend(["--", "sh", "-c", command])

        logger.debug(f"Executing: {command}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout * 10  # Longer timeout for actual commands
            )
            
            stdout = result.stdout
            stderr = result.stderr
            
            if result.returncode != 0 and stderr:
                logger.warning(f"Command returned non-zero: {stderr}")
            
            return stdout, stderr

        except subprocess.TimeoutExpired:
            raise SSHConnectionError(
                f"Command timeout: {command[:100]}..."
            )
        except Exception as e:
            raise SSHConnectionError(f"Command execution failed: {e}")

    def upload_file(self, local_path: str, remote_path: str) -> str:
        """
        Upload a local file to the Kubernetes pod via kubectl cp

        Args:
            local_path: Path to local file
            remote_path: Path on remote pod

        Returns:
            Remote path where file was uploaded

        Raises:
            SSHConnectionError: If not connected or upload fails
        """
        if not self._connected:
            self.connect()

        pod_name = self._resolve_pod_name()
        
        # Format: kubectl cp <local> <namespace>/<pod>:<remote> -c <container>
        remote_target = f"{self.namespace}/{pod_name}:{remote_path}"
        
        cmd = self._build_kubectl_base()
        # Remove namespace since it's in the target path
        cmd = ["kubectl"]
        if self.context:
            cmd.extend(["--context", self.context])
        cmd.extend(["cp", local_path, remote_target])
        if self.container:
            cmd.extend(["-c", self.container])

        logger.debug(f"Uploading {local_path} to {remote_target}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout * 10
            )

            if result.returncode != 0:
                raise SSHConnectionError(
                    f"File upload failed: {result.stderr}"
                )

            logger.info(f"Uploaded {local_path} to {remote_path}")
            return remote_path

        except subprocess.TimeoutExpired:
            raise SSHConnectionError(
                f"File upload timeout: {local_path}"
            )
        except Exception as e:
            raise SSHConnectionError(f"File upload failed: {e}")

    def download_file(self, remote_path: str, local_path: str) -> str:
        """
        Download a file from the Kubernetes pod via kubectl cp

        Args:
            remote_path: Path on remote pod
            local_path: Path to save locally

        Returns:
            Local path where file was saved

        Raises:
            SSHConnectionError: If not connected or download fails
        """
        if not self._connected:
            self.connect()

        pod_name = self._resolve_pod_name()
        
        # Format: kubectl cp <namespace>/<pod>:<remote> <local> -c <container>
        remote_source = f"{self.namespace}/{pod_name}:{remote_path}"
        
        cmd = ["kubectl"]
        if self.context:
            cmd.extend(["--context", self.context])
        cmd.extend(["cp", remote_source, local_path])
        if self.container:
            cmd.extend(["-c", self.container])

        logger.debug(f"Downloading {remote_source} to {local_path}")

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=self.timeout * 10
            )

            if result.returncode != 0:
                raise SSHConnectionError(
                    f"File download failed: {result.stderr}"
                )

            logger.info(f"Downloaded {remote_path} to {local_path}")
            return local_path

        except subprocess.TimeoutExpired:
            raise SSHConnectionError(
                f"File download timeout: {remote_path}"
            )
        except Exception as e:
            raise SSHConnectionError(f"File download failed: {e}")

    def close(self):
        """Close connection (no-op for kubectl, but keeps interface consistent)"""
        self._connected = False
        self._resolved_pod = None
        logger.debug("Kubernetes connection closed")

    def __enter__(self) -> "KubernetesManager":
        """Context manager entry"""
        return self.connect()

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()

    def __del__(self):
        """Cleanup on deletion"""
        try:
            self.close()
        except Exception:
            pass

    @staticmethod
    def from_config(config, server_name: Optional[str] = None) -> "KubernetesManager":
        """
        Create KubernetesManager from configuration

        Args:
            config: Config instance
            server_name: Server name to load config for

        Returns:
            KubernetesManager instance
        """
        server_config = config.get_server(server_name)
        
        return KubernetesManager(
            pod_name=server_config.get("pod_name"),
            pod_selector=server_config.get("pod_selector"),
            namespace=server_config.get("namespace", "default"),
            container=server_config.get("container"),
            context=server_config.get("context"),
            timeout=server_config.get("timeout", 30),
        )
