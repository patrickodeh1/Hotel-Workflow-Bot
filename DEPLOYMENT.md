# Hotel Workflow Bot - Deployment Guide

## System Requirements
- Python 3.8+
- Linux/macOS/Windows with Python installed
- Telegram Bot Token (from BotFather)
- Google Service Account Credentials (for Sheets API)

## Phase 1 Completion Checklist

✅ **Core Functionality**
- [x] Staff mark room cleaning progress via /clean
- [x] Staff file maintenance issues via /maintenance
- [x] Staff complete daily tasks via /task
- [x] All records sync to Google Sheets in real-time
- [x] Admins get real-time notifications for all staff actions

✅ **Admin Features**
- [x] View today's reports with /today or /admin panel
- [x] View weekly summary with /weekly
- [x] Manage staff via /addstaff, /removestaff, /liststaff
- [x] Role-based access control (admin vs staff)
- [x] Guide for managing staff with /staffguide

✅ **Data Management**
- [x] Cleaning Log (timestamp, room, staff, status)
- [x] Maintenance Log (timestamp, room, issue, priority, status)
- [x] Task Completion Log (timestamp, task, staff, status)
- [x] Staff Registry (user ID, name, role, date added)

✅ **Code Quality**
- [x] Clean, well-commented Python code
- [x] Proper error handling
- [x] Logging for debugging
- [x] Full Telegram Bot API integration

## Deployment Steps

### 1. Get Telegram Bot Token
1. Message @BotFather on Telegram
2. Send `/newbot`
3. Follow prompts to create bot
4. Copy the bot token (format: 123456789:ABCdefGHIjklmnoPQRstuvwxyz)

### 2. Create Google Service Account
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project named "Hotel Workflow"
3. Enable Google Sheets API and Google Drive API
4. Create Service Account:
   - Go to "Service Accounts" in IAM menu
   - Click "Create Service Account"
   - Name: `hotel-workflow-bot`
   - Grant roles: Editor
   - Create JSON key
5. Download JSON key as `credentials.json`
6. Share your Google Sheets with the service account email (found in JSON file)

### 3. Setup Project Files
```bash
# Navigate to project directory
cd /path/to/Hotel-Workflow-Bot

# Create .env file with your credentials
cat > .env << EOF
TELEGRAM_BOT_TOKEN=your_bot_token_here
GOOGLE_CREDENTIALS_FILE=credentials.json
SPREADSHEET_NAME=Hotel Workflow Data
ADMIN_USER_IDS=your_telegram_user_id_here
EOF

# Copy credentials.json to project directory
cp /path/to/downloaded/credentials.json ./credentials.json
```

### 4. Install Dependencies
```bash
# Create virtual environment
python3 -m venv bot_env

# Activate it
source bot_env/bin/activate

# Install packages
pip install -r requirements.txt
```

### 5. Test Everything Works
```bash
# Run diagnostic test
python3 test_sheets.py

# Should show:
# ✅ Successfully authenticated with Google Sheets
# ✅ Found spreadsheet: Hotel Workflow Data
# ✅ Testing data access (all logs)
# ✅ Testing data logging (all logs)
# ✅ Testing report generation
```

### 6. Start the Bot
```bash
# Make sure environment is activated
source bot_env/bin/activate

# Start bot
python3 hotel_bot.py

# You should see:
# [INFO] Bot starting...
# [INFO] Google Sheets initialized successfully
```

## Running as a Service (Linux)

### Create Systemd Service
```bash
sudo tee /etc/systemd/system/hotel-bot.service > /dev/null << EOF
[Unit]
Description=Hotel Workflow Telegram Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=/home/soarer/Documents/projects/freelance/Hotel-Workflow-Bot
Environment="PATH=/home/soarer/Documents/projects/freelance/Hotel-Workflow-Bot/bot_env/bin"
ExecStart=/home/soarer/Documents/projects/freelance/Hotel-Workflow-Bot/bot_env/bin/python3 hotel_bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Enable and start
sudo systemctl daemon-reload
sudo systemctl enable hotel-bot
sudo systemctl start hotel-bot

# Check status
sudo systemctl status hotel-bot

# View logs
sudo journalctl -u hotel-bot -f
```

### Stop/Restart Bot
```bash
sudo systemctl stop hotel-bot
sudo systemctl restart hotel-bot
```

## Running as Background Process (Alternative)

