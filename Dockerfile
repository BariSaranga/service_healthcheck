# Base image with Python runtime
FROM python:3.13-slim

# Metadata labels
LABEL maintainer="barisaranga@gmail.com"
LABEL description="Production-style service healthcheck CLI tool"
LABEL version="1.0.0"

# Prevent Python from writing .pyc files and force stdout/stderr unbuffered
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Create a non-root user for security
RUN useradd -m -u 1000 appuser

# Workdir inside container
WORKDIR /app

# Copy only dependency metadata first (better caching)
COPY pyproject.toml README.md ./

# Copy source code (required for installation)
COPY src ./src

# Install the package (runtime only, no dev dependencies)
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# Switch to non-root
USER appuser

# Create directory for logs with proper permissions
RUN mkdir -p /home/appuser/logs

# Default working directory for non-root user
WORKDIR /home/appuser

# Default command
ENTRYPOINT ["service-healthcheck"]
CMD ["--help"]
