"""Tests for CLI functionality."""

import pytest
from unittest.mock import Mock, MagicMock, patch

from service_healthcheck.cli import (
    parse_service,
    parse_arguments,
    determine_exit_code,
    main
)
from service_healthcheck.models import ServiceConfig, HealthCheckResult


class TestParseService:
    """Tests for service string parsing."""

    def test_parse_service_tcp_only(self):
        """Test parsing service with TCP only."""
        service = parse_service("db:localhost:5432")

        assert service.name == "db"
        assert service.host == "localhost"
        assert service.port == 5432
        assert service.https_path is None

    def test_parse_service_with_https_path(self):
        """Test parsing service with HTTPS path."""
        service = parse_service("api:example.com:443:/health")

        assert service.name == "api"
        assert service.host == "example.com"
        assert service.port == 443
        assert service.https_path == "/health"

    def test_parse_service_with_https_path_no_slash(self):
        """Test parsing service with HTTPS path without leading slash."""
        service = parse_service("api:example.com:443:status")

        assert service.name == "api"
        assert service.https_path == "/status"

    def test_parse_service_with_path_containing_colon(self):
        """Test parsing service with path containing colons."""
        service = parse_service("api:example.com:443:/api/v1/health:check")

        assert service.name == "api"
        assert service.host == "example.com"
        assert service.port == 443
        assert service.https_path == "/api/v1/health:check"

    def test_parse_service_invalid_format_missing_parts(self):
        """Test parsing service with missing parts."""
        with pytest.raises(ValueError, match="Invalid service format"):
            parse_service("db:localhost")

    def test_parse_service_invalid_port(self):
        """Test parsing service with invalid port."""
        with pytest.raises(ValueError, match="Invalid port number"):
            parse_service("db:localhost:notaport")

    def test_parse_service_with_whitespace(self):
        """Test parsing service with whitespace."""
        service = parse_service(" db : localhost : 5432 ")

        assert service.name == "db"
        assert service.host == "localhost"
        assert service.port == 5432


class TestParseArguments:
    """Tests for command-line argument parsing."""

    def test_parse_arguments_single_service(self):
        """Test parsing arguments with single service."""
        args = parse_arguments(["db:localhost:5432"])

        assert len(args.services) == 1
        assert args.services[0] == "db:localhost:5432"
        assert args.log_file == "./healthcheck.log"
        assert args.tcp_timeout == 5.0
        assert args.https_timeout == 10.0
        assert args.verbose is False

    def test_parse_arguments_multiple_services(self):
        """Test parsing arguments with multiple services."""
        args = parse_arguments([
            "db:localhost:5432",
            "api:example.com:443:/health",
            "cache:redis:6379"
        ])

        assert len(args.services) == 3

    def test_parse_arguments_custom_log_file(self):
        """Test parsing arguments with custom log file."""
        args = parse_arguments([
            "db:localhost:5432",
            "--log-file", "/var/log/healthcheck.log"
        ])

        assert args.log_file == "/var/log/healthcheck.log"

    def test_parse_arguments_custom_timeouts(self):
        """Test parsing arguments with custom timeouts."""
        args = parse_arguments([
            "db:localhost:5432",
            "--tcp-timeout", "10.0",
            "--https-timeout", "20.0"
        ])

        assert args.tcp_timeout == 10.0
        assert args.https_timeout == 20.0

    def test_parse_arguments_verbose(self):
        """Test parsing arguments with verbose flag."""
        args = parse_arguments([
            "db:localhost:5432",
            "--verbose"
        ])

        assert args.verbose is True

    def test_parse_arguments_no_services(self):
        """Test parsing arguments without services (should fail)."""
        with pytest.raises(SystemExit):
            parse_arguments([])


class TestDetermineExitCode:
    """Tests for exit code determination."""

    def test_exit_code_all_healthy(self):
        """Test exit code when all services are healthy."""
        results = [
            HealthCheckResult(
                service=ServiceConfig("svc1", "host1", 80),
                tcp_success=True,
                message="OK"
            ),
            HealthCheckResult(
                service=ServiceConfig("svc2", "host2", 443),
                tcp_success=True,
                https_success=True,
                message="OK"
            )
        ]

        exit_code = determine_exit_code(results)
        assert exit_code == 0

    def test_exit_code_partial_failure(self):
        """Test exit code when some services are unhealthy."""
        results = [
            HealthCheckResult(
                service=ServiceConfig("svc1", "host1", 80),
                tcp_success=True,
                message="OK"
            ),
            HealthCheckResult(
                service=ServiceConfig("svc2", "host2", 443),
                tcp_success=False,
                message="Failed"
            )
        ]

        exit_code = determine_exit_code(results)
        assert exit_code == 2

    def test_exit_code_all_unhealthy(self):
        """Test exit code when all services are unhealthy."""
        results = [
            HealthCheckResult(
                service=ServiceConfig("svc1", "host1", 80),
                tcp_success=False,
                message="Failed"
            ),
            HealthCheckResult(
                service=ServiceConfig("svc2", "host2", 443),
                tcp_success=False,
                message="Failed"
            )
        ]

        exit_code = determine_exit_code(results)
        assert exit_code == 2

    def test_exit_code_empty_results(self):
        """Test exit code with empty results list."""
        exit_code = determine_exit_code([])
        assert exit_code == 0


class TestMainFunction:
    """Tests for main CLI entry point."""

    @patch('service_healthcheck.cli.perform_healthcheck')
    @patch('service_healthcheck.cli.setup_logging')
    def test_main_successful_all_healthy(self, mock_setup_logging, mock_perform_healthcheck):
        """Test main function with all services healthy."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_perform_healthcheck.return_value = HealthCheckResult(
            service=ServiceConfig("db", "localhost", 5432),
            tcp_success=True,
            message="OK"
        )

        exit_code = main(["db:localhost:5432"])

        assert exit_code == 0
        mock_perform_healthcheck.assert_called_once()

    @patch('service_healthcheck.cli.perform_healthcheck')
    @patch('service_healthcheck.cli.setup_logging')
    def test_main_partial_failure(self, mock_setup_logging, mock_perform_healthcheck):
        """Test main function with partial failures."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        # Return different results for each call
        mock_perform_healthcheck.side_effect = [
            HealthCheckResult(
                service=ServiceConfig("db", "localhost", 5432),
                tcp_success=True,
                message="OK"
            ),
            HealthCheckResult(
                service=ServiceConfig("api", "localhost", 8080),
                tcp_success=False,
                message="Failed"
            )
        ]

        exit_code = main(["db:localhost:5432", "api:localhost:8080"])

        assert exit_code == 2

    @patch('service_healthcheck.cli.setup_logging')
    def test_main_invalid_service_format(self, mock_setup_logging):
        """Test main function with invalid service format."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        exit_code = main(["invalid"])

        assert exit_code == 3

    @patch('service_healthcheck.cli.perform_healthcheck')
    @patch('service_healthcheck.cli.setup_logging')
    def test_main_unexpected_exception(self, mock_setup_logging, mock_perform_healthcheck):
        """Test main function with unexpected exception."""
        mock_logger = MagicMock()
        mock_setup_logging.return_value = mock_logger

        mock_perform_healthcheck.side_effect = RuntimeError("Unexpected error")

        exit_code = main(["db:localhost:5432"])

        assert exit_code == 3
