#!/bin/bash

# RovoDev Setup Script
# Ubuntu Server 24.04.2 LTS - Automated Installation

set -e  # Exit on any error

echo "🚀 RovoDev Setup - Ubuntu 24.04.2 LTS"
echo "====================================="

# Check Ubuntu version
if [[ ! -f /etc/lsb-release ]] || ! grep -q "Ubuntu" /etc/lsb-release; then
    echo "⚠️  Warning: This script is designed for Ubuntu. Proceed with caution on other systems."
    exit 1
fi

# Check for Ubuntu 24.04
UBUNTU_VERSION=$(lsb_release -rs)
if [[ "$UBUNTU_VERSION" != "24.04" ]]; then
    echo "⚠️  Warning: This script is optimized for Ubuntu 24.04. You have $UBUNTU_VERSION"
    read -p "Continue anyway? (y/N): " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi


# Function to configure security
configure_security() {
    echo "🔒 Configuring basic security..."
    
    # Configure UFW firewall
    sudo ufw default deny incoming
    sudo ufw default allow outgoing
    sudo ufw allow ssh
    sudo ufw allow 8080  # FastAPI
    sudo ufw --force enable
    
    # Configure fail2ban
    sudo systemctl enable fail2ban
    sudo systemctl start fail2ban
    
    echo "✅ Security configured successfully"
}

# Function to install Docker (Ubuntu 24.04 compatible)
install_docker() {
    echo "📦 Installing Docker..."
    
    # Remove old Docker versions
    sudo apt remove -y docker docker-engine docker.io containerd runc 2>/dev/null || true
    
    # Add Docker's official GPG key
    sudo mkdir -p /etc/apt/keyrings
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    
    # Set up repository (Ubuntu 24.04 compatible)
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
        $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # Install Docker Engine
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
    
    # Configure Docker daemon
    sudo mkdir -p /etc/docker
    sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2"
}
EOF
    
    # Add current user to docker group
    sudo usermod -aG docker $USER
    
    # Enable and start Docker
    sudo systemctl enable docker
    sudo systemctl start docker
    
    echo "✅ Docker installed successfully"
}

# Function to install Signal CLI
install_signal_cli() {
    echo "📱 Installing Signal CLI..."
    
    # Install Java (required for signal-cli)
    sudo apt install -y openjdk-17-jre
    
    # Download and install signal-cli
    cd /tmp
    SIGNAL_CLI_VERSION="0.12.8"
    wget "https://github.com/AsamK/signal-cli/releases/download/v${SIGNAL_CLI_VERSION}/signal-cli-${SIGNAL_CLI_VERSION}.tar.gz"
    tar xf signal-cli-*.tar.gz
    sudo mv signal-cli-* /opt/signal-cli
    sudo ln -sf /opt/signal-cli/bin/signal-cli /usr/local/bin/
    
    # Verify installation
    if command_exists signal-cli; then
        echo "✅ Signal CLI installed successfully"
        echo "📱 Version: $(signal-cli --version)"
    else
        echo "❌ Signal CLI installation failed"
        exit 1
    fi
}

# Function to install Ollama
install_ollama() {
    echo "🤖 Installing Ollama..."
    
    # Download and install Ollama
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # Configure Ollama for 32GB RAM system
    sudo mkdir -p /etc/systemd/system/ollama.service.d
    sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
Environment="OLLAMA_FLASH_ATTENTION=1"
EOF
    
    # Reload systemd and start Ollama
    sudo systemctl daemon-reload
    sudo systemctl enable ollama
    sudo systemctl start ollama
    
    echo "✅ Ollama installed successfully"
}

# Function to pull Ollama model
pull_ollama_model() {
    echo "📥 Pulling Qwen2.5:14b model..."
    
    # This may take a while (several GB download)
    if ollama pull qwen2.5:14b; then
        echo "✅ Qwen2.5:14b model downloaded"
        return 0
    else
        echo "❌ Failed to download Qwen2.5:14b model"
        return 1
    fi
}

