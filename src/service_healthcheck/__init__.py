"""Service healthcheck package.

Production-style CLI tool for checking service health via TCP and HTTPS.
"""

__version__ = "1.0.0"
__author__ = "DevOps Learning Lab"

from .models import ServiceConfig, HealthCheckResult
from .healthcheck import perform_healthcheck, check_tcp_connectivity, check_https_endpoint

__all__ = [
    "ServiceConfig",
    "HealthCheckResult",
    "perform_healthcheck",
    "check_tcp_connectivity",
    "check_https_endpoint",
]
