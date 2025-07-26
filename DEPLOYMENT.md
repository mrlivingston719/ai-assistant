# RovoDev Deployment Guide

> **Complete guide for deploying RovoDev to any Ubuntu server via GitHub**

## 🎯 Deployment Goal

**Enable seamless deployment to any Ubuntu server via `git clone` + automated setup**

This deployment strategy allows you to:
- Deploy to multiple servers (development, staging, production)
- Quickly set up new instances
- Maintain consistent environments
- Easy updates via `git pull`

## 🚀 One-Command Deployment

### For Ubuntu 24.04 LTS (Recommended)

```bash
# Complete deployment in one command
curl -fsSL https://raw.githubusercontent.com/mrlivingston719/ai-assistant/main/deploy.sh | bash
```

### Manual Deployment Steps

```bash
# 1. Clone repository
git clone https://github.com/mrlivingston719/ai-assistant.git
cd ai-assistant

# 2. Run setup script
chmod +x setup.sh
./setup.sh

# 3. Configure environment
cp .env.example .env
nano .env  # Add your API tokens

# 4. Download AI model
ollama pull qwen2.5:14b

# 5. Start services
docker compose up -d

# 6. Verify deployment
curl http://localhost:8080/health
```

## 🖥️ Server Requirements

### Minimum Requirements
- **OS**: Ubuntu 22.04 LTS or 24.04 LTS
- **RAM**: 16GB (32GB recommended)
- **Storage**: 50GB available space
- **CPU**: 4+ cores
- **Network**: Internet connection for setup

### Recommended Specifications
- **RAM**: 32GB (optimal for Qwen2.5-14B model)
- **Storage**: 100GB+ SSD
- **CPU**: 8+ cores
- **Network**: Stable broadband connection

## 📋 Pre-Deployment Checklist

### 1. Server Access
- [ ] SSH access to Ubuntu server
- [ ] Sudo privileges
- [ ] Internet connectivity

### 2. API Tokens Ready
- [ ] Signal phone number configured
- [ ] Notion Integration Token (optional)
- [ ] Gmail API Credentials (optional)

### 3. Domain/Network Setup (Optional)
- [ ] Domain name configured
- [ ] SSL certificate ready
- [ ] Firewall rules planned

## 🔧 Detailed Deployment Steps

### Step 1: Server Preparation

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install git if not present
sudo apt install -y git curl

# Create deployment user (optional)
sudo useradd -m -s /bin/bash aiassistant
sudo usermod -aG sudo aiassistant
sudo su - aiassistant
```

### Step 2: Clone Repository

```bash
# Clone to home directory
cd ~
git clone https://github.com/mrlivingston719/ai-assistant.git
cd ai-assistant

# Verify files
ls -la
```

### Step 3: Run Automated Setup

```bash
# Make setup script executable
chmod +x setup.sh

# Run setup (installs Docker, Ollama, optimizes system)
./setup.sh

# Logout and login for Docker group changes
exit
# SSH back in
```

### Step 4: Environment Configuration

```bash
cd ~/rovodev

# Copy environment template
cp .env.example .env

# Edit environment file
nano .env
```

**Required Environment Variables:**
```bash
# Database
POSTGRES_PASSWORD=your_secure_password_here

# Signal Integration
SIGNAL_PHONE_NUMBER=+1234567890

# Optional integrations
NOTION_TOKEN=your_notion_token
GMAIL_CREDENTIALS={"type":"service_account",...}

# Application settings
LOG_LEVEL=INFO
DEBUG=False
```

### Step 5: Download AI Model

```bash
# Download Qwen2.5-14B model (8GB download)
ollama pull qwen2.5:14b

# Verify model is available
ollama list
```

### Step 6: Start Services

```bash
# Start all containers
docker compose up -d

# Check container status
docker compose ps

# View logs
docker compose logs -f
```

### Step 7: Verify Deployment

```bash
# Health checks
curl http://localhost:8080/health
curl http://localhost:8000/api/v1/heartbeat
curl http://localhost:11434/api/tags

# Application status
curl http://localhost:8080/status

# System monitoring
./system-monitor.sh
```

## 🌐 Production Deployment

### Reverse Proxy Setup (Nginx)

```bash
# Install nginx
sudo apt install -y nginx

# Create configuration
sudo nano /etc/nginx/sites-available/ai-assistant
```

**Nginx Configuration:**
```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Signal uses local communication - no webhook needed
    # All Signal integration is handled via signal-cli locally
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/ai-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### SSL Certificate (Let's Encrypt)

```bash
# Install certbot
sudo apt install -y certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Firewall Configuration

```bash
# Configure UFW for production
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable
```

## 🔄 Updates and Maintenance

### Updating RovoDev

```bash
cd ~/ai-assistant

