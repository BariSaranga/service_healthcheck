"""Tests for core healthcheck functionality."""

import socket
import urllib.error
from unittest.mock import Mock, MagicMock, patch
import pytest

from service_healthcheck.healthcheck import (
    check_tcp_connectivity,
    check_https_endpoint,
    perform_healthcheck
)
from service_healthcheck.models import ServiceConfig


class TestTCPConnectivity:
    """Tests for TCP connectivity checks."""

    def test_successful_tcp_connection(self):
        """Test successful TCP connection."""
        mock_socket = MagicMock()
        mock_socket.__enter__ = Mock(return_value=mock_socket)
        mock_socket.__exit__ = Mock(return_value=False)
        mock_socket.connect_ex.return_value = 0

        def mock_socket_fn(*args, **kwargs):
            return mock_socket

        success, message = check_tcp_connectivity(
            "localhost",
            5432,
            socket_create_fn=mock_socket_fn
        )

        assert success is True
        assert "successful" in message.lower()
        mock_socket.settimeout.assert_called_once()
        mock_socket.connect_ex.assert_called_once_with(("localhost", 5432))

    def test_failed_tcp_connection(self):
        """Test failed TCP connection."""
        mock_socket = MagicMock()
        mock_socket.__enter__ = Mock(return_value=mock_socket)
        mock_socket.__exit__ = Mock(return_value=False)
        mock_socket.connect_ex.return_value = 111  # Connection refused

        def mock_socket_fn(*args, **kwargs):
            return mock_socket

        success, message = check_tcp_connectivity(
            "localhost",
            9999,
            socket_create_fn=mock_socket_fn
        )

        assert success is False
        assert "failed" in message.lower()

    def test_tcp_connection_timeout(self):
        """Test TCP connection timeout."""
        mock_socket = MagicMock()
        mock_socket.__enter__ = Mock(return_value=mock_socket)
        mock_socket.__exit__ = Mock(return_value=False)
        mock_socket.connect_ex.side_effect = socket.timeout()

        def mock_socket_fn(*args, **kwargs):
            return mock_socket

        success, message = check_tcp_connectivity(
            "slow-host.example.com",
            443,
            socket_create_fn=mock_socket_fn
        )

        assert success is False
        assert "timeout" in message.lower()

    def test_tcp_dns_resolution_failure(self):
        """Test DNS resolution failure."""
        mock_socket = MagicMock()
        mock_socket.__enter__ = Mock(return_value=mock_socket)
        mock_socket.__exit__ = Mock(return_value=False)
        mock_socket.connect_ex.side_effect = socket.gaierror("Name or service not known")

        def mock_socket_fn(*args, **kwargs):
            return mock_socket

        success, message = check_tcp_connectivity(
            "nonexistent.invalid",
            443,
            socket_create_fn=mock_socket_fn
        )

        assert success is False
        assert "dns" in message.lower() or "resolution" in message.lower()


class TestHTTPSEndpoint:
    """Tests for HTTPS endpoint checks."""

    def test_successful_https_request(self):
        """Test successful HTTPS GET request."""
        mock_response = MagicMock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_response.getcode.return_value = 200

        def mock_urlopen(url, timeout=None):
            return mock_response

        success, message = check_https_endpoint(
            "api.example.com",
            "/health",
            urlopen_fn=mock_urlopen
        )

        assert success is True
        assert "200" in message

    def test_https_request_with_path_without_slash(self):
        """Test HTTPS request with path not starting with /."""
        mock_response = MagicMock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_response.getcode.return_value = 200

        calls = []
        def mock_urlopen(url, timeout=None):
            calls.append(url)
            return mock_response

        success, message = check_https_endpoint(
            "api.example.com",
            "status",  # No leading slash
            urlopen_fn=mock_urlopen
        )

        assert success is True
        assert calls[0] == "https://api.example.com/status"

    def test_https_request_non_2xx_status(self):
        """Test HTTPS request returning non-2xx status."""
        mock_response = MagicMock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_response.getcode.return_value = 503

        def mock_urlopen(url, timeout=None):
            return mock_response

        success, message = check_https_endpoint(
            "api.example.com",
            "/health",
            urlopen_fn=mock_urlopen
        )

        assert success is False
        assert "503" in message

    def test_https_request_http_error(self):
        """Test HTTPS request with HTTP error."""
        def mock_urlopen(url, timeout=None):
            raise urllib.error.HTTPError(url, 404, "Not Found", {}, None)

        success, message = check_https_endpoint(
            "api.example.com",
            "/missing",
            urlopen_fn=mock_urlopen
        )

        assert success is False
        assert "404" in message

    def test_https_request_url_error(self):
        """Test HTTPS request with URL error."""
        def mock_urlopen(url, timeout=None):
            raise urllib.error.URLError("Connection refused")

        success, message = check_https_endpoint(
            "api.example.com",
            "/health",
            urlopen_fn=mock_urlopen
        )

        assert success is False
        assert "failed" in message.lower()

    def test_https_request_timeout(self):
        """Test HTTPS request timeout."""
        def mock_urlopen(url, timeout=None):
            raise socket.timeout()

        success, message = check_https_endpoint(
            "slow-api.example.com",
            "/health",
            urlopen_fn=mock_urlopen
        )

        assert success is False
        assert "timeout" in message.lower()


