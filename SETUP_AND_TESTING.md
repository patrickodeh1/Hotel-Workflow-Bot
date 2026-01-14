# Hotel Workflow Telegram Bot - Setup & Testing Guide

## ✅ What's Fixed

### 1. **Report Generation Now Works**
- ✅ Today's report shows all data for current date (cleaning, maintenance, tasks)
- ✅ Weekly report aggregates last 7 days of activity
- ✅ Reports display properly in both `/today` command and `/admin` panel

### 2. **All Data Types Sync to Google Sheets**
- ✅ Cleaning Log: Room number, status, staff name, timestamp
- ✅ Maintenance Log: Room number, issue, priority, staff name, timestamp
- ✅ Task Completion Log: Task name, staff name, timestamp, status
- ✅ Staff Registry: User ID, name, role, date added

### 3. **Real-Time Admin Alerts**
- Admins receive instant notifications when staff:
  - Mark room cleaning progress
  - File maintenance issues
  - Complete daily tasks

### 4. **Role-Based Access Control**
- Regular staff see only: `/clean`, `/maintenance`, `/task`, `/mystats`
- Admins see all staff commands PLUS: `/admin`, `/addstaff`, `/removestaff`, `/liststaff`, `/today`, `/weekly`, `/staffguide`
- Non-command messages trigger help with role-specific commands

## 📋 Core Functions

### Staff Commands
```
/clean          - Mark room cleaning progress
/maintenance    - Report maintenance issue
/task           - Mark task as completed
/mystats        - View your activity stats
/start          - View welcome & available commands
```

### Admin Commands
```
/admin          - Open admin control panel (buttons for reports)
/today          - View today's detailed report
/weekly         - View weekly summary & top performers
/addstaff       - Register new staff member
/removestaff    - Remove staff member
/liststaff      - View all staff members
/staffguide     - Admin guide for managing staff
/getid          - Get your Telegram User ID
```

## 🚀 Quick Start

### 1. Install Dependencies
```bash
cd /home/soarer/Documents/projects/freelance/Hotel-Workflow-Bot
python3 -m venv bot_env
source bot_env/bin/activate
pip install -r requirements.txt
```

### 2. Set Environment Variables (.env file)
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
GOOGLE_CREDENTIALS_FILE=credentials.json
SPREADSHEET_NAME=Hotel Workflow Data
ADMIN_USER_IDS=123456789,987654321
```

### 3. Get Your Telegram User ID
- Message the bot `/getid`
- It will show your Telegram User ID
- Use this to register staff members

### 4. Run the Bot
```bash
source bot_env/bin/activate
python3 hotel_bot.py
```

## 🧪 Testing the Bot

### Test Cleaning Log
1. Send `/clean` command
2. Enter room number (e.g., 101)
3. Select status (Not Started, In Progress, Done, Pending Review)
4. Check Google Sheets "Cleaning Log" - entry should appear with timestamp, staff name, and room number

### Test Maintenance Log
1. Send `/maintenance` command
2. Enter room number (e.g., 102)
3. Describe the issue (e.g., "Faucet leaking")
4. Select priority (Low, Medium, High, Critical)
5. Check Google Sheets "Maintenance Log" - entry should appear

### Test Task Completion
1. Send `/task` command
2. Enter task name (e.g., "Clean lobby")
3. Check Google Sheets "Task Completion Log" - entry should appear

### Test Reports
1. Admin sends `/today`
   - Should show count of today's entries for cleaning, maintenance, tasks
   - Shows last 3 entries from each category
   
2. Admin sends `/weekly`
   - Should show entries from last 7 days
   - Shows "Top Performers" ranked by activity count

3. Admin sends `/admin` then clicks buttons
   - "📊 Today's Reports" - same as `/today`
   - "📈 Weekly Summary" - same as `/weekly`
   - "👥 Staff List" - shows all registered staff
   - "📋 Full Reports" - link to Google Sheets

### Test Staff Management
1. New staff sends `/getid` to get their Telegram User ID
2. Admin sends `/addstaff`
3. Admin enters new staff's User ID
4. Admin enters staff name
5. Admin selects role (Staff or Admin)
6. New staff can now use `/start` and access bot

### Test Admin Notifications
1. Staff sends `/clean` and logs a room
2. Admin should receive alert: "🔔 Admin Alert\n\n🧹 *Cleaning Update*..."
3. Same for `/maintenance` and `/task`

## 📊 Google Sheets Structure

### Cleaning Log
| Timestamp | Room Number | Staff Name | Staff ID | Status | Notes |
|-----------|-------------|------------|----------|--------|-------|
| 2026-01-14 10:30:45 | 101 | John | 123456 | Done | |

### Maintenance Log
| Timestamp | Room Number | Issue | Staff Name | Staff ID | Priority | Status |
|-----------|-------------|-------|------------|----------|----------|--------|
| 2026-01-14 11:00:00 | 102 | Faucet broken | John | 123456 | HIGH | Open |

### Task Completion Log
| Timestamp | Task Name | Staff Name | Staff ID | Status |
|-----------|-----------|------------|----------|--------|
| 2026-01-14 09:15:30 | Clean lobby | John | 123456 | Completed |

### Staff Registry
| User ID | Name | Role | Date Added | Status |
|---------|------|------|------------|--------|
| 123456 | John Doe | staff | 2026-01-14 08:00:00 | active |

## 🔍 Troubleshooting

### Reports Show "0 entries"
- Ensure you've actually logged data via `/clean`, `/maintenance`, or `/task`
- Check that timestamps in Google Sheets match today's date
- Verify Google Sheets API permissions in credentials.json

### Admins Don't Receive Notifications
- Check that `ADMIN_USER_IDS` is set correctly in .env
- Admin must be registered in the system or in ADMIN_USER_IDS list
- Check bot logs for any errors

### Data Not Appearing in Google Sheets
- Run test_sheets.py to verify Google Sheets connection:
  ```bash
  source bot_env/bin/activate
  python3 test_sheets.py
  ```
- Check that credentials.json has proper permissions for Sheets API

### Staff Can't Access Bot
- Ensure they're registered via `/addstaff`
- Verify their User ID was entered correctly
- They should send `/start` after being added

## 📝 Code Quality

- Clean, well-commented Python code
- Proper error handling for all API calls
- Logging of all bot activities for debugging
- Role-based access control throughout
- Real-time admin notifications
- All data persists in Google Sheets

## 🔐 Security Notes

- Keep `credentials.json` private (never commit to git)
- Keep `TELEGRAM_BOT_TOKEN` in .env file only
- ADMIN_USER_IDS should contain trusted Telegram User IDs only
- Regularly audit staff registry for inactive users

## 📞 Support

For issues:
1. Check bot logs: `tail -f bot.log` (if enabled)
2. Run test_sheets.py to verify Sheets connection
3. Verify all environment variables are set correctly
4. Check Google Sheets API quota usage in Google Cloud Console
