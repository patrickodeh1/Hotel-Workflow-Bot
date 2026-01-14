# Hotel Workflow Bot - Technical Documentation

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    TELEGRAM BOT                              │
│                    (hotel_bot.py)                            │
└─────────────────────────────────────────────────────────────┘
                            │
                ┌───────────┼───────────┐
                │           │           │
            [Staff]     [Admin]    [Commands]
                │           │           │
                └───────────┼───────────┘
                            │
                    GOOGLE SHEETS API
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
    [Cleaning Log]  [Maintenance Log]  [Task Log]  [Staff Registry]
```

## File Structure

```
Hotel-Workflow-Bot/
├── hotel_bot.py                 # Main bot application
├── test_sheets.py               # Google Sheets integration tests
├── requirements.txt             # Python dependencies
├── credentials.json             # Google Service Account (KEEP SECURE!)
├── .env                         # Environment variables (KEEP SECURE!)
├── README.md                    # Basic project info
├── SETUP_AND_TESTING.md        # User guide and testing procedures
├── DEPLOYMENT.md               # Deployment and operations guide
└── bot_env/                    # Python virtual environment
    └── lib/python3.x/site-packages/  # Installed packages
```

## Code Organization

### 1. Configuration & Setup (Lines 1-115)
- Environment variable loading
- Logging setup
- Google Sheets initialization
- Conversation state definitions

**Key Functions:**
- `init_google_sheets()` - Connect to Google Sheets, create worksheets
- `is_admin(user_id)` - Check admin status
- `is_authorized(user_id)` - Check if user is registered
- `log_to_sheet(sheet_name, data)` - Append data to worksheet

### 2. Admin Functions (Lines 117-130)
- `notify_admins(context, message)` - Send real-time alerts to all admins

### 3. Basic Commands (Lines 132-190)
- `start(update, context)` - /start command, show welcome & available commands
- `getid_command(update, context)` - /getid command, show user's Telegram ID

### 4. Staff Commands (Lines 192-330)
- `clean_command()` - Initiate /clean flow
- `maintenance_command()` - Initiate /maintenance flow
- `task_command()` - Initiate /task flow
- `mystats_command()` - Show user's activity statistics

### 5. Admin Report Commands (Lines 332-465)
- `today_report()` - Generate today's activity report
- `weekly_report()` - Generate weekly summary
- `admin_panel()` - Show admin control buttons

### 6. Staff Management (Lines 467-565)
- `addstaff_start()` - Start staff addition flow
- `receive_staff_id()` - Get staff member's Telegram ID
- `receive_staff_name()` - Get staff member's name
- `finalize_staff_addition()` - Select role and register staff
- `removestaff_command()` - Show removal dialog
- `cancel_conversation()` - Cancel any conversation
- `staffguide_command()` - Show admin guide

### 7. Conversation Handlers (Lines 567-660)
- `handle_cleaning_room()` - Receive room number for cleaning
- `handle_maintenance_room()` - Receive room number for maintenance
- `handle_maintenance_issue()` - Receive issue description
- `handle_task_name()` - Receive task name
- `show_help()` - Show commands to user

### 8. Button Callbacks (Lines 662-890)
- `button_callback(update, context)` - Handle all button clicks
  - Status selection for cleaning
  - Priority selection for maintenance
  - Admin panel report generation
  - Staff member removal

### 9. Main & Initialization (Lines 892-955)
- `main()` - Application setup and polling

## Data Flow Diagrams

### Cleaning Flow
```
User: /clean
    ↓
Bot: "Enter room number"
    ↓
User: Types room number (e.g., "101")
    ↓
Bot: Displays status buttons
    ↓
User: Clicks status (e.g., "Done")
    ↓
Bot: Logs to "Cleaning Log" sheet
    ↓
Bot: Notifies all admins
    ↓
User: Gets confirmation
```

### Maintenance Flow
```
User: /maintenance
    ↓
Bot: "Enter room number"
    ↓
User: Types room number
    ↓
Bot: "Describe the issue"
    ↓
User: Types issue description
    ↓
Bot: Displays priority buttons
    ↓
User: Clicks priority
    ↓
Bot: Logs to "Maintenance Log" sheet
    ↓
