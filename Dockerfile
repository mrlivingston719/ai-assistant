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

# Install Signal CLI with error checking
RUN cd /tmp && \
    echo "Downloading Signal CLI..." && \
    wget https://github.com/AsamK/signal-cli/releases/download/v0.13.18/signal-cli-0.13.18.tar.gz && \
    echo "Extracting Signal CLI..." && \
    tar xf signal-cli-0.13.18.tar.gz && \
    echo "Installing Signal CLI to /opt/signal-cli..." && \
    mkdir -p /opt && \
    mv signal-cli-0.13.18 /opt/signal-cli && \
    echo "Creating symlink..." && \
    ln -sf /opt/signal-cli/bin/signal-cli /usr/local/bin/signal-cli && \
    echo "Verifying installation..." && \
    ls -la /opt/signal-cli/bin/ && \
    /opt/signal-cli/bin/signal-cli --version && \
    echo "Cleaning up..." && \
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