# Function to optimize system for 32GB RAM
optimize_system() {
    echo "⚡ Optimizing system for 32GB RAM..."
    
    # Configure swap (4GB for safety)
    if [[ ! -f /swapfile ]]; then
        sudo fallocate -l 4G /swapfile
        sudo chmod 600 /swapfile
        sudo mkswap /swapfile
        sudo swapon /swapfile
        echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
    fi
    
    # Configure swappiness for high-RAM system
    echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
    
    # Configure file limits
    echo '* soft nofile 65536' | sudo tee -a /etc/security/limits.conf
    echo '* hard nofile 65536' | sudo tee -a /etc/security/limits.conf
    
    # Apply sysctl changes
    sudo sysctl -p
    
    echo "✅ System optimization complete"
}

# Function to setup Signal linking
setup_signal_linking() {
    echo "📱 Setting up Signal device linking..."
    echo ""
    echo "🔗 To link your server as a Signal device:"
    echo ""
    echo "1. First, add your phone number to .env file"
    echo "2. Then run: signal-cli link -n \"AI Assistant Server\""
    echo "3. Scan the QR code with your Signal app"
    echo "4. Go to Signal Settings → Linked devices → Link New Device"
    echo ""
    echo "⚠️  IMPORTANT: You must complete Signal linking before starting the application!"
    echo ""
}

# Function to prompt for Signal phone number
prompt_signal_phone() {
    echo "📱 Signal Phone Number Configuration"
    echo ""
    echo "Please enter your Signal phone number (including country code):"
    echo "Example: +1234567890"
    echo ""
    
    while true; do
        read -p "Signal phone number: " SIGNAL_PHONE_NUMBER
        
        # Validate phone number format
        if [[ $SIGNAL_PHONE_NUMBER =~ ^\+[1-9][0-9]{9,14}$ ]]; then
            echo "✅ Valid phone number format: $SIGNAL_PHONE_NUMBER"
            break
        else
            echo "❌ Invalid format. Please use format: +1234567890 (country code + number)"
            echo "   - Must start with +"
            echo "   - Must be 10-15 digits after country code"
            echo ""
        fi
    done
    
    # Export for use in calling function
    export SIGNAL_PHONE_NUMBER
    return 0
}

# Function to setup environment file
setup_environment() {
    echo "⚙️  Setting up environment configuration..."
    
    if [[ ! -f .env ]]; then
        cp .env.example .env
        echo "📝 Created .env file from template"
        echo ""
        
        # Prompt for Signal phone number
        prompt_signal_phone
        
        # Update .env file with phone number
        sed -i "s/SIGNAL_PHONE_NUMBER=+1234567890/SIGNAL_PHONE_NUMBER=$SIGNAL_PHONE_NUMBER/" .env
        echo "✅ Signal phone number configured in .env"
        
        # Generate secure postgres password
        postgres_password=$(openssl rand -base64 32 | tr -d "=+/" | cut -c1-25)
        sed -i "s/your_secure_postgres_password/$postgres_password/g" .env
        echo "✅ Generated secure PostgreSQL password"
        
        echo ""
        echo "📝 Environment file configured with:"
        echo "   - Signal phone number: $SIGNAL_PHONE_NUMBER"
        echo "   - PostgreSQL password: [generated]"
        echo ""
        echo "Optional: You can add these later:"
        echo "   - NOTION_TOKEN=... (for Notion integration)"
        echo "   - Note: Gmail integration removed - using Signal 'Note to Self' only"
        echo ""
        
    else
        echo "📝 .env file already exists"
        
        # Check if Signal phone number is configured
        if ! grep -q "SIGNAL_PHONE_NUMBER=+" .env 2>/dev/null; then
            echo "⚠️  Signal phone number not configured. Let's set it up:"
            prompt_signal_phone
            
            # Update existing .env file
            if grep -q "SIGNAL_PHONE_NUMBER=" .env; then
                sed -i "s/SIGNAL_PHONE_NUMBER=.*/SIGNAL_PHONE_NUMBER=$SIGNAL_PHONE_NUMBER/" .env
            else
                echo "SIGNAL_PHONE_NUMBER=$SIGNAL_PHONE_NUMBER" >> .env
            fi
            echo "✅ Signal phone number updated in .env"
        else
            echo "✅ Signal phone number already configured"
        fi
    fi
}

