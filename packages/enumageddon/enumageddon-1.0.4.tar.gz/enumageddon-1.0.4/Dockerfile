# Use official Python runtime as base image
FROM python:3.11-slim

# Set working directory in container
WORKDIR /app

# Set metadata
LABEL maintainer="Not-4O4"
LABEL description="Enumageddon - Web Fuzzer & Cloud Enumeration Tool"

# Copy requirements first for better caching
COPY requirements.txt .

# Install system dependencies and Python packages
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    git \
    curl \
    && rm -rf /var/lib/apt/lists/* && \
    pip install --no-cache-dir -r requirements.txt

# Copy the entire project
COPY . .

# Install enumageddon in development mode
RUN pip install --no-cache-dir -e .

# Create a non-root user
RUN useradd -m -u 1000 enumageddon && \
    chown -R enumageddon:enumageddon /app

# Switch to non-root user
USER enumageddon

# Set the entry point
ENTRYPOINT ["enumageddon"]

# Default command shows help
CMD ["--help"]