class TestPerformHealthcheck:
    """Tests for complete healthcheck orchestration."""

    def test_healthcheck_tcp_only_success(self, sample_service_tcp_only):
        """Test healthcheck with TCP only - success."""
        mock_socket = MagicMock()
        mock_socket.__enter__ = Mock(return_value=mock_socket)
        mock_socket.__exit__ = Mock(return_value=False)
        mock_socket.connect_ex.return_value = 0

        def mock_socket_fn(*args, **kwargs):
            return mock_socket

        result = perform_healthcheck(
            sample_service_tcp_only,
            socket_create_fn=mock_socket_fn
        )

        assert result.tcp_success is True
        assert result.https_success is None
        assert result.is_healthy is True

    def test_healthcheck_tcp_only_failure(self, sample_service_tcp_only):
        """Test healthcheck with TCP only - failure."""
        mock_socket = MagicMock()
        mock_socket.__enter__ = Mock(return_value=mock_socket)
        mock_socket.__exit__ = Mock(return_value=False)
        mock_socket.connect_ex.return_value = 111

        def mock_socket_fn(*args, **kwargs):
            return mock_socket

        result = perform_healthcheck(
            sample_service_tcp_only,
            socket_create_fn=mock_socket_fn
        )

        assert result.tcp_success is False
        assert result.https_success is None
        assert result.is_healthy is False

    def test_healthcheck_with_https_both_success(self, sample_service_with_https):
        """Test healthcheck with HTTPS - both TCP and HTTPS succeed."""
        mock_socket = MagicMock()
        mock_socket.__enter__ = Mock(return_value=mock_socket)
        mock_socket.__exit__ = Mock(return_value=False)
        mock_socket.connect_ex.return_value = 0

        def mock_socket_fn(*args, **kwargs):
            return mock_socket

        mock_response = MagicMock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_response.getcode.return_value = 200

        def mock_urlopen(url, timeout=None):
            return mock_response

        result = perform_healthcheck(
            sample_service_with_https,
            socket_create_fn=mock_socket_fn,
            urlopen_fn=mock_urlopen
        )

        assert result.tcp_success is True
        assert result.https_success is True
        assert result.is_healthy is True

    def test_healthcheck_with_https_tcp_fails(self, sample_service_with_https):
        """Test healthcheck with HTTPS - TCP fails, HTTPS not attempted."""
        mock_socket = MagicMock()
        mock_socket.__enter__ = Mock(return_value=mock_socket)
        mock_socket.__exit__ = Mock(return_value=False)
        mock_socket.connect_ex.return_value = 111

        def mock_socket_fn(*args, **kwargs):
            return mock_socket

        result = perform_healthcheck(
            sample_service_with_https,
            socket_create_fn=mock_socket_fn
        )

        assert result.tcp_success is False
        assert result.https_success is None  # Not attempted
        assert result.is_healthy is False

    def test_healthcheck_with_https_only_https_fails(self, sample_service_with_https):
        """Test healthcheck with HTTPS - TCP succeeds but HTTPS fails."""
        mock_socket = MagicMock()
        mock_socket.__enter__ = Mock(return_value=mock_socket)
        mock_socket.__exit__ = Mock(return_value=False)
        mock_socket.connect_ex.return_value = 0

        def mock_socket_fn(*args, **kwargs):
            return mock_socket

        def mock_urlopen(url, timeout=None):
            raise urllib.error.HTTPError(url, 500, "Internal Server Error", {}, None)

        result = perform_healthcheck(
            sample_service_with_https,
            socket_create_fn=mock_socket_fn,
            urlopen_fn=mock_urlopen
        )

        assert result.tcp_success is True
        assert result.https_success is False
        assert result.is_healthy is False