# Pull latest changes
git pull origin main

# Rebuild containers if needed
docker compose down
docker compose build --no-cache
docker compose up -d

# Check health after update
curl http://localhost:8080/health
```

### Backup Strategy

```bash
# Create backup script
nano ~/backup-ai-assistant.sh
```

**Backup Script:**
```bash
#!/bin/bash
BACKUP_DIR="/backup/ai-assistant/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
docker exec assistant-postgres pg_dump -U assistant assistant > "$BACKUP_DIR/postgres.sql"

# Backup ChromaDB
docker cp assistant-chromadb:/chroma/chroma "$BACKUP_DIR/chromadb"

# Backup environment and configs
cp ~/ai-assistant/.env "$BACKUP_DIR/"
cp ~/ai-assistant/docker-compose.yml "$BACKUP_DIR/"

echo "Backup completed: $BACKUP_DIR"
```

```bash
chmod +x ~/backup-ai-assistant.sh

# Schedule daily backups
crontab -e
# Add: 0 2 * * * /home/aiassistant/backup-ai-assistant.sh
```

### Monitoring and Logs

```bash
# System monitoring
~/ai-assistant/system-monitor.sh

# Application logs
docker compose logs -f assistant

# Database logs
docker compose logs -f postgres

# Vector database logs
docker compose logs -f chromadb

# System resource usage
htop
docker stats
```

## 🚨 Troubleshooting

### Common Issues

**1. Docker Permission Denied**
```bash
sudo usermod -aG docker $USER
# Logout and login again
```

**2. Port Already in Use**
```bash
sudo lsof -i :8080
# Kill conflicting process or change ports
```

**3. Ollama Model Not Loading**
```bash
ollama pull qwen2.5:14b
systemctl status ollama
journalctl -u ollama -f
```

**4. Database Connection Failed**
```bash
docker compose logs postgres
# Check POSTGRES_PASSWORD in .env
```

**5. Out of Memory**
```bash
free -h
# Increase swap or reduce model size
```

### Health Check Commands

```bash
# Quick health check
curl -f http://localhost:8080/health || echo "API unhealthy"
curl -f http://localhost:8000/api/v1/heartbeat || echo "ChromaDB unhealthy"
curl -f http://localhost:11434/api/tags || echo "Ollama unhealthy"

# Detailed status
curl http://localhost:8080/status | jq

# Container status
docker compose ps
docker stats --no-stream
```

## 📊 Performance Optimization

### For 32GB RAM Systems

**Memory Allocation:**
- Ollama: 16GB
- PostgreSQL: 2GB
- ChromaDB: 2GB
- FastAPI: 4GB
- System: 8GB

**Docker Compose Optimization:**
```yaml
# Add to docker-compose.yml
services:
  postgres:
    deploy:
      resources:
        limits:
          memory: 2G
  chromadb:
    deploy:
      resources:
        limits:
          memory: 2G
  assistant:
    deploy:
      resources:
        limits:
          memory: 4G
```

### System Tuning

```bash
# Optimize for AI workloads
echo 'vm.swappiness=10' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_ratio=15' | sudo tee -a /etc/sysctl.conf
echo 'vm.dirty_background_ratio=5' | sudo tee -a /etc/sysctl.conf

# Apply changes
sudo sysctl -p
```

## 🔐 Security Hardening

### Production Security Checklist

- [ ] Change default passwords
- [ ] Configure firewall (UFW)
- [ ] Enable fail2ban
- [ ] Set up SSL certificates
- [ ] Regular security updates
- [ ] Monitor access logs
- [ ] Backup encryption
- [ ] API rate limiting

### Security Script

```bash
# Create security hardening script
nano ~/harden-ai-assistant.sh
```

**Security Hardening:**
```bash
#!/bin/bash
# Basic security hardening for RovoDev

# Update system
sudo apt update && sudo apt upgrade -y

# Configure firewall
sudo ufw default deny incoming
sudo ufw default allow outgoing
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw --force enable

# Install and configure fail2ban
sudo apt install -y fail2ban
sudo systemctl enable fail2ban
sudo systemctl start fail2ban

# Secure SSH
sudo sed -i 's/#PermitRootLogin yes/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/#PasswordAuthentication yes/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo systemctl restart ssh

# Set up automatic security updates
sudo apt install -y unattended-upgrades
sudo dpkg-reconfigure -plow unattended-upgrades

echo "Security hardening completed"
```

---

**This deployment guide ensures RovoDev can be reliably deployed to any Ubuntu server with minimal manual intervention while maintaining security and performance best practices.**