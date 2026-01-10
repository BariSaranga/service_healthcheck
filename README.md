# Service Healthcheck

[![CI](https://github.com/BariSaranga/service_healthcheck/actions/workflows/ci.yml/badge.svg)](https://github.com/BariSaranga/service_healthcheck/actions)
[![Docker](https://img.shields.io/badge/docker-ghcr.io-blue)](https://github.com/BariSaranga/service_healthcheck/pkgs/container/service_healthcheck)

Production-style CLI tool for checking service health via TCP and optional HTTPS connectivity.

## Features

- **TCP Connectivity Checks**: Verify services are reachable via TCP sockets
- **HTTPS Health Endpoints**: Optional HTTP GET requests to health endpoints
- **Clear Exit Codes**: Machine-readable results for CI/CD integration
- **Structured Logging**: File and console logging with different verbosity levels
- **Configurable Timeouts**: Control TCP and HTTPS timeout behavior
- **Zero Runtime Dependencies**: Uses Python standard library only

## Installation

### From Source

```bash
# Clone the repository
git clone https://github.com/BariSaranga/service_healthcheck.git
cd service_healthcheck

# Install in development mode
pip install -e ".[dev]"
```

### For Development

```bash
# Install with development dependencies (pytest, coverage, etc.)
pip install -e ".[dev]"
```

## Usage

### Basic Usage

Check a single service with TCP only:

```bash
service-healthcheck db:localhost:5432
```

Check multiple services:

```bash
service-healthcheck db:localhost:5432 cache:localhost:6379 api:localhost:8080
```

### With HTTPS Health Endpoints

Check TCP connectivity and make HTTPS GET request:

```bash
service-healthcheck api:api.example.com:443:/health
```

Multiple services with mixed configurations:

```bash
service-healthcheck \
  db:postgres.local:5432 \
  api:api.example.com:443:/health \
  cache:redis.local:6379
```

### Service Format

Services are specified in the format:

```
name:host:port[:https_path]
```

- `name`: Human-readable service identifier
- `host`: Hostname or IP address
- `port`: TCP port number (1-65535)
- `https_path`: Optional path for HTTPS GET request (e.g., `/health`, `/status`)

### Command-Line Options

```bash
service-healthcheck [OPTIONS] SERVICE [SERVICE ...]
```

**Options:**

- `--log-file PATH`: Path to log file (default: `./healthcheck.log`)
- `--tcp-timeout SECONDS`: TCP connection timeout (default: 5.0)
- `--https-timeout SECONDS`: HTTPS request timeout (default: 10.0)
- `--verbose`: Enable verbose output (DEBUG level)
- `-h, --help`: Show help message

### Examples

**Custom log file location:**

```bash
service-healthcheck db:localhost:5432 --log-file /var/log/healthcheck.log
```

**Adjust timeouts for slow networks:**

```bash
service-healthcheck api:slow-api.com:443:/health \
  --tcp-timeout 10.0 \
  --https-timeout 30.0
```

**Verbose output for debugging:**

```bash
service-healthcheck db:localhost:5432 --verbose
```

**Multiple services with various configurations:**

```bash
service-healthcheck \
  primary-db:db1.prod.local:5432 \
  replica-db:db2.prod.local:5432 \
  api-gateway:api.prod.local:443:/v1/health \
  cache:cache.prod.local:6379 \
  message-queue:mq.prod.local:5672 \
  --log-file /var/log/prod-healthcheck.log
```

## Exit Codes

The tool uses standard exit codes for easy integration with scripts and CI/CD pipelines:

- **0**: All services are healthy
- **2**: Partial or complete failure (one or more services unhealthy)
- **3**: Execution or configuration error (invalid arguments, unexpected exceptions)

### Using Exit Codes in Scripts

```bash
#!/bin/bash

service-healthcheck db:localhost:5432 api:localhost:8080

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "All services healthy - deploying application"
    ./deploy.sh
elif [ $EXIT_CODE -eq 2 ]; then
    echo "Some services unhealthy - aborting deployment"
    exit 1
else
    echo "Healthcheck failed to run - check configuration"
    exit 1
fi
```

## Logging

The tool provides dual logging outputs:

### Console Output (stdout)

INFO level and above by default. Use `--verbose` for DEBUG level.

```
INFO: Starting health check for service: db
INFO: Service db is healthy
INFO: Health Check Summary
INFO: db: HEALTHY
INFO: Total: 1/1 healthy
INFO: Result: All services healthy
```

### File Output (healthcheck.log)

Detailed logging with timestamps, severity levels, and full messages:

```
2026-01-06 10:30:00 - service_healthcheck - INFO - Starting health check for service: db
2026-01-06 10:30:00 - service_healthcheck - DEBUG - TCP connection successful to localhost:5432
2026-01-06 10:30:00 - service_healthcheck - INFO - Service db is healthy
```

## Running as a Module

You can also run the tool as a Python module:

```bash
python -m service_healthcheck db:localhost:5432
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/BariSaranga/service_healthcheck.git
cd service_healthcheck

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install with dev dependencies
pip install -e ".[dev]"
```

### Running Tests

```bash
# Run all tests with coverage
pytest

# Run specific test file
pytest tests/test_healthcheck.py

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=service_healthcheck --cov-report=html
```

### Test Coverage

The project aims for high test coverage with comprehensive unit and integration tests:

- Core healthcheck logic with mocked network calls
- CLI argument parsing and validation
- Exit code determination for all scenarios
- Error handling and edge cases

View coverage report:

```bash
pytest --cov=service_healthcheck --cov-report=html
open htmlcov/index.html  # On macOS
```

### Project Structure

```
service_healthcheck/
├── .github/
│   └── workflows/
│       └── ci.yml              # GitHub Actions CI configuration
├── src/
│   └── service_healthcheck/
│       ├── __init__.py         # Package initialization
│       ├── __main__.py         # Entry point for -m execution
│       ├── cli.py              # CLI argument parsing and orchestration
│       ├── healthcheck.py      # Core TCP and HTTPS check logic
│       ├── logging_config.py   # Logging configuration
│       └── models.py           # Data models (ServiceConfig, HealthCheckResult)
├── tests/
│   ├── conftest.py             # Shared pytest fixtures
│   ├── test_healthcheck.py     # Tests for core health check logic
│   ├── test_cli.py             # Tests for CLI functionality
│   └── test_exit_codes.py      # Tests for exit code logic
├── .gitignore
├── pyproject.toml              # Project configuration
└── README.md
```

## CI/CD Integration

The project includes a GitHub Actions workflow that:

- Runs on push and pull requests
- Uses Python 3.13 on ubuntu-latest
- Caches pip dependencies for faster builds
- Runs the full test suite
- Uploads coverage reports as artifacts

### Using in CI/CD Pipelines

**GitHub Actions example:**

```yaml
- name: Health check services
  run: |
    pip install -e .
    service-healthcheck \
      db:postgres:5432 \
      api:api.staging.local:443:/health

- name: Deploy if healthy
  if: success()
  run: ./deploy.sh
```

**GitLab CI example:**

```yaml
health_check:
  script:
    - pip install -e .
    - service-healthcheck db:postgres:5432 api:localhost:8080:/health
  only:
    - main
```

## Requirements

- Python >= 3.13
- No external runtime dependencies (uses stdlib only)

### Development Requirements

- pytest >= 7.4.0
- pytest-cov >= 4.1.0
- pytest-mock >= 3.11.0

## License

This project is part of the DevOps Learning Lab.

## Contributing

Contributions are welcome! Please ensure:

1. All tests pass: `pytest`
2. Code follows project style
3. New features include tests
4. Documentation is updated

## Troubleshooting

### Common Issues

**"Connection refused" errors:**
- Verify the service is running
- Check firewall rules
- Ensure correct host and port

**HTTPS certificate errors:**
- The tool uses standard Python SSL verification
- For self-signed certificates, you may need to configure SSL context

**Timeout issues:**
- Increase timeout values with `--tcp-timeout` and `--https-timeout`
- Check network connectivity
- Verify DNS resolution

### Debug Mode

Use `--verbose` flag for detailed logging:

```bash
service-healthcheck db:localhost:5432 --verbose
```

This enables DEBUG-level logging to both console and log file.
