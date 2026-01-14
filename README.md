# 🏨 Hotel Workflow Telegram Bot

A comprehensive role-based Telegram bot for managing hotel staff tasks, maintenance, and housekeeping workflows. All operations live in Telegram with real-time Google Sheets synchronization.

## ✅ Status: Phase 1 Complete

**All requirements met. All issues fixed. Ready for production.**

| Component | Status | Details |
|-----------|--------|---------|
| Report Generation | ✅ WORKING | Today's & weekly reports pull real data |
| Data Syncing | ✅ WORKING | Cleaning, maintenance, and tasks all sync |
| Admin Alerts | ✅ WORKING | Real-time notifications on all actions |
| Staff Management | ✅ WORKING | Add/remove/list staff with roles |
| Role-Based Access | ✅ WORKING | Staff vs Admin commands properly segregated |

---

## Quick Start

### Installation
```bash
cd /home/soarer/Documents/projects/freelance/Hotel-Workflow-Bot
source bot_env/bin/activate
pip install -r requirements.txt
```

### Configuration
Create `.env` file:
```
TELEGRAM_BOT_TOKEN=your_token_here
ADMIN_USER_IDS=your_telegram_id
GOOGLE_CREDENTIALS_FILE=credentials.json
SPREADSHEET_NAME=Hotel Workflow Data
```

### Run
```bash
python3 hotel_bot.py
```

### Verify
```bash
python3 test_sheets.py
```

---

## 📋 Features

### 👔 Staff Commands
- **`/clean`** - Mark room cleaning progress
- **`/maintenance`** - Report maintenance issue
- **`/task`** - Mark task as completed
- **`/mystats`** - View your activity statistics
- **`/start`** - Show available commands
- **`/getid`** - Get your Telegram User ID

### 👨‍💼 Admin Commands
- **`/admin`** - Open control panel with buttons
- **`/today`** - View today's activity report
- **`/weekly`** - View weekly summary and top performers
- **`/addstaff`** - Register new staff member
- **`/removestaff`** - Remove staff member
- **`/liststaff`** - View all registered staff
- **`/staffguide`** - Admin management guide

### 🤖 Automatic Features
- Real-time notifications to all admins on staff actions
- Automatic data sync to Google Sheets
- Role-based help messages for non-command input
- Admin alerts for every cleaning, maintenance, and task entry

---

## 🏢 Data Organization

All data syncs automatically to Google Sheets:

### Cleaning Log
- Room number
- Status (Not Started, In Progress, Done, Pending Review)
- Staff name and ID
- Timestamp

### Maintenance Log
- Room number
- Issue description
- Priority (Low, Medium, High, Critical)
- Staff name and ID
- Timestamp

### Task Completion Log
- Task name
- Staff name and ID
- Completion status
- Timestamp

### Staff Registry
- Telegram User ID
- Name
- Role (Staff or Admin)
- Date registered

---

## 📊 Reports

### Today's Report (`/today`)
```
📊 Today's Report (2026-01-14)

🧹 Cleaning: 2 rooms processed
Recent updates:
  • Room 101 → Done (John)
  • Room 102 → In Progress (Mary)

🔧 Maintenance: 1 issues reported
Recent reports:
  • Room 103: Faucet leaking (HIGH)

✅ Tasks: 2 completed
Recent tasks:
  • Clean lobby (John)
```

### Weekly Report (`/weekly`)
```
📈 Weekly Summary
(2026-01-07 to 2026-01-14)

🧹 Cleaning: 15 rooms cleaned
🔧 Maintenance: 8 issues reported
✅ Tasks: 20 completed

📊 Top Performers:
🥇 John: 18 activities
🥈 Mary: 15 activities
🥉 Bob: 12 activities
```

---

## 👥 Staff Management Workflow

### Add New Staff
```
Admin: /addstaff
Bot: "Enter staff's User ID"
Admin: Types user ID from /getid command
Bot: "Enter staff name"
Admin: Types name
Bot: Shows role selection (Staff or Admin)
Admin: Selects role
Bot: Confirms and registers
Staff: Gets access to bot
```

