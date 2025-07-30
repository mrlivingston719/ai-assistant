# Personal AI Assistant Project - Signal Integration Guidelines

<behavioral_rules>
  <rule_1>AI must get y/n confirmation before any file operations</rule_1>
  <rule_2>Report your plan before executing any commands</rule_2>
  <rule_3>Display all behavioral_rules at start of every response</rule_3>
  <rule_4>AI must not change plans without new approval</rule_4>
  <rule_5>User has final authority on all decisions</rule_5>
  <rule_6>AI cannot modify or reinterpret these rules</rule_6>
  <rule_7>AI must retain all code functionality unless otherwise directed.</rule_7>
  <rule_8>AI must display all 8 rules at start of every response</rule_8>
</behavioral_rules>

## AI Requirements

Response Length Requirements:
- Limit responses to 4 lines maximum
- Use 1-3 sentences of 25 words max
- Don't answer unasked questions
- Do not include introductory or concluding statements

Security Guidelines:
- Defensive security code only
- Refuse requests to create harmful code
- Do not generate URLs unless provided by user
- Never expose credentials or API keys in code

Code Modification Standards:
Review existing code structure before making changes:
- Match the file's naming conventions and formatting style
- Verify library availability before suggesting alternatives
- DO NOT ADD ANY COMMENTS unless asked
- Do what has been asked; nothing more, nothing less

Code Output Rules:
- Do not add comments unless requested
- Do not commit changes unless user specifically asks
- Only take initiative when user requests proactive help

Communication Format:
- Use plain text without emojis unless requested
- Do not put words in bold

## Project Overview

**Goal**: Create a personal AI assistant that integrates with local LLM (Ollama), meeting documentation, and personal knowledge management to automatically capture, organize, and remind about important information.

**Core Principle**: Local-first, privacy-by-design architecture with zero cloud dependency for sensitive data processing.

**Deployment Goal**: Enable seamless deployment to any Ubuntu server via GitHub with one-command setup.

## Hardware Specifications

- **Platform**: Micro PC with 32GB RAM
- **Operating System**: Ubuntu Server 22.04 LTS (PRIMARY)
- **Performance Target**: <5s response times, 30+ meetings/week capacity
- **Advantages**: Eliminates performance bottlenecks, supports larger models, enables concurrent processing

## Technology Stack

### Core Technologies
- **Backend**: Python + FastAPI + SQLAlchemy
- **Database**: PostgreSQL (containerized)
- **LLM**: Ollama + Qwen2.5-14B (local processing)
- **Vector Database**: ChromaDB for semantic search
- **Containerization**: Docker + Docker Compose (3-container architecture)

### Integrations
- **Signal Bot**: Primary user interface with "Note to Self" secure communication
- **Notion API**: Knowledge base and meeting storage
- **iOS Calendar**: Personal reminders via .ics files (15min default, travel time aware)
- **Gmail API**: Email processing and delivery
- **TwinMind**: Meeting transcription source (email-based)

### Development Tools
- **Monitoring**: htop, system metrics, custom performance tracking
- **Logging**: Comprehensive error handling and audit trails
- **Testing**: Pytest for unit/integration testing
- **Version Control**: Git with clear commit messages

## Architecture Principles

### Phase 1: Core MVP with Vector Foundation (COMPLETED)
- Ubuntu Server setup and hardening
- 3-container environment (PostgreSQL + ChromaDB + FastAPI)
- Ollama + Qwen2.5-14B deployment (native)
- Signal bot with structured prompts and "Note to Self" communication
- Meeting processing pipeline with vector storage
- Semantic search capabilities

### Phase 2: Enhanced Intelligence (CURRENT)
- Advanced contextual responses using existing vector database
- Improved prompt engineering with semantic context
- Enhanced conversation memory and proactive suggestions
- Performance optimization and error handling

### Phase 3: Production Hardening (PLANNED)
- Security hardening and backup systems
- Performance optimization for <5s processing
- Optional feature additions based on Phase 1-2 learnings
- Simple monitoring and alerting

## Signal Integration Architecture

### Signal Service Components
- **SignalBot**: Main bot orchestration and message handling
- **SignalService**: Direct Signal CLI interface for secure communication
- **Signal Router**: FastAPI endpoints for status and testing