Bot: Notifies all admins
    ↓
User: Gets confirmation
```

### Task Flow
```
User: /task
    ↓
Bot: "Enter task name"
    ↓
User: Types task name
    ↓
Bot: Logs to "Task Completion Log" sheet
    ↓
Bot: Notifies all admins
    ↓
User: Gets confirmation
```

### Report Generation Flow
```
Admin: /today
    ↓
Bot: Fetches all records from Cleaning Log
Bot: Filters for today's date
Bot: Fetches all records from Maintenance Log
Bot: Filters for today's date
Bot: Fetches all records from Task Log
Bot: Filters for today's date
    ↓
Bot: Formats and sends report with:
    - Count of entries
    - Last 3 entries from each log
    - Staff names
    ↓
Admin: Receives formatted report
```

## Conversation States

### Staff Addition Flow
```
States: STAFF_ID → STAFF_NAME → STAFF_ROLE → ConversationHandler.END

STAFF_ID:
  Input: Telegram User ID (numeric)
  Action: Store in context.user_data['new_staff_id']

STAFF_NAME:
  Input: Full name (text)
  Action: Store in context.user_data['new_staff_name']

STAFF_ROLE:
  Input: Button click (role_staff or role_admin)
  Action: 
    - Create staff_registry entry
    - Log to "Staff Registry" sheet
    - Send confirmation message
```

### Cleaning Flow
```
States: CLEANING_ROOM → CLEANING_STATUS → ConversationHandler.END

CLEANING_ROOM:
  Input: Room number (text)
  Action: Store in context.user_data['room_number']

CLEANING_STATUS:
  Input: Button click (status selection)
  Action:
    - Create log entry [timestamp, room, staff, status, notes]
    - Log to "Cleaning Log" sheet
    - Notify admins
    - Send confirmation
```

### Maintenance Flow
```
States: MAINTENANCE_ROOM → MAINTENANCE_ISSUE → MAINTENANCE_PRIORITY → END

MAINTENANCE_ROOM:
  Input: Room number
  Action: Store in context.user_data['room_number']

MAINTENANCE_ISSUE:
  Input: Issue description
  Action: Store in context.user_data['issue_description']

MAINTENANCE_PRIORITY:
  Input: Button click (priority selection)
  Action:
    - Create log entry [timestamp, room, issue, staff, priority, status]
    - Log to "Maintenance Log" sheet
    - Notify admins
    - Send confirmation
```

### Task Flow
```
States: TASK_NAME_STATE → ConversationHandler.END

TASK_NAME_STATE:
  Input: Task name (text)
  Action:
    - Create log entry [timestamp, task, staff, status]
    - Log to "Task Completion Log" sheet
    - Notify admins
    - Send confirmation
```

## Data Structures

### Cleaning Log Entry
```python
[
  "2026-01-14 10:30:45",          # Timestamp
  "101",                           # Room Number
  "John Doe",                      # Staff Name
  "123456789",                     # Staff ID
  "Done",                          # Status
  ""                               # Notes (optional)
]
```

### Maintenance Log Entry
```python
[
  "2026-01-14 11:00:00",          # Timestamp
  "102",                           # Room Number
  "Faucet leaking",                # Issue
  "John Doe",                      # Staff Name
  "123456789",                     # Staff ID
  "HIGH",                          # Priority
  "Open"                           # Status
]
```

### Task Completion Log Entry
```python
[
  "2026-01-14 09:15:30",          # Timestamp
  "Clean lobby",                   # Task Name
  "John Doe",                      # Staff Name
  "123456789",                     # Staff ID
  "Completed"                      # Status
]
```

### Staff Registry Entry
```python
{
  "new_staff_id": 123456789,
  "new_staff_name": "John Doe",
  "role": "staff"  # or "admin"
  "added_date": "2026-01-14 08:00:00",
  "status": "active"
}
```

## Error Handling

### Sheet Operations
```python
try:
    worksheet.append_row(data)
    return True
except Exception as e:
    logger.error(f"Failed to log to sheet: {e}")
    return False
```

### Admin Notifications
```python
for admin_id in ADMIN_IDS:
    try:
        await context.bot.send_message(...)
    except Exception as e:
        logger.error(f"Failed to notify admin {admin_id}: {e}")
        # Continue with next admin
