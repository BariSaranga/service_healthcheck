"""Dedicated tests for exit code logic."""

import pytest
from unittest.mock import patch, MagicMock

from service_healthcheck.cli import main
from service_healthcheck.models import ServiceConfig, HealthCheckResult


class TestExitCodeScenarios:
    """Comprehensive tests for all exit code scenarios."""

    @patch('service_healthcheck.cli.perform_healthcheck')
    @patch('service_healthcheck.cli.setup_logging')
    def test_exit_code_0_single_service_healthy(self, mock_setup_logging, mock_perform_healthcheck):
        """Exit code 0: Single service, healthy."""
        mock_setup_logging.return_value = MagicMock()

        mock_perform_healthcheck.return_value = HealthCheckResult(
            service=ServiceConfig("db", "localhost", 5432),
            tcp_success=True,
            message="OK"
        )

        exit_code = main(["db:localhost:5432"])
        assert exit_code == 0

    @patch('service_healthcheck.cli.perform_healthcheck')
    @patch('service_healthcheck.cli.setup_logging')
    def test_exit_code_0_multiple_services_all_healthy(self, mock_setup_logging, mock_perform_healthcheck):
        """Exit code 0: Multiple services, all healthy."""
        mock_setup_logging.return_value = MagicMock()

        mock_perform_healthcheck.side_effect = [
            HealthCheckResult(
                service=ServiceConfig("db", "localhost", 5432),
                tcp_success=True,
                message="OK"
            ),
            HealthCheckResult(
                service=ServiceConfig("api", "localhost", 8080),
                tcp_success=True,
                https_success=True,
                message="OK"
            ),
            HealthCheckResult(
                service=ServiceConfig("cache", "localhost", 6379),
                tcp_success=True,
                message="OK"
            )
        ]

        exit_code = main([
            "db:localhost:5432",
            "api:localhost:8080:/health",
            "cache:localhost:6379"
        ])
        assert exit_code == 0

    @patch('service_healthcheck.cli.perform_healthcheck')
    @patch('service_healthcheck.cli.setup_logging')
    def test_exit_code_2_single_service_unhealthy(self, mock_setup_logging, mock_perform_healthcheck):
        """Exit code 2: Single service, unhealthy."""
        mock_setup_logging.return_value = MagicMock()

        mock_perform_healthcheck.return_value = HealthCheckResult(
            service=ServiceConfig("db", "localhost", 5432),
            tcp_success=False,
            message="Connection refused"
        )

        exit_code = main(["db:localhost:5432"])
        assert exit_code == 2

    @patch('service_healthcheck.cli.perform_healthcheck')
    @patch('service_healthcheck.cli.setup_logging')
    def test_exit_code_2_partial_failures(self, mock_setup_logging, mock_perform_healthcheck):
        """Exit code 2: Partial failures (some healthy, some not)."""
        mock_setup_logging.return_value = MagicMock()

        mock_perform_healthcheck.side_effect = [
            HealthCheckResult(
                service=ServiceConfig("db", "localhost", 5432),
                tcp_success=True,
                message="OK"
            ),
            HealthCheckResult(
                service=ServiceConfig("api", "localhost", 8080),
                tcp_success=False,
                message="Connection refused"
            ),
            HealthCheckResult(
                service=ServiceConfig("cache", "localhost", 6379),
                tcp_success=True,
                message="OK"
            )
        ]

        exit_code = main([
            "db:localhost:5432",
            "api:localhost:8080",
            "cache:localhost:6379"
        ])
        assert exit_code == 2

    @patch('service_healthcheck.cli.perform_healthcheck')
    @patch('service_healthcheck.cli.setup_logging')
    def test_exit_code_2_all_services_unhealthy(self, mock_setup_logging, mock_perform_healthcheck):
        """Exit code 2: All services unhealthy."""
        mock_setup_logging.return_value = MagicMock()

        mock_perform_healthcheck.side_effect = [
            HealthCheckResult(
                service=ServiceConfig("db", "localhost", 5432),
                tcp_success=False,
                message="Connection refused"
            ),
            HealthCheckResult(
                service=ServiceConfig("api", "localhost", 8080),
                tcp_success=False,
                message="Connection refused"
            )
        ]

        exit_code = main([
            "db:localhost:5432",
            "api:localhost:8080"
        ])
        assert exit_code == 2

    @patch('service_healthcheck.cli.perform_healthcheck')
    @patch('service_healthcheck.cli.setup_logging')
    def test_exit_code_2_https_check_fails(self, mock_setup_logging, mock_perform_healthcheck):
        """Exit code 2: TCP succeeds but HTTPS check fails."""
        mock_setup_logging.return_value = MagicMock()

        mock_perform_healthcheck.return_value = HealthCheckResult(
            service=ServiceConfig("api", "localhost", 8080, "/health"),
            tcp_success=True,
            https_success=False,
            message="TCP OK; HTTPS failed: HTTP 503"
        )

        exit_code = main(["api:localhost:8080:/health"])
        assert exit_code == 2

    @patch('service_healthcheck.cli.setup_logging')
    def test_exit_code_3_invalid_service_format(self, mock_setup_logging):
        """Exit code 3: Invalid service format."""
        mock_setup_logging.return_value = MagicMock()

        exit_code = main(["invalid:format"])
        assert exit_code == 3

    @patch('service_healthcheck.cli.setup_logging')
    def test_exit_code_3_invalid_port(self, mock_setup_logging):
        """Exit code 3: Invalid port number."""
        mock_setup_logging.return_value = MagicMock()

        exit_code = main(["db:localhost:notaport"])
        assert exit_code == 3

    @patch('service_healthcheck.cli.perform_healthcheck')
    @patch('service_healthcheck.cli.setup_logging')
    def test_exit_code_3_unexpected_exception(self, mock_setup_logging, mock_perform_healthcheck):
        """Exit code 3: Unexpected exception during execution."""
        mock_setup_logging.return_value = MagicMock()

        mock_perform_healthcheck.side_effect = RuntimeError("Unexpected error")

        exit_code = main(["db:localhost:5432"])
        assert exit_code == 3

    @patch('service_healthcheck.cli.setup_logging')
    def test_exit_code_3_keyboard_interrupt(self, mock_setup_logging):
        """Exit code 3: Keyboard interrupt."""
        mock_logger = MagicMock()
        mock_setup_logging.side_effect = KeyboardInterrupt()

        exit_code = main(["db:localhost:5432"])
        assert exit_code == 3

    @patch('service_healthcheck.cli.perform_healthcheck')
    @patch('service_healthcheck.cli.setup_logging')
    def test_exit_code_3_mixed_invalid_and_valid_services(self, mock_setup_logging, mock_perform_healthcheck):
        """Exit code 3: Mix of invalid and valid service formats."""
        mock_setup_logging.return_value = MagicMock()

        # Should fail on invalid format before checking valid ones
        exit_code = main([
            "db:localhost:5432",
            "invalid",
            "api:localhost:8080"
        ])
        assert exit_code == 3