# Function to create necessary directories
create_directories() {
    echo "📁 Creating necessary directories..."
    
    mkdir -p logs
    mkdir -p data/postgres
    mkdir -p data/chroma
    
    echo "✅ Directories created"
}

# Function to create monitoring tools
setup_monitoring() {
    echo "📊 Setting up monitoring tools..."
    
    # Create system monitor script
    tee ~/system-monitor.sh > /dev/null <<'EOF'
#!/bin/bash
echo "=== RovoDev System Monitor ==="
echo "Memory Usage:"
free -h
echo ""
echo "Disk Usage:"
df -h
echo ""
echo "Docker Containers:"
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
echo ""
echo "Ollama Status:"
systemctl is-active ollama
echo ""
echo "Top Memory Processes:"
ps aux --sort=-%mem | head -10
echo ""
echo "RovoDev Health Check:"
curl -s http://localhost:8080/health 2>/dev/null || echo "FastAPI not responding"
curl -s http://localhost:8000/api/v1/heartbeat 2>/dev/null || echo "ChromaDB not responding"
curl -s http://localhost:11434/api/tags 2>/dev/null || echo "Ollama not responding"
echo ""
echo "Signal Status:"
signal-cli --version 2>/dev/null || echo "Signal CLI not available"
EOF
    
    chmod +x ~/system-monitor.sh
    
    echo "✅ Monitoring tools created"
}