```

### Report Generation
```python
try:
    data = worksheet.get_all_records()
    filtered = [r for r in data if condition]
    # Generate report
except Exception as e:
    logger.error(f"Failed to generate report: {e}")
    await message.reply_text(f"Error: {str(e)}")
```

## Security Considerations

### 1. Credentials Management
- `credentials.json`: Service account key (NEVER commit to git)
- `.env`: Bot token and admin IDs (NEVER commit to git)
- Recommendation: Use .gitignore to exclude these files

### 2. Access Control
- Only registered users can use the bot
- Only users in ADMIN_IDS can access admin commands
- Real-time admin notifications ensure oversight

### 3. Data Privacy
- All data stored in Google Sheets (encrypted at rest by Google)
- Data in transit encrypted (HTTPS/TLS)
- Sensitive data (like task details) not logged to console

### 4. Audit Trail
- Every action has timestamp in Google Sheets
- Staff name and ID recorded with each entry
- Admin notifications create event log

## Performance Considerations

### Google Sheets Quotas
- API quota: 500 requests per 100 seconds
- Cell limit: 10 million cells per sheet
- Action timing: Each user action = 1-3 API calls

### Optimization
- `get_all_records()` caches data briefly
- Admins should regularly archive old data
- Consider pagination for very large datasets (future phase)

## Testing Strategy

### Unit Testing
- Test sheet connection in `test_sheets.py`
- Verify data format before logging
- Check date filtering logic

### Integration Testing
- Test complete user flows
- Verify admin notifications
- Check report generation

### Manual Testing Checklist
- [ ] All staff commands work (clean, maintenance, task)
- [ ] Reports show correct data
- [ ] Admins receive notifications
- [ ] Staff management works (add/remove)
- [ ] Role-based access control works
- [ ] Non-command messages show help
- [ ] Data appears in Google Sheets

## Extension Points (Future Phases)

### Phase 2: Enhanced Features
```python
# Room status tracking
def update_room_status(room_id, status):
    # Track room state (occupied, cleaning, ready, maintenance)
    pass

# Task assignment
def assign_task(staff_id, task_description, deadline):
    # Assign specific tasks to staff
    pass

# Guest feedback integration
def log_guest_feedback(room_id, rating, comments):
    # Record guest satisfaction
    pass
```

### Phase 3: Dashboard
```python
# Web interface
from flask import Flask

app = Flask(__name__)

@app.route('/dashboard')
def dashboard():
    # Show real-time stats
    # Display reports
    # Manage staff
    pass
```

### Phase 4: Advanced Analytics
```python
# Analytics engine
def calculate_staff_performance(staff_id, period):
    # Rooms cleaned per day
    # Average issues reported
    # Task completion rate
    pass

def generate_revenue_report(period):
    # Revenue per staff member
    # Cost analysis
    # Efficiency metrics
    pass
```

## API Reference

### Internal Functions

#### `init_google_sheets() -> gspread.Spreadsheet`
Initializes Google Sheets connection and creates worksheets if needed.
- Returns: gspread client or None
- Raises: Logs errors, doesn't crash

#### `is_admin(user_id: int) -> bool`
Checks if user has admin privileges.
- Parameters: Telegram user ID
- Returns: True if admin, False otherwise

#### `is_authorized(user_id: int) -> bool`
Checks if user is authorized to use the bot.
- Parameters: Telegram user ID
- Returns: True if authorized, False otherwise

#### `log_to_sheet(sheet_name: str, data: list) -> bool`
Appends data to Google Sheets worksheet.
- Parameters:
  - sheet_name: Name of worksheet (e.g., 'Cleaning Log')
  - data: List of values to append
- Returns: True if successful, False if failed

#### `notify_admins(context: ContextTypes.DEFAULT_TYPE, message: str)`
Sends message to all admins.
- Parameters:
  - context: Telegram context object
  - message: Message text (supports Markdown)
- Side effects: Logs errors but continues

---

**Version**: 1.0.0
**Status**: Phase 1 Complete
**Last Updated**: 2026-01-14
**Next Phase**: 2.0 (Enhanced Features & Analytics)
