FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies including Java for Signal CLI
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    openjdk-17-jre \
    wget \
    && rm -rf /var/lib/apt/lists/*

# Install Signal CLI
RUN cd /tmp && \
    SIGNAL_CLI_VERSION="0.12.8" && \
    wget "https://github.com/AsamK/signal-cli/releases/download/v${SIGNAL_CLI_VERSION}/signal-cli-${SIGNAL_CLI_VERSION}.tar.gz" && \
    tar xf signal-cli-*.tar.gz && \
    mv signal-cli-* /opt/signal-cli && \
    ln -sf /opt/signal-cli/bin/signal-cli /usr/local/bin/ && \
    rm -rf /tmp/signal-cli-*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create logs directory
RUN mkdir -p logs

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=5 \
    CMD curl -f http://localhost:8080/health || exit 1

# Run the application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8080", "--reload"]