### Remove Staff
```
Admin: /removestaff
Bot: Shows list of all staff
Admin: Clicks staff member to remove
Bot: Confirms removal
Staff: Loses access
```

---

## 🔔 Admin Notifications

Admins automatically receive alerts:

**On Cleaning Update**
```
🔔 Admin Alert

🧹 Cleaning Update
Room: 101
Status: Done
Staff: John
```

**On Maintenance Report**
```
🔔 Admin Alert

⚠️ Maintenance Report
Room: 102
Issue: Faucet leaking
Priority: HIGH
By: Mary
```

**On Task Completion**
```
🔔 Admin Alert

📝 Task Completed
Task: Clean lobby
By: John
```

---

## 📚 Documentation

| Document | Purpose |
|----------|---------|
| **README.md** (this file) | Overview and quick start |
| **SETUP_AND_TESTING.md** | Complete setup guide and testing procedures |
| **DEPLOYMENT.md** | Production deployment and operations |
| **TECHNICAL_DOCUMENTATION.md** | Architecture, code details, and extension points |
| **CHANGES.md** | Detailed change log and what was fixed |

---

## 🧪 Testing

### Test Data Flow
1. Send `/clean` command
2. Enter room number (e.g., 101)
3. Select status
4. Check Google Sheets - entry appears instantly
5. Admin receives notification

### Test Reports
1. Admin sends `/today`
2. Should show entries logged today
3. Should show counts and recent entries

### Test Staff Management
1. Send `/getid` to get your Telegram ID
2. Admin sends `/addstaff`
3. Admin enters ID, name, role
4. You can now use `/start`

### Run Diagnostic
```bash
source bot_env/bin/activate
python3 test_sheets.py
```

Expected output:
```
✅ Successfully authenticated with Google Sheets
✅ Found spreadsheet: Hotel Workflow Data
✅ Cleaning Log: X records
✅ Maintenance Log: X records
✅ Task Completion Log: X records
✅ Staff Registry: X records
✅ Successfully logged test data
✅ Report generation works
```

---

## 🔐 Security & Privacy

- **Credentials**: Keep `.env` and `credentials.json` secure
- **Access Control**: Only registered users can access bot
- **Role-Based**: Staff and admin have different permissions
- **Data**: All data encrypted in transit and at rest (Google Sheets)
- **Audit Trail**: Every action timestamped with staff member info

---

## 🚀 Deployment

### Local Testing
```bash
python3 hotel_bot.py
```

### Production (Linux Systemd)
```bash
sudo systemctl start hotel-bot
sudo systemctl enable hotel-bot
```

See **DEPLOYMENT.md** for full production setup.

---

## 🐛 Troubleshooting

### Reports Show No Data
```bash
# Use commands to log test data first
/clean → enter room → select status
/maintenance → enter room → describe issue → select priority
/task → enter task name

# Then check reports
/today
```

### Bot Won't Start
```bash
# Verify virtual environment
source bot_env/bin/activate

# Check dependencies
pip install -r requirements.txt

# Run bot with output
python3 hotel_bot.py
```

### Google Sheets Not Syncing
```bash
# Run diagnostic
python3 test_sheets.py

# Verify credentials
cat credentials.json | head -5

# Check .env
cat .env
```

### Admins Don't Get Alerts
- Ensure `ADMIN_USER_IDS` is set in `.env`
- Admin should send `/start` first
- Check bot logs for errors

See **SETUP_AND_TESTING.md** for more troubleshooting.

---

## 📱 Requirements

- Python 3.8+
- Telegram account with bot token
- Google account with Sheets API access
- Linux/Mac/Windows with internet connection

---

## 📦 Dependencies

All included in `requirements.txt`:
- python-telegram-bot==20.7
- gspread==5.12.0
- google-auth-oauthlib==1.1.0
- python-dotenv==1.2.1
- (plus other supporting libraries)

---

## 🎯 What's Working

✅ Staff can log cleaning progress
✅ Staff can report maintenance issues
✅ Staff can mark tasks complete
✅ All data syncs to Google Sheets
✅ Admins get real-time notifications
✅ Reports show real data from sheets
✅ No fake or dummy data
✅ Role-based access control
✅ Staff management (add/remove)
✅ Activity statistics tracking
✅ Help messages with role-specific commands

