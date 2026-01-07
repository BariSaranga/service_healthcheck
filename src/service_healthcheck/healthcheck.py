"""Core health check logic for TCP and HTTPS connectivity."""

import socket
import urllib.request
import urllib.error
from typing import Callable, Optional
import logging

from .models import ServiceConfig, HealthCheckResult


logger = logging.getLogger("service_healthcheck")


def check_tcp_connectivity(
    host: str,
    port: int,
    timeout: float = 5.0,
    socket_create_fn: Optional[Callable] = None
) -> tuple[bool, str]:
    """Check TCP connectivity to a host:port.

    Args:
        host: Hostname or IP address
        port: TCP port number
        timeout: Connection timeout in seconds
        socket_create_fn: Optional socket creation function (for testing)

    Returns:
        Tuple of (success, message)
    """
    socket_fn = socket_create_fn or socket.socket

    try:
        with socket_fn(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(timeout)
            result = sock.connect_ex((host, port))
            if result == 0:
                logger.debug(f"TCP connection successful to {host}:{port}")
                return True, f"TCP connection successful to {host}:{port}"
            else:
                logger.warning(f"TCP connection failed to {host}:{port} (error code: {result})")
                return False, f"TCP connection failed to {host}:{port}"
    except socket.gaierror as e:
        logger.error(f"DNS resolution failed for {host}: {e}")
        return False, f"DNS resolution failed for {host}: {e}"
    except socket.timeout:
        logger.error(f"TCP connection timeout to {host}:{port}")
        return False, f"TCP connection timeout to {host}:{port}"
    except Exception as e:
        logger.error(f"TCP connection error to {host}:{port}: {e}")
        return False, f"TCP connection error: {e}"


def check_https_endpoint(
    host: str,
    path: str,
    timeout: float = 10.0,
    urlopen_fn: Optional[Callable] = None
) -> tuple[bool, str]:
    """Check HTTPS endpoint with GET request.

    Args:
        host: Hostname
        path: URL path (must start with /)
        timeout: Request timeout in seconds
        urlopen_fn: Optional urlopen function (for testing)

    Returns:
        Tuple of (success, message)
    """
    if not path.startswith('/'):
        path = '/' + path

    url = f"https://{host}{path}"
    urlopen = urlopen_fn or urllib.request.urlopen

    try:
        with urlopen(url, timeout=timeout) as response:
            status_code = response.getcode()
            if 200 <= status_code < 300:
                logger.debug(f"HTTPS GET successful to {url} (status: {status_code})")
                return True, f"HTTPS GET successful (status: {status_code})"
            else:
                logger.warning(f"HTTPS GET returned non-2xx status: {status_code}")
                return False, f"HTTPS GET returned status {status_code}"
    except urllib.error.HTTPError as e:
        logger.error(f"HTTPS GET failed to {url}: HTTP {e.code}")
        return False, f"HTTPS GET failed: HTTP {e.code}"
    except urllib.error.URLError as e:
        logger.error(f"HTTPS GET failed to {url}: {e.reason}")
        return False, f"HTTPS GET failed: {e.reason}"
    except socket.timeout:
        logger.error(f"HTTPS GET timeout to {url}")
        return False, f"HTTPS GET timeout"
    except Exception as e:
        logger.error(f"HTTPS GET error to {url}: {e}")
        return False, f"HTTPS GET error: {e}"


def perform_healthcheck(
    service: ServiceConfig,
    tcp_timeout: float = 5.0,
    https_timeout: float = 10.0,
    socket_create_fn: Optional[Callable] = None,
    urlopen_fn: Optional[Callable] = None
) -> HealthCheckResult:
    """Perform complete health check on a service.

    Args:
        service: Service configuration
        tcp_timeout: TCP connection timeout
        https_timeout: HTTPS request timeout
        socket_create_fn: Optional socket creation function (for testing)
        urlopen_fn: Optional urlopen function (for testing)

    Returns:
        HealthCheckResult with check outcomes
    """
    logger.info(f"Starting health check for service: {service.name}")

    # TCP check
    tcp_success, tcp_message = check_tcp_connectivity(
        service.host,
        service.port,
        timeout=tcp_timeout,
        socket_create_fn=socket_create_fn
    )

    # If TCP fails, no point in HTTPS check
    if not tcp_success:
        logger.warning(f"Service {service.name} failed TCP check")
        return HealthCheckResult(
            service=service,
            tcp_success=False,
            https_success=None,
            message=tcp_message
        )

    # HTTPS check if configured
    https_success = None
    message = tcp_message

    if service.https_path:
        https_success, https_message = check_https_endpoint(
            service.host,
            service.https_path,
            timeout=https_timeout,
            urlopen_fn=urlopen_fn
        )
        message = f"{tcp_message}; {https_message}"

        if not https_success:
            logger.warning(f"Service {service.name} failed HTTPS check")

    result = HealthCheckResult(
        service=service,
        tcp_success=tcp_success,
        https_success=https_success,
        message=message
    )

    if result.is_healthy:
        logger.info(f"Service {service.name} is healthy")
    else:
        logger.warning(f"Service {service.name} is unhealthy")

    return result
