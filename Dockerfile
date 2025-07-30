FROM ubuntu:22.04

# Set working directory
WORKDIR /app

# Install system dependencies and add Eclipse Adoptium repository for OpenJDK 21
RUN apt-get update && apt-get install -y \
    curl \
    gcc \
    python3 \
    python3-pip \
    wget \
    software-properties-common \
    && wget -O - https://packages.adoptium.net/artifactory/api/gpg/public/key | apt-key add - \
    && echo "deb https://packages.adoptium.net/artifactory/deb $(lsb_release -cs) main" | tee /etc/apt/sources.list.d/adoptium.list \
    && apt-get update \
    && apt-get install -y temurin-21-jre \
    && rm -rf /var/lib/apt/lists/*

# Create symlinks for python and pip
RUN ln -sf /usr/bin/python3 /usr/bin/python

# Install Signal CLI with step-by-step error checking
RUN cd /tmp

RUN echo "Downloading Signal CLI..." && \
    wget -v https://github.com/AsamK/signal-cli/releases/download/v0.13.18/signal-cli-0.13.18.tar.gz || \
    (echo "Download failed, trying alternative" && curl -L -o signal-cli-0.13.18.tar.gz https://github.com/AsamK/signal-cli/releases/download/v0.13.18/signal-cli-0.13.18.tar.gz)

RUN echo "Extracting Signal CLI..." && \
    tar -xvf signal-cli-0.13.18.tar.gz && \
    ls -la

RUN echo "Installing Signal CLI to /opt/signal-cli..." && \
    mkdir -p /opt && \
    mv signal-cli-0.13.18 /opt/signal-cli && \
    ls -la /opt/

RUN echo "Creating symlink..." && \
    ln -sf /opt/signal-cli/bin/signal-cli /usr/local/bin/signal-cli && \
    ls -la /usr/local/bin/signal-cli


RUN echo "Cleaning up..." && \
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