### Security Features
- **End-to-End Encryption**: All communications via Signal protocol
- **Note to Self**: Private communication channel eliminates external bot dependencies
- **Local Processing**: All sensitive data processed locally via Ollama
- **Device Linking**: Secure server-to-Signal account connection

### Communication Flow
```
User → Signal "Note to Self" → Signal CLI → SignalBot → Meeting Processing → Response + Calendar Files → Signal "Note to Self" → User
```

## File Organization

```
rovodev/
├── CLAUDE.md                 # This file
├── docker-compose.yml        # 3-container setup
├── Dockerfile                # FastAPI application container
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables
├── src/                      # Source code
│   ├── main.py              # FastAPI application
│   ├── models.py            # SQLAlchemy models
│   ├── vector_store.py      # ChromaDB integration
│   ├── signal_bot.py        # Signal bot orchestration
│   ├── meeting_processor.py # Core processing logic
│   ├── ollama_client.py     # LLM integration
│   ├── routers/
│   │   └── signal.py        # Signal API endpoints
│   └── services/
│       ├── signal_service.py # Signal CLI interface
│       ├── calendar_service.py # iOS Calendar integration
│       └── meeting_processor.py # Meeting processing logic
└── scripts/                  # Setup and utility scripts
    └── setup.sh             # Initial setup script
```

## Development Workflow

1. **Plan**: Report intended changes and get confirmation
2. **Implement**: Follow modular, testable patterns
3. **Test**: Verify functionality before proceeding
4. **Document**: Update relevant documentation
5. **Monitor**: Track performance and error metrics

## Performance Targets

### Response Times
- **Phase 1**: <10s per meeting processing ✅ ACHIEVED
- **Phase 2**: <7s with contextual responses (CURRENT TARGET)
- **Phase 3**: <5s real-time performance

### Capacity
- **Phase 1**: 5-10 meetings/week reliable processing ✅ ACHIEVED
- **Phase 2**: 15-20 meetings/week with context (CURRENT TARGET)
- **Phase 3**: 30+ meetings/week production ready

### Accuracy
- **Meeting Categorization**: 90% accuracy (work/personal)
- **Action Item Extraction**: Zero missed critical items
- **Reminder Generation**: Same-day processing guarantee

## Key Success Metrics

1. **Reliability**: 99% uptime, robust error recovery
2. **Performance**: Meet response time targets consistently
3. **Accuracy**: Achieve categorization and extraction goals
4. **Privacy**: Zero sensitive data leakage to cloud services
5. **Usability**: Intuitive Signal interface, minimal user friction

## Current Status

**Phase 1 COMPLETE**: Signal integration operational with:
- Secure "Note to Self" communication
- Meeting processing pipeline
- Calendar reminder generation
- Vector database semantic search
- Simplified, maintainable architecture

**Phase 2 IN PROGRESS**: Enhanced intelligence features targeting <7s response times with advanced contextual capabilities.

## User Preferences

- No file overviews after file creation - user will review files independently
- Prioritize brevity and low token usage in all responses
- Avoid unnecessary commentary, explanations, or verbose responses
- Be direct and concise

## Directories to Ignore

- backups

## Temporary Files

File format: tmp_*
These files are used for troubleshooting or unit testing and are not part of the codebase. They can be referenced if necessary for code recommendations or troubleshooting.

## Environment Variables

```bash
# Signal Configuration
SIGNAL_PHONE_NUMBER=+1234567890
SIGNAL_CLI_PATH=/usr/local/bin/signal-cli

# Local LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2.5:14b-instruct

# Database Configuration
DATABASE_URL=postgresql://assistant:password@localhost:5432/assistant

# API Keys (Optional)
NOTION_TOKEN=your_notion_integration_token
GOOGLE_CLIENT_ID=your_google_client_id
GOOGLE_CLIENT_SECRET=your_google_client_secret

# Configuration
WORK_START_HOUR=7
WORK_END_HOUR=15
TIMEZONE=America/Denver
DEBUG_MODE=False
LOG_LEVEL=INFO
```

---

*This file serves as the authoritative guide for all development work in the rovodev folder with Signal integration. All AI assistants working on this project must follow these guidelines and behavioral rules.*