# Main setup process
main() {
    echo "Starting RovoDev setup process for Ubuntu 24.04.2 LTS..."
    echo ""
    
    # Check system requirements
    echo "🔍 Checking system requirements..."
    
    # Check available RAM
    total_ram=$(free -g | awk '/^Mem:/{print $2}')
    if [[ $total_ram -lt 16 ]]; then
        echo "⚠️  Warning: System has ${total_ram}GB RAM. Recommended: 32GB for optimal performance."
    else
        echo "✅ RAM: ${total_ram}GB (Excellent)"
    fi
    
    # Check available disk space
    available_space=$(df -BG . | awk 'NR==2 {print $4}' | sed 's/G//')
    if [[ $available_space -lt 50 ]]; then
        echo "⚠️  Warning: Available disk space: ${available_space}GB. Recommended: 50GB+"
    else
        echo "✅ Disk space: ${available_space}GB (Good)"
    fi
    
    echo ""
      
    # Configure security
    configure_security
    
    # Install Docker if not present
    if ! command_exists docker; then
        install_docker
        echo "⚠️  Please log out and log back in for Docker group changes to take effect"
        echo "   Then run this script again to continue setup"
        exit 0
    else
        echo "✅ Docker already installed"
    fi
    
    # Verify Docker Compose
    if docker compose version >/dev/null 2>&1; then
        echo "✅ Docker Compose available"
    else
        echo "❌ Docker Compose not working properly"
        exit 1
    fi
    
    # Install Signal CLI if not present
    if ! command_exists signal-cli; then
        install_signal_cli
    else
        echo "✅ Signal CLI already installed"
        echo "📱 Version: $(signal-cli --version)"
    fi
    
    # Install Ollama if not present
    if ! command_exists ollama; then
        install_ollama
    else
        echo "✅ Ollama already installed"
    fi
    
    # Check if Ollama is running
    if ! systemctl is-active --quiet ollama; then
        echo "🔄 Starting Ollama service..."
        sudo systemctl start ollama
    fi
    
    # Pull Ollama model
    echo "🤖 Checking Ollama model..."
    if ! ollama list | grep -q "qwen2.5:14b"; then
        echo "📥 Qwen2.5:14b model not found. Downloading automatically (~8GB)..."
        if pull_ollama_model; then
            echo "✅ Qwen2.5:14b model downloaded successfully"
        else
            echo "❌ Failed to download Ollama model. You can download it later with: ollama pull qwen2.5:14b"
        fi
    else
        echo "✅ Qwen2.5:14b model already available"
    fi
    
    # Optimize system for 32GB RAM
    optimize_system
    
    # Setup environment and directories
    setup_environment
    create_directories
    
    # Setup Signal linking instructions
    setup_signal_linking
    
    # Setup monitoring tools
    setup_monitoring
    
    # Test Docker setup
    echo "🧪 Testing Docker setup..."
    if docker run --rm hello-world >/dev/null 2>&1; then
        echo "✅ Docker test successful"
    else
        echo "❌ Docker test failed. Please check Docker installation"
        exit 1
    fi
    
    # Validate final configuration
    echo "🔍 Validating configuration..."
    if [[ -f .env ]]; then
        if grep -q "SIGNAL_PHONE_NUMBER=+" .env && grep -q "POSTGRES_PASSWORD=" .env; then
            echo "✅ Environment configuration valid"
        else
            echo "❌ Environment configuration incomplete"
            exit 1
        fi
    else
        echo "❌ .env file not found"
        exit 1
    fi
    
    # Final system check
    echo ""
    echo "🔍 Final system verification..."
    echo "Docker version: $(docker --version)"
    echo "Docker Compose version: $(docker compose version --short)"
    echo "Signal CLI version: $(signal-cli --version 2>/dev/null || echo 'Not available')"
    echo "Ollama status: $(systemctl is-active ollama)"
    echo "Available models: $(ollama list 2>/dev/null | wc -l) models"
    
    echo ""
    echo "🎉 Ubuntu 24.04.2 LTS setup complete for RovoDev!"
    echo ""
    echo "✅ System optimized for 32GB RAM"
    echo "✅ Docker and Docker Compose installed"
    echo "✅ Signal CLI installed and ready"
    echo "✅ Ollama configured and running"
    echo "✅ Security hardening applied"
    echo "✅ Monitoring tools available"
    echo ""
    echo "Next steps:"
    echo "1. Edit .env file with your phone number:"
    echo "   nano .env"
    echo "   # Set SIGNAL_PHONE_NUMBER=+1234567890"
    echo ""
    echo "2. Link Signal device:"
    echo "   signal-cli link -n \"AI Assistant Server\""
    echo "   # Scan QR code with Signal app"
    echo ""
    echo "3. Test Signal connection:"
    echo "   signal-cli -a \$(grep SIGNAL_PHONE_NUMBER .env | cut -d= -f2) send \$(grep SIGNAL_PHONE_NUMBER .env | cut -d= -f2) -m \"Test\""
    echo ""
    echo "4. Start RovoDev containers:"
    echo "   docker compose up -d"
    echo ""
    echo "5. Check system health:"
    echo "   ./system-monitor.sh"
    echo ""
    echo "6. Test endpoints:"
    echo "   curl http://localhost:8080/health"
    echo "   curl http://localhost:8080/signal/status"
    echo ""
    echo "For ongoing management:"
    echo "- Monitor: ~/system-monitor.sh"
    echo "- Logs: docker compose logs -f"
    echo "- Stop: docker compose down"
    echo "- Restart: docker compose restart"
    echo ""
    echo "⚠️  IMPORTANT NOTES:"
    echo "- Please logout and login again for Docker group changes to take effect!"
    echo "- Signal CLI must be linked in BOTH host and container:"
    echo "  1. Link on host: signal-cli link -n \"Host Device\""
    echo "  2. Link in container: docker exec -it assistant-api signal-cli link -n \"Container Device\""
    echo "- Both will need separate QR code scans with your Signal app"
    echo ""
}

# Run main function
main "$@"