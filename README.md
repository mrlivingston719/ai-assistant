# Personal AI Assistant

> **Secure Signal integration with end-to-end encryption for meeting processing and personal knowledge management**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-required-blue.svg)](https://www.docker.com/)

## 🚀 Quick Deploy to Any Ubuntu Server

Deploy RovoDev to any Ubuntu 24.04 LTS server in under 30 minutes:

```bash
# 1. Clone the repository
git clone https://github.com/mrlivingston719/ai-assistant.git
cd ai-assistant

# 2. Run automated setup (installs Docker, Ollama, optimizes system)
chmod +x setup.sh
./setup.sh

# 3. Configure your Signal phone number
# Setup script will prompt for your Signal phone number
# and automatically configure .env file

# 4. Download AI model (8GB download)
ollama pull qwen2.5:14b

# 5. Start the application
# Development mode:
docker compose up -d

# Production mode (recommended for servers):
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# 6. Verify deployment
curl http://localhost:8080/health
```

**That's it!** Your personal AI assistant is now running locally.

## 🎯 What RovoDev Does

- **📝 Meeting Processing**: Automatically processes meeting transcripts from TwinMind
- **🤖 AI-Powered Analysis**: Extracts action items, summaries, and insights using local LLM
- **📱 Signal Interface**: Chat with your AI assistant via Signal "Note to Self" with E2E encryption
- **📅 Smart Reminders**: Generates iOS calendar files with intelligent timing
- **🔍 Semantic Search**: Find relevant meetings and context using vector search
- **🔒 Privacy-First**: All sensitive data processed locally, never sent to cloud

## 🏗️ Architecture

**3-Container Setup:**
- **PostgreSQL**: Structured data (meetings, action items, users)
- **ChromaDB**: Vector embeddings for semantic search
- **FastAPI**: Main application with Signal bot integration

**Local AI Processing:**
- **Ollama + Qwen2.5-14B**: Local LLM for text processing (no cloud dependency)
- **ChromaDB**: Vector database for semantic search and context

**Simplified Design Philosophy:**
- **Direct Service Initialization**: No complex dependency injection - services created directly in main.py
- **Basic Error Handling**: Simple try/catch blocks instead of custom exception hierarchies
- **Minimal Infrastructure**: Essential components only, appropriate for personal tools
- **Clean Architecture**: Easy to understand and maintain codebase

## 📋 Requirements

### Hardware (Recommended)
- **RAM**: 32GB (minimum 16GB)
- **Storage**: 50GB+ available space
- **CPU**: 4+ cores
- **Network**: Internet connection for initial setup

### Software
- **OS**: Ubuntu 24.04 LTS (primary), Ubuntu 22.04 LTS (supported)
- **Docker**: Installed automatically by setup script
- **Ollama**: Installed automatically by setup script

## 🔧 Manual Installation

If you prefer manual setup or are using a different OS:

### 1. Install Dependencies

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh

# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Download AI model
ollama pull qwen2.5:14b
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.example .env

# Edit with your API tokens
nano .env
```

Required environment variables:
- `SIGNAL_PHONE_NUMBER`: Your Signal phone number (e.g., +1234567890)
- `POSTGRES_PASSWORD`: Secure password for PostgreSQL
- `NOTION_TOKEN`: (Optional) Notion integration token
- `GMAIL_CREDENTIALS`: (Optional) Gmail API credentials

### 3. Start Services

```bash
# Start all containers
docker compose up -d

# Check health
docker compose ps
curl http://localhost:8080/health
```

## 📱 Setup Signal Integration

1. **Install Signal CLI**: Already included in automated setup
2. **Link Device**: The setup script guides you through device linking
3. **Phone Number**: Provide your Signal phone number during configuration
4. **"Note to Self"**: Send meeting notes to yourself in Signal

## 🔍 Usage Examples

### Process a Meeting
Send meeting transcript to yourself in Signal (Note to Self):
```
Hey, here's my meeting transcript from today:

[Meeting content...]
```

The AI will:
- Extract action items
- Generate summary
- Create calendar reminders
- Store for future context

### Ask Questions
```
What action items do I have from this week's meetings?
Find meetings about the marketing project
What did we decide about the budget?
```

### Smart Reminders
The system automatically:
- Creates .ics calendar files
- Sets 15-minute default reminders
- Adds travel time buffers
- Sends via Signal "Note to Self"

## 🛠️ Development

### Local Development Setup

```bash
# Clone repository
git clone https://github.com/mrlivingston719/ai-assistant.git
cd ai-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Start development server
uvicorn src.main:app --reload --host 0.0.0.0 --port 8080
```

### Project Structure

```
ai-assistant/
├── src/                    # Application source code
│   ├── main.py            # FastAPI app with simplified service initialization
│   ├── config.py          # Configuration management
│   ├── models.py          # Database models
│   ├── database.py        # Database connection
│   ├── vector_store.py    # ChromaDB integration
│   ├── signal_bot.py      # Signal "Note to Self" integration
│   ├── routers/           # API route handlers
│   │   ├── meetings.py    # Meeting management endpoints
│   │   └── signal.py      # Signal integration endpoints
│   └── services/          # Business logic services
│       ├── meeting_processor.py  # AI-powered meeting processing
│       ├── signal_service.py     # Signal CLI integration
│       └── calendar_service.py   # iOS calendar generation
├── docker-compose.yml     # Container orchestration
├── Dockerfile            # Application container
├── requirements.txt      # Python dependencies
├── setup.sh             # Automated setup script
└── .env.example         # Environment template
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest

# Run with coverage
pytest --cov=src
```

## 🔒 Security & Privacy

### Privacy Features
- **Local Processing**: All AI processing happens locally via Ollama
- **No Cloud Dependencies**: Sensitive data never leaves your server
- **Encrypted Storage**: API tokens and credentials stored securely
- **Audit Trail**: All AI decisions logged for transparency

### Security Hardening
The setup script automatically:
- Configures UFW firewall
- Enables fail2ban
- Sets up Docker security
- Optimizes system for AI workloads

### Production Deployment
For production use:
1. **Use HTTPS**: Configure reverse proxy (nginx/Caddy)
2. **Secure API Keys**: Use proper secret management
3. **Regular Backups**: Backup PostgreSQL and ChromaDB data
4. **Monitor Resources**: Use included monitoring tools

## 📊 Monitoring

### Health Checks
```bash
# Application health
curl http://localhost:8080/health

# Component status
curl http://localhost:8080/status

# Database health
curl http://localhost:8000/api/v1/heartbeat  # ChromaDB
curl http://localhost:11434/api/tags         # Ollama
```

### System Monitoring
```bash
# Use included monitoring script
./system-monitor.sh

# Docker logs
docker compose logs -f

# Resource usage
htop
docker stats
```

## 🚀 Performance

### Optimized for 32GB RAM
- **Ollama**: 16GB allocation for fast LLM processing
- **PostgreSQL**: 2GB for database operations
- **ChromaDB**: 2GB for vector operations
- **FastAPI**: 4GB for application logic
- **System Buffer**: 4GB for OS and other processes

### Performance Targets
- **Phase 1**: <10s meeting processing
- **Phase 2**: <7s with contextual responses
- **Phase 3**: <5s real-time performance
- **Capacity**: 30+ meetings/week

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

### Common Issues

**Docker Permission Denied**
```bash
sudo usermod -aG docker $USER
# Logout and login again
```

**Ollama Model Not Found**
```bash
ollama pull qwen2.5:14b
ollama list  # Verify model is downloaded
```

**Port Already in Use**
```bash
# Check what's using the port
sudo lsof -i :8080
# Stop conflicting services or change ports in docker-compose.yml
```

### Getting Help

- **Issues**: [GitHub Issues](https://github.com/mrlivingston719/ai-assistant/issues)
- **Discussions**: [GitHub Discussions](https://github.com/mrlivingston719/ai-assistant/discussions)
- **Documentation**: See `/docs` folder for detailed guides

## 🗺️ Roadmap

### Phase 1: Core MVP ✅
- [x] 3-container architecture
- [x] Meeting processing pipeline
- [x] Signal "Note to Self" integration with E2E encryption
- [x] Vector search capabilities
- [x] iOS calendar integration

### Phase 2: Enhanced Intelligence (In Progress)
- [ ] Advanced contextual responses
- [ ] Improved prompt engineering
- [ ] Enhanced conversation memory
- [ ] Performance optimization

### Phase 3: Production Hardening (Planned)
- [ ] Security hardening
- [ ] Advanced monitoring
- [ ] Backup automation
- [ ] Multi-user support

---

**Built with ❤️ for privacy-conscious users who want powerful AI without compromising their data.**