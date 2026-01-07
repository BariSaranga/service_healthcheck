"""Command-line interface for service healthcheck."""

import argparse
import sys
import logging
from typing import List

from .models import ServiceConfig, HealthCheckResult
from .healthcheck import perform_healthcheck
from .logging_config import setup_logging


def parse_service(service_str: str) -> ServiceConfig:
    """Parse a service specification string.

    Format: name:host:port[:https_path]

    Args:
        service_str: Service specification string

    Returns:
        ServiceConfig instance

    Raises:
        ValueError: If service string is invalid
    """
    parts = service_str.split(':')

    if len(parts) < 3:
        raise ValueError(
            f"Invalid service format: '{service_str}'. "
            "Expected: name:host:port[:https_path]"
        )

    name = parts[0].strip()
    host = parts[1].strip()

    try:
        port = int(parts[2].strip())
    except ValueError:
        raise ValueError(f"Invalid port number in '{service_str}': {parts[2]}")

    https_path = None
    if len(parts) >= 4:
        https_path = ':'.join(parts[3:]).strip()  # Rejoin in case path contains ':'
        if https_path:
            if not https_path.startswith('/'):
                https_path = '/' + https_path

    return ServiceConfig(name=name, host=host, port=port, https_path=https_path)


def parse_arguments(args: List[str] = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        args: Argument list (defaults to sys.argv)

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        prog="service-healthcheck",
        description="Check health of services via TCP and optional HTTPS",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s api:api.example.com:443:/health
  %(prog)s db:localhost:5432 cache:redis.local:6379
  %(prog)s web:example.com:443:/status --log-file /var/log/healthcheck.log

Service format: name:host:port[:https_path]
  - name: Service identifier
  - host: Hostname or IP
  - port: TCP port number
  - https_path: Optional HTTPS path for GET request

Exit codes:
  0 - All services healthy
  2 - Partial failures (some services unhealthy)
  3 - Execution or configuration error
        """
    )

    parser.add_argument(
        'services',
        nargs='+',
        metavar='SERVICE',
        help='Service(s) to check (format: name:host:port[:https_path])'
    )

    parser.add_argument(
        '--log-file',
        default='./healthcheck.log',
        help='Path to log file (default: ./healthcheck.log)'
    )

    parser.add_argument(
        '--tcp-timeout',
        type=float,
        default=5.0,
        metavar='SECONDS',
        help='TCP connection timeout in seconds (default: 5.0)'
    )

    parser.add_argument(
        '--https-timeout',
        type=float,
        default=10.0,
        metavar='SECONDS',
        help='HTTPS request timeout in seconds (default: 10.0)'
    )

    parser.add_argument(
        '--verbose',
        action='store_true',
        help='Enable verbose output (DEBUG level)'
    )

    return parser.parse_args(args)


def determine_exit_code(results: List[HealthCheckResult]) -> int:
    """Determine appropriate exit code based on check results.

    Args:
        results: List of health check results

    Returns:
        Exit code (0=all healthy, 2=partial failures)
    """
    if not results:
        return 0

    healthy_count = sum(1 for r in results if r.is_healthy)
    total_count = len(results)

    if healthy_count == total_count:
        return 0  # All healthy
    else:
        return 2  # Partial or complete failure


def main(args: List[str] = None) -> int:
    """Main entry point for CLI.

    Args:
        args: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code (0=success, 2=partial failure, 3=error)
    """
    try:
        # Parse arguments
        parsed_args = parse_arguments(args)

        # Setup logging
        log_level = logging.DEBUG if parsed_args.verbose else logging.INFO
        logger = setup_logging(
            log_file=parsed_args.log_file,
            log_level=log_level,
            console_level=log_level
        )

        logger.info("=" * 60)
        logger.info("Service Health Check - Starting")
        logger.info("=" * 60)

        # Parse services
        services = []
        for service_str in parsed_args.services:
            try:
                service = parse_service(service_str)
                services.append(service)
                logger.debug(f"Parsed service: {service}")
            except ValueError as e:
                logger.error(f"Invalid service specification: {e}")
                return 3

        if not services:
            logger.error("No valid services to check")
            return 3

        # Perform health checks
        results = []
        for service in services:
            result = perform_healthcheck(
                service,
                tcp_timeout=parsed_args.tcp_timeout,
                https_timeout=parsed_args.https_timeout
            )
            results.append(result)

        # Summary
        logger.info("=" * 60)
        logger.info("Health Check Summary")
        logger.info("=" * 60)

        for result in results:
            status = "HEALTHY" if result.is_healthy else "UNHEALTHY"
            logger.info(f"{result.service.name}: {status}")
            if parsed_args.verbose:
                logger.debug(f"  Details: {result.message}")

        healthy_count = sum(1 for r in results if r.is_healthy)
        total_count = len(results)
        logger.info(f"Total: {healthy_count}/{total_count} healthy")

        # Determine exit code
        exit_code = determine_exit_code(results)

        if exit_code == 0:
            logger.info("Result: All services healthy")
        else:
            logger.warning("Result: Some services unhealthy")

        logger.info("=" * 60)

        return exit_code

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 3
    except Exception as e:
        # Catch-all for unexpected errors
        print(f"FATAL ERROR: {e}", file=sys.stderr)
        logging.getLogger("service_healthcheck").exception("Unhandled exception")
        return 3


if __name__ == "__main__":
    sys.exit(main())