---

## 📈 Future Phases

**Phase 2**: Task assignment, room status tracking, scheduling
**Phase 3**: Web dashboard, analytics, email reports
**Phase 4**: Mobile app, multi-location support

---

## 📞 Support

1. Check documentation files (README, SETUP_AND_TESTING.md)
2. Run diagnostic: `python3 test_sheets.py`
3. Review TECHNICAL_DOCUMENTATION.md for architecture
4. Check bot logs for error messages

---

**Version**: 1.0.0 | **Status**: ✅ Production Ready | **Last Updated**: 2026-01-14
   - ⏳ **Pending Review** - Cleaning done, waiting for inspection

#### 3️⃣ Report Maintenance Issue
```
/maintenance
```
1. Click "Report Issue"
2. Enter the room number
3. Describe the issue (e.g., "Broken AC", "Leaking faucet")
4. Select priority:
   - 🟢 **Low** - Can wait
   - 🟡 **Medium** - Should be fixed soon
   - 🟠 **High** - Urgent
   - 🔴 **Critical** - Emergency

#### 4️⃣ Log Task Completion
```
/task
```
1. Click "Mark Task Complete"
2. Enter the task name (e.g., "Pool cleaning", "Lobby inspection")
3. Task is automatically logged

#### 5️⃣ View Your Activity Statistics
```
/mystats
```
See how many rooms you've cleaned, maintenance reports submitted, and tasks completed today and all-time.

### For Admin

#### Adding Staff Members

**Step-by-step process:**

1. **Ask staff member to run `/getid`**
   - They'll get their User ID from the bot
   - They share it with you

2. **Run `/addstaff` command**
   - Enter the staff member's User ID
   - Enter their full name
   - Select their role:
     - 👔 **Staff** - Can log cleaning, maintenance, and tasks
     - 👨‍💼 **Admin** - Can manage staff and view reports

3. **System automatically notifies the staff member**
   - They receive a welcome message
   - They can start using `/start` to see available commands

#### Viewing All Registered Staff
```
/liststaff
```
Shows all staff members organized by role with their join dates.

#### Removing Staff Members
```
/removestaff
```
Click on a staff member to remove them from the system.

#### Viewing Daily Reports
```
/today
```
Shows:
- Number of rooms cleaned with recent examples
- Maintenance issues reported with priority levels
- Tasks completed

#### Viewing Weekly Performance
```
/weekly
```
Shows:
- Total cleaning, maintenance, and tasks for the week
- Top 5 performing staff members with medals (🥇🥈🥉)

#### Admin Control Panel
```
/admin
```
Central hub with buttons for:
- 📊 Today's Reports
- 📈 Weekly Summary
- 👥 Staff List
- ➕ Add Staff
- 🔄 Reset Tasks
- 📋 Full Reports (Google Sheets)

#### Admin Guide for Staff Management
```
/staffguide
```
Detailed guide explaining the complete staff management workflow.

## 🛠️ Setup Instructions

