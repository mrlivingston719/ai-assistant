# Signal Integration Deployment Guide

## 🔐 **Secure Signal "Note to Self" Integration**

This deployment guide covers the complete setup of the Personal AI Assistant with Signal integration for maximum privacy and security.

## 📋 **Prerequisites**

- Ubuntu Server 22.04 or 24.04 LTS
- 16GB+ RAM (32GB recommended)
- 50GB+ available storage
- Signal app installed on your phone
- Your phone number registered with Signal

## 🚀 **Complete Deployment Process**

### **Step 1: Server Setup**

```bash
# Clone the repository
git clone https://github.com/mrlivingston719/ai-assistant.git
cd ai-assistant

# Run automated setup (installs everything)
chmod +x setup.sh
./setup.sh
```

**The setup script will:**
- Install Docker, Docker Compose, and system dependencies
- Install Signal CLI and Java runtime
- Install and configure Ollama with optimizations
- Prompt for your Signal phone number
- Generate secure database passwords
- Configure firewall and security settings

### **Step 2: Signal Device Linking**

After setup completes, link your server as a Signal device:

```bash
# Generate QR code for device linking
signal-cli link -n "AI Assistant Server"
```

**On your phone:**
1. Open Signal app
2. Go to Settings → Linked devices
3. Tap "Link New Device"
4. Scan the QR code displayed in terminal
5. Wait for confirmation

### **Step 3: Test Signal Connection**

```bash
# Test Signal CLI connection
signal-cli -a +YOUR_PHONE_NUMBER send +YOUR_PHONE_NUMBER -m "Test from AI server"
```

Check your Signal "Note to Self" - you should see the test message!

### **Step 4: Download AI Model**

```bash
# Download Qwen2.5-14B model (~8GB)
ollama pull qwen2.5:14b
```

### **Step 5: Start Application**

```bash
# Start all containers
docker compose up -d

# Verify all services are healthy
docker ps
curl http://localhost:8080/health
```

### **Step 6: Container Signal Linking**

The container also needs Signal CLI access:

```bash
# Link Signal CLI inside container
docker exec -it assistant-api signal-cli link -n "Container Device"
```

Scan the second QR code with your Signal app.

## 🎯 **Usage**

### **Send Meeting Notes**
1. Open Signal on your phone
2. Go to "Note to Self" (saved messages)
3. Send meeting content:
   ```
   Meeting with John about Q1 planning
   
   Discussed:
   - Budget increase approved for marketing
   - Hiring 2 new developers by March
   - Product launch moved to April 15th
   
   Action items:
   - John to post job listings by Friday
   - Review marketing budget next week
   - Schedule follow-up meeting for March 1st
   ```

### **Receive AI Response**
Within 5-10 seconds, you'll receive:
- Meeting summary
- Extracted action items
- Calendar reminder files (.ics)

### **Ask Questions**
Ask about your meetings:
- "What did we decide about the budget?"
- "When is the product launch?"
- "Who's responsible for hiring?"

## 🔒 **Security Benefits**

### **Maximum Privacy**
- ✅ **End-to-end encryption** for all communication
- ✅ **Signal's proven security** protocol
- ✅ **No third-party bot services** involved
- ✅ **Local AI processing** - sensitive data never leaves your server
- ✅ **Zero metadata leakage** to external services

### **Trust Model**
- **Your phone** ↔ **Signal servers** ↔ **Your server**
- All communication encrypted with Signal's protocol
- Your server acts as a "linked device" (like a tablet)
- No data stored on external servers

## 🔧 **Troubleshooting**

### **Signal CLI Issues**

**QR Code Not Displaying**
```bash
# Use ASCII QR code if terminal doesn't support graphics
signal-cli link -n "AI Assistant" --qr-ascii
```

**"Account not found" Error**
```bash
# Verify you're using YOUR phone number
signal-cli -a +YOUR_ACTUAL_NUMBER send +YOUR_ACTUAL_NUMBER -m "test"
```

**Permission Errors**
```bash
# Fix Signal CLI permissions
sudo chown -R $USER:$USER ~/.local/share/signal-cli/
```

### **Container Issues**

**Signal CLI Not Working in Container**
```bash
# Check if Signal CLI is installed in container
docker exec -it assistant-api signal-cli --version

# Check Signal CLI data volume
docker exec -it assistant-api ls -la /root/.local/share/signal-cli/
```

**Health Check Failures**
```bash
# Check container logs
docker logs assistant-api

# Check individual service health
curl http://localhost:8080/signal/health
```

### **Application Issues**

**Messages Not Processing**
```bash
# Check application logs
docker logs assistant-api -f

# Verify Signal phone number configuration
grep SIGNAL_PHONE_NUMBER .env
```

**Database Connection Issues**
```bash
# Check database container
docker logs assistant-postgres

# Test database connection
docker exec -it assistant-postgres psql -U assistant -d assistant -c "SELECT 1;"
```

## 📊 **Monitoring**

### **System Monitor**
```bash
# Use the included monitoring script
~/system-monitor.sh
```

### **Service Status**
```bash
# Check all service health
curl http://localhost:8080/health

# Check Signal bot status
curl http://localhost:8080/signal/status

# Check recent conversations
curl http://localhost:8080/signal/conversations
```

## 🔄 **Updates & Maintenance**

### **Update Application**
```bash
# Pull latest changes
git pull origin main

# Rebuild and restart containers
docker compose down
docker compose up -d --build
```

### **Update AI Model**
```bash
# Download newer model version
ollama pull qwen2.5:latest

# Update environment variable
sed -i 's/OLLAMA_MODEL=qwen2.5:14b/OLLAMA_MODEL=qwen2.5:latest/' .env

# Restart application
docker compose restart assistant
```

### **Backup Signal CLI Data**
```bash
# Backup Signal CLI configuration
tar -czf signal-cli-backup.tar.gz ~/.local/share/signal-cli/

# Backup database
docker exec assistant-postgres pg_dump -U assistant assistant > backup.sql
```

## 🎉 **Success!**

Your Personal AI Assistant is now running with secure Signal integration!

**Key capabilities:**
- 🔐 End-to-end encrypted communication
- 🤖 Intelligent meeting processing
- 📅 Automatic calendar reminders
- 🔍 Semantic search of your meetings
- 🏠 Complete local control of your data

**Next steps:**
- Send your first meeting notes to Signal "Note to Self"
- Configure optional integrations (Notion, Gmail)
- Explore advanced features and customization

---

**Your AI assistant is now ready to help you stay organized while keeping your data completely private and secure!**