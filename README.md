# 🏨 Hotel Workflow Telegram Bot

A comprehensive role-based Telegram bot for managing hotel staff tasks, maintenance, and housekeeping workflows. Features interactive reporting, staff management, and real-time admin notifications.

## ✨ Features

### 👔 Staff Features
- **🧹 Room Cleaning Tracking**: Log room cleaning with status options
  - Not Started
  - In Progress
  - Done
  - Pending Review
- **🔧 Maintenance Reporting**: Report maintenance issues with priority levels
  - Low
  - Medium
  - High
  - Critical
- **📝 Task Management**: Log completed tasks and activities
- **📊 Activity Statistics**: View personal activity stats with daily and all-time records
- **🆔 Get User ID**: Easy way to retrieve your Telegram ID for registration

### 👨‍💼 Admin Features
- **👥 Staff Management**: Add, remove, and view all registered staff members
- **📊 Daily Reports**: View today's cleaning, maintenance, and task summary
- **📈 Weekly Summary**: Get weekly performance metrics and top performers
- **🔔 Admin Notifications**: Real-time alerts for all staff activities
- **🔄 Task Reset**: Reset daily tasks when needed
- **📋 Full Reports**: Access complete data in Google Sheets
- **📚 Staff Management Guide**: Easy step-by-step admin guide

## 📖 User Guide

### For Staff Members

#### 1️⃣ Get Your User ID
```
/getid
```
Share the ID with your admin to get registered.

#### 2️⃣ Report Room Cleaning
```
/clean
```
1. Click "Enter Room Number"
2. Type the room number (e.g., 101, 205)
3. Select the status:
   - ✅ **Not Started** - Room not yet cleaned
   - 🔄 **In Progress** - Currently cleaning
   - ✨ **Done** - Cleaning completed
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