### Prerequisites
- Telegram Bot Token (from [@BotFather](https://t.me/BotFather))
- Google Cloud Service Account credentials
- Python 3.8+

### 1. Create Telegram Bot

1. Open Telegram and message [@BotFather](https://t.me/BotFather)
2. Send `/newbot`
3. Follow the prompts to create your bot
4. Save the API token

### 2. Set Up Google Sheets Access

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project
3. Enable these APIs:
   - Google Sheets API
   - Google Drive API
4. Create a Service Account:
   - Credentials → Create Credentials → Service Account
   - Go to the service account → Keys → Add Key → Create new key
   - Download as JSON and save as `credentials.json`
5. Create a Google Sheet named "Hotel Workflow Data"
6. Share the sheet with the service account email (from credentials.json)

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment Variables

Create a `.env` file:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GOOGLE_CREDENTIALS_FILE=credentials.json
SPREADSHEET_NAME=Hotel Workflow Data
ADMIN_USER_IDS=123456789,987654321
```

**Note:** Get admin User IDs by running `/getid`

### 5. Run the Bot

```bash
python3 hotel_bot.py
```

The bot will automatically create all necessary Google Sheets worksheets on first run.

## 📊 Data Storage

The bot automatically creates and manages these Google Sheets:

### Cleaning Log
| Timestamp | Room Number | Staff Name | Staff ID | Status | Notes |
|-----------|------------|-----------|---------|--------|-------|
| 2024-01-13 10:30:45 | 101 | John | 123456 | Done | - |

### Maintenance Log
| Timestamp | Room Number | Issue | Staff Name | Staff ID | Priority | Status |
|-----------|------------|-------|-----------|---------|----------|--------|
| 2024-01-13 11:15:30 | 205 | Broken AC | Jane | 789012 | High | Open |

### Task Completion Log
| Timestamp | Task Name | Staff Name | Staff ID | Status |
|-----------|-----------|-----------|---------|--------|
| 2024-01-13 14:00:00 | Pool Cleaning | Mike | 456789 | Completed |

### Staff Registry
| User ID | Name | Role | Date Added | Status |
|---------|------|------|-----------|--------|
| 123456 | John Smith | staff | 2024-01-10 09:30:00 | active |

## 🎯 Features Implemented

✅ **Core Functionality**
- Interactive button-based interface
- Conversation handling for multi-step processes
- Real-time admin notifications
- Google Sheets integration

✅ **Staff Management**
- Complete staff registration system
- Role-based access control (Staff/Admin)
- Staff removal with database cleanup
- User ID retrieval for easy onboarding

✅ **Reporting Features**
- Daily activity summaries
- Weekly performance metrics
- Top performer rankings
- Individual staff statistics

✅ **Status & Priority Examples**
- Cleaning statuses with clear examples
- Maintenance priorities with color indicators
- Safe data access (fixed "list out of range" error)

✅ **Admin Guide**
- Comprehensive staff management guide
- Step-by-step workflow instructions
- Role explanations
- Best practices

## 🔐 Security & Authorization

- Only authorized users (admins + registered staff) can use the bot
- Admin-only commands are protected
- All activities logged with timestamp and user information
- Safe error handling prevents system crashes

## ⚠️ Troubleshooting

### Bot not responding
- Check that `TELEGRAM_BOT_TOKEN` is correct in `.env`
- Ensure bot has internet connection

### Google Sheets errors
- Verify `credentials.json` exists and is valid
- Check that service account has access to the sheet
- Ensure sheet name matches `SPREADSHEET_NAME` in `.env`

### Staff not registered
- Ask staff to run `/getid` to get their User ID
- Use `/addstaff` to register them properly
- Verify User ID is entered correctly (no spaces)

### "List out of range" error (FIXED)
- This error is now fixed with safe indexing
- Reports gracefully handle empty data

## 📝 Commands Reference

| Command | User | Purpose |
|---------|------|---------|
| `/start` | All | Show welcome message and available commands |
| `/getid` | All | Get your Telegram User ID |
| `/clean` | Staff | Log room cleaning |
| `/maintenance` | Staff | Report maintenance issue |
| `/task` | Staff | Log task completion |
| `/mystats` | Staff | View personal activity statistics |
| `/admin` | Admin | Open admin control panel |
| `/addstaff` | Admin | Register new staff member |
| `/liststaff` | Admin | View all staff members |
| `/removestaff` | Admin | Remove staff member |
| `/today` | Admin | View today's activity report |
| `/weekly` | Admin | View weekly performance summary |
| `/reset` | Admin | Reset daily tasks |
| `/staffguide` | Admin | View staff management guide |

## 🚀 Getting Started Checklist

- [ ] Create Telegram bot with @BotFather
- [ ] Set up Google Cloud service account
- [ ] Download credentials.json
- [ ] Create `.env` file with your tokens
- [ ] Run `pip install -r requirements.txt`
- [ ] Start bot with `python3 hotel_bot.py`
- [ ] Add yourself as admin using your User ID
- [ ] Test with `/start` and `/getid`
- [ ] Add first staff member using `/addstaff`
- [ ] Train staff on commands

## 📄 License

Private project for hotel operations.

## 🤝 Support

For issues or feature requests, contact the development team.
