"""Shared pytest fixtures for service_healthcheck tests."""

import pytest
from service_healthcheck.models import ServiceConfig


@pytest.fixture
def sample_service_tcp_only():
    """Sample service configuration with TCP only."""
    return ServiceConfig(
        name="test-db",
        host="localhost",
        port=5432,
        https_path=None
    )


@pytest.fixture
def sample_service_with_https():
    """Sample service configuration with HTTPS endpoint."""
    return ServiceConfig(
        name="test-api",
        host="api.example.com",
        port=443,
        https_path="/health"
    )


@pytest.fixture
def sample_services_list():
    """List of sample service configurations."""
    return [
        ServiceConfig(name="db", host="localhost", port=5432),
        ServiceConfig(name="api", host="api.local", port=8080, https_path="/status"),
        ServiceConfig(name="cache", host="redis.local", port=6379),
    ]
