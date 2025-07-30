# Ubuntu Server 24.04.2 LTS Setup Guide for RovoDev

*Complete configuration guide for fresh Ubuntu Server installation*

## Prerequisites

- **Hardware**: Micro PC with 32GB RAM
- **OS**: Ubuntu Server 24.04.2 LTS (fresh install)
- **Network**: Internet connection for downloads
- **Access**: SSH access or direct console

## Phase 1: Initial System Configuration

### 1.1 System Updates and Security

```bash
# Update package lists and upgrade system
sudo apt update && sudo apt upgrade -y

# Install essential packages
sudo apt install -y \
    curl \
    wget \
    git \
    vim \
    htop \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release \
    ufw \
    fail2ban

# Check system info
lsb_release -a
free -h
df -h
```

### 1.2 User Configuration

```bash
# Add your user to sudo group (if not already)
sudo usermod -aG sudo $USER

# Create rovodev directory
mkdir -p ~/rovodev
cd ~/rovodev

# Set up SSH key (if using SSH)
# ssh-keygen -t ed25519 -C "your_email@example.com"
```

### 1.3 Basic Security Hardening

```bash
# Configure UFW firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 8080  # FastAPI
sudo ufw --force enable

# Configure fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Disable unnecessary services
sudo systemctl disable snapd
sudo systemctl stop snapd
```

## Phase 2: Docker Installation (Ubuntu 24.04 Compatible)

### 2.1 Install Docker Engine

```bash
# Remove old Docker versions
sudo apt remove -y docker docker-engine docker.io containerd runc

# Add Docker's official GPG key
sudo mkdir -p /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

# Add Docker repository (Ubuntu 24.04 compatible)
echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

# Install Docker Engine
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Add user to docker group
sudo usermod -aG docker $USER

# Enable Docker service
sudo systemctl enable docker
sudo systemctl start docker

# Test Docker installation
sudo docker run hello-world
```

### 2.2 Configure Docker for Production

```bash
# Create Docker daemon configuration
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

# Restart Docker
sudo systemctl restart docker

# Verify Docker Compose
docker compose version
```

## Phase 3: Ollama Installation (Native)

### 3.1 Install Ollama

```bash
# Download and install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Create ollama service user (if not created automatically)
sudo useradd -r -s /bin/false -m -d /usr/share/ollama ollama

# Configure Ollama service
sudo systemctl enable ollama
sudo systemctl start ollama

# Check Ollama status
sudo systemctl status ollama
```

### 3.2 Configure Ollama for Performance

```bash
# Create Ollama configuration directory
sudo mkdir -p /etc/systemd/system/ollama.service.d

# Configure Ollama environment for 32GB RAM
sudo tee /etc/systemd/system/ollama.service.d/override.conf > /dev/null <<EOF
[Service]
Environment="OLLAMA_HOST=0.0.0.0:11434"
Environment="OLLAMA_ORIGINS=*"
Environment="OLLAMA_NUM_PARALLEL=4"
Environment="OLLAMA_MAX_LOADED_MODELS=2"
Environment="OLLAMA_FLASH_ATTENTION=1"
EOF

# Reload systemd and restart Ollama
sudo systemctl daemon-reload
sudo systemctl restart ollama

# Test Ollama
curl http://localhost:11434/api/tags
```

### 3.3 Download Qwen2.5-14B Model

```bash
# Pull the model (this will take time - ~8GB download)
ollama pull qwen2.5:14b

# Verify model is available
ollama list

# Test model
ollama run qwen2.5:14b "Hello, how are you?"
```

## Phase 4: System Optimization for RovoDev

### 4.1 Memory and Performance Tuning

```bash
# Configure swap (optional with 32GB RAM, but good for safety)
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make swap permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Configure swappiness for 32GB RAM system
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf

# Configure file limits for Docker and Ollama
echo '* soft nofile 65536' | sudo tee -a /etc/security/limits.conf
echo '* hard nofile 65536' | sudo tee -a /etc/security/limits.conf

# Apply sysctl changes
sudo sysctl -p
```

### 4.2 Network Configuration

```bash
# Configure network for Docker
sudo tee /etc/docker/daemon.json > /dev/null <<EOF
{
  "log-driver": "json-file",
  "log-opts": {
    "max-size": "10m",
    "max-file": "3"
  },
  "storage-driver": "overlay2",
  "default-address-pools": [
    {
      "base": "172.17.0.0/16",
      "size": 24
    }
  ]
}
EOF

# Restart Docker
sudo systemctl restart docker
```

### 4.3 Monitoring Setup

