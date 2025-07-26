#!/bin/bash

# Personal AI Assistant Setup Script
# Application-specific dependencies only

set -e  # Exit on any error

echo "🚀 Personal AI Assistant Setup"
echo "==============================="
echo "Installing application dependencies only..."
echo ""

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Signal CLI is installed inside the Docker container - no host installation needed

# Function to install Ollama
install_ollama() {
    echo "🤖 Installing Ollama..."
    
    # Download and install Ollama
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # Start Ollama service
    sudo systemctl enable ollama
    sudo systemctl start ollama
    
    echo "✅ Ollama installed successfully"
}

# Function to pull Ollama model
pull_ollama_model() {
    echo "📥 Pulling Qwen2.5:14b model..."
    echo "This may take a while (~8GB download)..."
    
    if ollama pull qwen2.5:14b; then
        echo "✅ Qwen2.5:14b model downloaded"
        return 0
    else
        echo "❌ Failed to download Qwen2.5:14b model"
        echo "You can download it later with: ollama pull qwen2.5:14b"
        return 1
    fi
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
    echo "📁 Creating application directories..."
    
    mkdir -p logs
    mkdir -p data/postgres
    mkdir -p data/chroma
    
    echo "✅ Application directories created"
}

# Main setup process
main() {
    echo "Checking prerequisites..."
    echo ""
    
    # Check if Docker is available
    if ! command_exists docker; then
        echo "❌ Docker not found. Please install Docker first:"
        echo "   curl -fsSL https://get.docker.com -o get-docker.sh"
        echo "   sh get-docker.sh"
        echo "   sudo usermod -aG docker \$USER"
        echo "   # Then logout and login again"
        exit 1
    else
        echo "✅ Docker found"
    fi
    
    # Check Docker Compose
    if ! docker compose version >/dev/null 2>&1; then
        echo "❌ Docker Compose not available"
        exit 1
    else
        echo "✅ Docker Compose found"
    fi
    
    echo ""
    
    # Signal CLI runs inside Docker container
    echo "✅ Signal CLI will be available inside Docker container"
    
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
        echo "📥 Qwen2.5:14b model not found. Downloading..."
        pull_ollama_model
    else
        echo "✅ Qwen2.5:14b model already available"
    fi
    
    # Setup environment and directories
    setup_environment
    create_directories
    
    echo ""
    echo "🎉 Application setup complete!"
    echo ""
    echo "✅ Signal CLI ready inside Docker container"
    echo "✅ Ollama configured and running"
    echo "✅ Environment configured"
    echo "✅ Application directories created"
    echo ""
    echo "Next steps:"
    echo ""
    echo "1. Start application containers:"
    echo "   docker compose up -d"
    echo ""
    echo "2. Link Signal device (inside container):"
    echo "   docker exec -it assistant-api signal-cli link -n \"AI Assistant\""
    echo "   # Scan QR code with Signal app"
    echo ""
    echo "3. Test Signal connection (inside container):"
    echo "   docker exec -it assistant-api signal-cli -a \$(grep SIGNAL_PHONE_NUMBER .env | cut -d= -f2) send \$(grep SIGNAL_PHONE_NUMBER .env | cut -d= -f2) -m \"Test\""
    echo ""
    echo "4. Check health:"
    echo "   curl http://localhost:8080/health"
    echo ""
    echo "For management:"
    echo "- View logs: docker compose logs -f"
    echo "- Stop: docker compose down"
    echo "- Restart: docker compose restart"
    echo ""
}

# Run main function
main "$@"