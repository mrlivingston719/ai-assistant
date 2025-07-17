#!/bin/bash

# RovoDev One-Command Deployment Script
# Deploys RovoDev to Ubuntu server via GitHub

set -e  # Exit on any error

echo "🚀 RovoDev One-Command Deployment"
echo "================================="
echo ""

# Check if running on Ubuntu
if [[ ! -f /etc/lsb-release ]] || ! grep -q "Ubuntu" /etc/lsb-release; then
    echo "❌ This script requires Ubuntu. Please use manual deployment for other systems."
    exit 1
fi

# Check Ubuntu version
UBUNTU_VERSION=$(lsb_release -rs)
echo "📋 Detected Ubuntu $UBUNTU_VERSION"

if [[ "$UBUNTU_VERSION" != "24.04" && "$UBUNTU_VERSION" != "22.04" ]]; then
    echo "⚠️  Warning: This script is optimized for Ubuntu 22.04/24.04. You have $UBUNTU_VERSION"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if git is installed
if ! command -v git >/dev/null 2>&1; then
    echo "📦 Installing git..."
    sudo apt update
    sudo apt install -y git curl
fi

# Set deployment directory
DEPLOY_DIR="$HOME/rovodev"
REPO_URL="https://github.com/yourusername/rovodev.git"

echo "📁 Deployment directory: $DEPLOY_DIR"
echo "📡 Repository: $REPO_URL"
echo ""

# Clone or update repository
if [[ -d "$DEPLOY_DIR" ]]; then
    echo "📂 RovoDev directory exists. Updating..."
    cd "$DEPLOY_DIR"
    git pull origin main
else
    echo "📥 Cloning RovoDev repository..."
    git clone "$REPO_URL" "$DEPLOY_DIR"
    cd "$DEPLOY_DIR"
fi

echo "✅ Repository ready"
echo ""

# Run setup script
echo "🔧 Running automated setup..."
chmod +x setup.sh
./setup.sh

echo ""
echo "⚙️  Setup completed. Now configuring environment..."

# Setup environment file
if [[ ! -f .env ]]; then
    cp .env.example .env
    echo "📝 Created .env file from template"
    echo ""
    echo "⚠️  IMPORTANT: You need to configure your API tokens!"
    echo ""
    echo "Required configuration:"
    echo "1. Get Telegram Bot Token from @BotFather"
    echo "2. Set a secure PostgreSQL password"
    echo "3. (Optional) Add Notion and Gmail credentials"
    echo ""
    echo "Edit the .env file now:"
    echo "  nano .env"
    echo ""
    read -p "Press Enter when you've configured .env file..."
else
    echo "📝 .env file already exists"
fi

echo ""
echo "🤖 Downloading AI model (this may take several minutes)..."

# Download Ollama model
if ! ollama list | grep -q "qwen2.5:14b"; then
    echo "📥 Downloading Qwen2.5-14B model (8GB)..."
    ollama pull qwen2.5:14b
    echo "✅ Model downloaded successfully"
else
    echo "✅ Qwen2.5-14B model already available"
fi

echo ""
echo "🐳 Starting Docker containers..."

# Start services
docker compose up -d

# Wait for services to start
echo "⏳ Waiting for services to start..."
sleep 30

echo ""
echo "🧪 Running health checks..."

# Health checks
HEALTH_CHECKS=0

# Check FastAPI
if curl -f http://localhost:8080/health >/dev/null 2>&1; then
    echo "✅ FastAPI: Healthy"
    ((HEALTH_CHECKS++))
else
    echo "❌ FastAPI: Unhealthy"
fi

# Check ChromaDB
if curl -f http://localhost:8000/api/v1/heartbeat >/dev/null 2>&1; then
    echo "✅ ChromaDB: Healthy"
    ((HEALTH_CHECKS++))
else
    echo "❌ ChromaDB: Unhealthy"
fi

# Check Ollama
if curl -f http://localhost:11434/api/tags >/dev/null 2>&1; then
    echo "✅ Ollama: Healthy"
    ((HEALTH_CHECKS++))
else
    echo "❌ Ollama: Unhealthy"
fi

echo ""

if [[ $HEALTH_CHECKS -eq 3 ]]; then
    echo "🎉 Deployment Successful!"
    echo ""
    echo "✅ All services are running and healthy"
    echo "✅ RovoDev is ready to use"
    echo ""
    echo "Next steps:"
    echo "1. Test your Telegram bot by sending a message"
    echo "2. Send a meeting transcript to test processing"
    echo "3. Check system status: ./system-monitor.sh"
    echo ""
    echo "Useful commands:"
    echo "- View logs: docker compose logs -f"
    echo "- Restart: docker compose restart"
    echo "- Stop: docker compose down"
    echo "- Update: git pull && docker compose up -d --build"
    echo ""
    echo "🌐 Access points:"
    echo "- API Health: http://localhost:8080/health"
    echo "- API Status: http://localhost:8080/status"
    echo "- ChromaDB: http://localhost:8000"
    echo "- Ollama: http://localhost:11434"
    
elif [[ $HEALTH_CHECKS -gt 0 ]]; then
    echo "⚠️  Partial Deployment"
    echo ""
    echo "Some services are running, but there may be issues."
    echo "Check logs: docker compose logs -f"
    echo "Check configuration: nano .env"
    echo ""
    echo "Common issues:"
    echo "- Missing API tokens in .env file"
    echo "- Insufficient memory (need 16GB+ RAM)"
    echo "- Ports already in use"
    
else
    echo "❌ Deployment Failed"
    echo ""
    echo "No services are responding. Check:"
    echo "1. Docker is running: docker --version"
    echo "2. Containers started: docker compose ps"
    echo "3. Logs for errors: docker compose logs"
    echo "4. System resources: free -h"
    echo ""
    echo "For help, see: https://github.com/yourusername/rovodev/issues"
fi

echo ""
echo "📊 System Status:"
./system-monitor.sh

echo ""
echo "🔗 Useful Links:"
echo "- Documentation: https://github.com/yourusername/rovodev"
echo "- Issues: https://github.com/yourusername/rovodev/issues"
echo "- Deployment Guide: https://github.com/yourusername/rovodev/blob/main/DEPLOYMENT.md"