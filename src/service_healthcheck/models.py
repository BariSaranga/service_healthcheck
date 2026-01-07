"""Data models for service healthcheck."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class ServiceConfig:
    """Configuration for a service to healthcheck.

    Attributes:
        name: Human-readable service name
        host: Hostname or IP address
        port: TCP port number
        https_path: Optional HTTPS path for GET request (e.g., '/health')
    """
    name: str
    host: str
    port: int
    https_path: Optional[str] = None

    def __post_init__(self):
        """Validate service configuration."""
        if not self.name:
            raise ValueError("Service name cannot be empty")
        if not self.host:
            raise ValueError("Service host cannot be empty")
        if not isinstance(self.port, int) or self.port < 1 or self.port > 65535:
            raise ValueError(f"Invalid port number: {self.port}")


@dataclass
class HealthCheckResult:
    """Result of a service health check.

    Attributes:
        service: The service configuration that was checked
        tcp_success: Whether TCP connectivity check succeeded
        https_success: Whether HTTPS check succeeded (None if not performed)
        message: Human-readable status message
    """
    service: ServiceConfig
    tcp_success: bool
    https_success: Optional[bool] = None
    message: str = ""

    @property
    def is_healthy(self) -> bool:
        """Determine if the overall check is healthy.

        Returns:
            True if TCP succeeded and HTTPS succeeded (if attempted)
        """
        if not self.tcp_success:
            return False
        if self.https_success is not None and not self.https_success:
            return False
        return True