```bash
# Install monitoring tools
sudo apt install -y \
    iotop \
    nethogs \
    ncdu \
    tree

# Create monitoring script
tee ~/system-monitor.sh > /dev/null <<'EOF'
#!/bin/bash
echo "=== System Resources ==="
echo "Memory Usage:"
free -h
echo ""
echo "Disk Usage:"
df -h
echo ""
echo "Docker Containers:"
docker ps
echo ""
echo "Ollama Status:"
systemctl is-active ollama
echo ""
echo "Top Processes:"
ps aux --sort=-%mem | head -10
EOF

chmod +x ~/system-monitor.sh
```

## Phase 5: RovoDev Project Setup

### 5.1 Clone and Setup Project

```bash
# Navigate to project directory
cd ~/rovodev

# If you have the project files, copy them here
# Otherwise, create the structure manually

# Create necessary directories
mkdir -p logs data/postgres data/chroma

# Set proper permissions
chmod 755 logs data data/postgres data/chroma
```

### 5.2 Environment Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit environment file
nano .env

# Required configurations:
# POSTGRES_PASSWORD=your_secure_password
# TELEGRAM_BOT_TOKEN=your_bot_token
# NOTION_TOKEN=your_notion_token
# GMAIL_CREDENTIALS=path_to_credentials
```

### 5.3 Test Container Setup

```bash
# Test Docker Compose
docker compose config

# Start containers in background
docker compose up -d

# Check container status
docker compose ps

# View logs
docker compose logs -f

# Test health endpoints
curl http://localhost:8080/health
curl http://localhost:8000/api/v1/heartbeat  # ChromaDB
```

## Phase 6: Security and Maintenance

### 6.1 Backup Configuration

```bash
# Create backup script
tee ~/backup-rovodev.sh > /dev/null <<'EOF'
#!/bin/bash
BACKUP_DIR="/home/$USER/backups"
DATE=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR

# Backup Docker volumes
docker compose down
sudo tar -czf $BACKUP_DIR/postgres_data_$DATE.tar.gz -C /var/lib/docker/volumes rovodev_postgres_data
sudo tar -czf $BACKUP_DIR/chroma_data_$DATE.tar.gz -C /var/lib/docker/volumes rovodev_chroma_data
docker compose up -d

# Backup configuration
tar -czf $BACKUP_DIR/rovodev_config_$DATE.tar.gz ~/rovodev/.env ~/rovodev/docker-compose.yml

echo "Backup completed: $BACKUP_DIR"
EOF

chmod +x ~/backup-rovodev.sh
```

### 6.2 Automatic Updates

```bash
# Configure automatic security updates
sudo apt install -y unattended-upgrades

# Configure unattended upgrades
sudo dpkg-reconfigure -plow unattended-upgrades
```

### 6.3 Log Rotation

```bash
# Configure log rotation for RovoDev
sudo tee /etc/logrotate.d/rovodev > /dev/null <<EOF
/home/$USER/rovodev/logs/*.log {
    daily
    missingok
    rotate 7
    compress
    delaycompress
    notifempty
    copytruncate
}
EOF
```

## Phase 7: Verification and Testing

### 7.1 System Health Check

```bash
# Run comprehensive health check
~/system-monitor.sh

# Check all services
sudo systemctl status docker
sudo systemctl status ollama
docker compose ps

# Test Ollama
curl -X POST http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model": "qwen2.5:14b", "prompt": "Hello", "stream": false}'

# Test Docker network
docker network ls
docker network inspect rovodev_rovodev-network
```

### 7.2 Performance Baseline

```bash
# Memory usage baseline
free -h

# Disk I/O test
sudo hdparm -Tt /dev/sda  # Adjust device as needed

# Network test
curl -o /dev/null -s -w "Time: %{time_total}s\n" http://localhost:8080/health
```

## Troubleshooting Common Issues

### Docker Permission Issues
```bash
# If Docker permission denied
sudo chmod 666 /var/run/docker.sock
# Or logout and login again after adding to docker group
```

### Ollama Connection Issues
```bash
# Check Ollama logs
sudo journalctl -u ollama -f

# Restart Ollama
sudo systemctl restart ollama
```

### Memory Issues
```bash
# Check memory usage
cat /proc/meminfo
docker stats

# Clear system cache if needed
sudo sync && sudo sysctl vm.drop_caches=3
```

## Next Steps

1. **Run the automated setup script**: `./setup.sh`
2. **Configure API tokens**: Edit `.env` file
3. **Start RovoDev**: `docker compose up -d`
4. **Test functionality**: Use health endpoints and Telegram bot
5. **Monitor performance**: Use `~/system-monitor.sh`

## Resource Allocation Verification

With 32GB RAM, you should see approximately:
- **System/OS**: 4GB
- **Ollama + Qwen2.5-14B**: 12-16GB
- **PostgreSQL**: 2GB
- **ChromaDB**: 2GB
- **FastAPI**: 2-4GB
- **Available**: 6-8GB buffer

---

*This guide is optimized for Ubuntu Server 24.04.2 LTS and the RovoDev 3-container architecture.*