```bash
# Start in background with output to file
nohup python3 -u hotel_bot.py > bot.log 2>&1 &

# View logs
tail -f bot.log

# Find process ID
ps aux | grep hotel_bot

# Kill if needed
kill <PID>
```

## First-Time Setup Walkthrough

1. **Get Your User ID**
   - Start a conversation with your bot
   - Send `/getid`
   - Note your Telegram User ID

2. **Add to ADMIN_USER_IDS**
   - Edit .env file
   - Set `ADMIN_USER_IDS=your_id_here`
   - Restart bot

3. **Restart Bot**
   ```bash
   # If systemd:
   sudo systemctl restart hotel-bot
   
   # If background process:
   # Kill it and restart
   ```

4. **Test Admin Functions**
   - Send `/admin` - should open control panel
   - Try `/addstaff` to register another user
   - Try `/today` to see today's report

5. **Register Staff**
   - Each staff member sends `/getid` to bot
   - Admin sends `/addstaff`
   - Enter staff member's User ID and name
   - Select role (Staff or Admin)
   - Staff member can now use `/start`

## Environment Variables Reference

```bash
# REQUIRED
TELEGRAM_BOT_TOKEN=          # Your Telegram bot token from BotFather
ADMIN_USER_IDS=              # Comma-separated list of admin Telegram user IDs

# OPTIONAL (defaults shown)
GOOGLE_CREDENTIALS_FILE=credentials.json    # Path to Google credentials JSON
SPREADSHEET_NAME=Hotel Workflow Data        # Name of Google Sheet
```

## Monitoring & Maintenance

### Regular Checks
- [ ] Check bot logs weekly for errors
- [ ] Verify Google Sheets has new entries
- [ ] Confirm admin notifications are being sent
- [ ] Test reports generation (/today, /weekly)

### Archive Old Data
- Google Sheets limits: 10 million cells per sheet
- After 6 months, create archive sheet
- Move old records to archive
- Keep current sheet for active month

### Backups
- Regularly download Google Sheets as CSV
- Store backups in secure location
- Recommended: weekly backups

## Phase 2 Planning

Potential enhancements for future phases:
- Task assignment and deadline tracking
- Room status dashboard (occupied, cleaning, maintenance)
- Automated scheduling for cleaning rotations
- Guest feedback integration
- Revenue tracking per staff member
- Email reports to management
- Web dashboard for viewing all data
- Mobile app version
- Multi-language support

## Support & Troubleshooting

### Bot Won't Start
```bash
# Check Python version
python3 --version  # Should be 3.8+

# Check dependencies
pip list | grep -E "telegram|gspread|google"

# Check .env file exists and is readable
cat .env

# Check logs
tail -20 bot.log  # if using background process
journalctl -u hotel-bot -n 20  # if using systemd
```

### Google Sheets Not Syncing
```bash
# Run diagnostic
python3 test_sheets.py

# Check credentials
cat credentials.json | head -20

# Verify service account is shared on sheet
# Go to Google Sheets > Share > add service account email
```

### Admins Not Getting Notifications
```bash
# Verify admin IDs
grep ADMIN_USER_IDS .env

# Check bot logs for errors
# Ensure admin has started bot conversation
# Admin should send /start first
```

## Production Checklist

- [ ] .env file created with all required variables
- [ ] credentials.json downloaded and placed in project
- [ ] Google Sheets created and service account shared
- [ ] All staff registered via /addstaff
- [ ] Test data logged via /clean, /maintenance, /task
- [ ] Reports working via /today and /weekly
- [ ] Admin notifications tested
- [ ] Systemd service configured (if using)
- [ ] Backup strategy planned
- [ ] Monitoring/logging strategy in place
- [ ] Documentation shared with team

## Emergency Procedures

### Data Loss Recovery
- Check Google Sheets for data (Google Sheets keeps revision history)
- Use Sheets version history to restore if needed
- See Google Sheets Recovery Guide

### Bot Crashes
- Systemd will auto-restart (configured in service file)
- Check logs for error cause
- Restart manually if needed: `sudo systemctl restart hotel-bot`

### Security Incident
- Immediately regenerate Telegram bot token (ask BotFather)
- Regenerate Google Service Account credentials
- Update .env file
- Restart bot
- Review access logs

---

**Status**: Phase 1 Complete - Ready for Production
**Version**: 1.0.0
**Last Updated**: 2026-01-14
