# Signal Integration Setup Guide

## 🔒 **Signal "Note to Self" Integration**

This guide shows how to set up Signal integration for secure, encrypted communication with your AI assistant using your existing Signal "Note to Self" chat.

## 📋 **Prerequisites**

- Ubuntu Server with the AI assistant already deployed
- Signal app installed on your phone
- Your phone number registered with Signal

## 🚀 **Setup Process**

### **Step 1: Install Signal CLI on Server**

```bash
# Update system
sudo apt update

# Install Java (required for signal-cli)
sudo apt install openjdk-17-jre -y

# Download and install signal-cli
cd /tmp
wget https://github.com/AsamK/signal-cli/releases/latest/download/signal-cli-0.12.8.tar.gz
tar xf signal-cli-*.tar.gz
sudo mv signal-cli-* /opt/signal-cli
sudo ln -sf /opt/signal-cli/bin/signal-cli /usr/local/bin/

# Verify installation
signal-cli --version
```

### **Step 2: Link Server as Signal Device**

```bash
# Generate linking QR code
signal-cli link -n "AI Assistant Server"
```

**This will display a QR code in your terminal.**

### **Step 3: Link with Your Phone**

1. **Open Signal app** on your phone
2. **Go to Settings** → **Linked devices**
3. **Tap "Link New Device"**
4. **Scan the QR code** displayed in your terminal
5. **Wait for confirmation** (should take 10-30 seconds)

### **Step 4: Test the Connection**

```bash
# Replace +1234567890 with YOUR actual phone number
signal-cli -a +1234567890 send +1234567890 -m "Test from AI server"
```

**Check your Signal "Note to Self"** - you should see the test message!

### **Step 5: Configure Environment**

```bash
# Edit your .env file
nano .env

# Add your phone number (replace with your actual number)
SIGNAL_PHONE_NUMBER=+1234567890
```

### **Step 6: Restart the Application**

```bash
# Restart containers to pick up new configuration
docker compose down
docker compose up -d

# Check logs to verify Signal integration
docker logs assistant-api
```

## ✅ **Verification**

### **Test the Integration**

1. **Send a message to your Note to Self** in Signal:
   ```
   Meeting with John about project timeline. Discussed:
   - Launch date moved to March 15th
   - Need to hire 2 more developers
   - Budget approved for additional resources
   
   Action items:
   - John to post job listings by Friday
   - Review budget allocation next week
   - Schedule follow-up meeting for March 1st
   ```

2. **Wait 5-10 seconds** for processing

3. **You should receive**:
   - Meeting summary
   - Extracted action items
   - Calendar reminder files (.ics)

### **Check API Status**

```bash
# Check Signal bot status
curl http://localhost:8080/signal/status

# Test Signal connection
curl -X POST http://localhost:8080/signal/test-connection

# Check overall health
curl http://localhost:8080/health
```

## 🔧 **Troubleshooting**

### **Common Issues**

**QR Code Not Displaying**
```bash
# Make sure you're in a terminal that supports graphics
# Try using tmux or screen if SSH'd into server
signal-cli link -n "AI Assistant" --qr-ascii
```

**"Account not found" Error**
```bash
# Make sure you used YOUR phone number
signal-cli -a +YOUR_ACTUAL_NUMBER send +YOUR_ACTUAL_NUMBER -m "test"
```

**Permission Errors**
```bash
# Fix signal-cli permissions
sudo chown -R $USER:$USER ~/.local/share/signal-cli/
```

**Messages Not Processing**
```bash
# Check application logs
docker logs assistant-api -f

# Verify Signal CLI is working
signal-cli -a +YOUR_NUMBER receive
```

### **Reset Signal CLI (if needed)**

```bash
# Remove Signal CLI data and start over
rm -rf ~/.local/share/signal-cli/
signal-cli link -n "AI Assistant Server"
```

## 🔒 **Security Benefits**

### **What You Get**
- ✅ **End-to-end encryption** for all communication
- ✅ **No third-party bot services** involved
- ✅ **Signal's proven security** protocol
- ✅ **Familiar interface** (your existing Note to Self)
- ✅ **Zero metadata leakage** to external services

### **Privacy Model**
- **Your phone** ↔ **Signal servers** ↔ **Your server**
- All communication encrypted with Signal's protocol
- Your server acts as a "linked device" (like a tablet)
- No data stored on external servers

## 📱 **Usage**

### **Send Meeting Notes**
Just send meeting content to your **Note to Self** in Signal:
- Paste TwinMind transcripts
- Type meeting notes
- Forward meeting emails

### **Ask Questions**
Ask about your meetings:
- "What did we decide about the budget?"
- "When is the next review meeting?"
- "Who was assigned the marketing tasks?"

### **Receive Responses**
Get back:
- Meeting summaries
- Action item lists
- Calendar reminder files
- Contextual answers

## 🎯 **Next Steps**

Once Signal integration is working:

1. **Test with real meeting content**
2. **Verify calendar files work on iOS**
3. **Set up Notion integration** (optional)
4. **Configure Gmail processing** (optional)
5. **Explore advanced features**

---

**Your AI assistant is now securely integrated with Signal! All communication is end-to-end encrypted and completely private.**