"""
Hotel Workflow Telegram Bot - Complete Production Version
A comprehensive role-based bot for managing hotel staff tasks, maintenance, and housekeeping.
"""

import os
import logging
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.error import TelegramError
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters
)
import gspread
from google.oauth2.service_account import Credentials
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
SPREADSHEET_NAME = os.getenv('SPREADSHEET_NAME', 'Hotel Workflow Data')

# Admin user IDs
ADMIN_IDS = [int(x) for x in os.getenv('ADMIN_USER_IDS', '').split(',') if x]

# Conversation states
STAFF_ID, STAFF_NAME, STAFF_ROLE = range(3)
CLEANING_ROOM, CLEANING_STATUS = range(3, 5)
MAINTENANCE_ROOM, MAINTENANCE_ISSUE, MAINTENANCE_PRIORITY = range(5, 8)
TASK_NAME_STATE = range(8, 9)

# Role management
user_roles = {}
staff_registry = {}

# Status options
CLEANING_STATUSES = ['Not Started', 'In Progress', 'Done', 'Pending Review']
MAINTENANCE_PRIORITIES = ['Low', 'Medium', 'High', 'Critical']

# Google Sheets setup
def init_google_sheets():
    """Initialize Google Sheets connection"""
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=scopes)
        client = gspread.authorize(creds)
        
        try:
            sheet = client.open(SPREADSHEET_NAME)
        except gspread.SpreadsheetNotFound:
            sheet = client.create(SPREADSHEET_NAME)
            logger.info(f"Created new spreadsheet: {SPREADSHEET_NAME}")
        
        worksheets = {ws.title: ws for ws in sheet.worksheets()}
        
        if 'Cleaning Log' not in worksheets:
            cleaning_ws = sheet.add_worksheet('Cleaning Log', 1000, 10)
            cleaning_ws.append_row(['Timestamp', 'Room Number', 'Staff Name', 'Staff ID', 'Status', 'Notes'])
        
        if 'Maintenance Log' not in worksheets:
            maintenance_ws = sheet.add_worksheet('Maintenance Log', 1000, 10)
            maintenance_ws.append_row(['Timestamp', 'Room Number', 'Issue', 'Staff Name', 'Staff ID', 'Priority', 'Status'])
        
        if 'Task Completion Log' not in worksheets:
            tasks_ws = sheet.add_worksheet('Task Completion Log', 1000, 10)
            tasks_ws.append_row(['Timestamp', 'Task Name', 'Staff Name', 'Staff ID', 'Status'])
        
        if 'Staff Registry' not in worksheets:
            staff_ws = sheet.add_worksheet('Staff Registry', 1000, 10)
            staff_ws.append_row(['User ID', 'Name', 'Role', 'Date Added', 'Status'])
        
        logger.info("Google Sheets initialized successfully")
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Google Sheets: {e}")
        return None

sheets_client = init_google_sheets()

def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in ADMIN_IDS or user_roles.get(user_id) == 'admin'

def is_authorized(user_id: int) -> bool:
    """Check if user is authorized"""
    return is_admin(user_id) or user_id in staff_registry

def log_to_sheet(sheet_name: str, data: list):
    """Log data to Google Sheets"""
    if not sheets_client:
        logger.error("Google Sheets client not initialized")
        return False
    
    try:
        sheet = sheets_client.open(SPREADSHEET_NAME)
        worksheet = sheet.worksheet(sheet_name)
        worksheet.append_row(data)
        return True
    except Exception as e:
        logger.error(f"Failed to log to sheet {sheet_name}: {e}")
        return False

async def notify_admins(context: ContextTypes.DEFAULT_TYPE, message: str):
    """Send notification to all admins"""
    for admin_id in ADMIN_IDS:
        try:
            await context.bot.send_message(chat_id=admin_id, text=f"🔔 *Admin Alert*\n\n{message}", parse_mode='Markdown')
        except Exception as e:
            logger.error(f"Failed to notify admin {admin_id}: {e}")

# ============= BASIC COMMANDS =============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command"""
    user = update.effective_user
    user_id = user.id
    
    if user_id in ADMIN_IDS:
        user_roles[user_id] = 'admin'
    
    if not is_authorized(user_id):
        await update.message.reply_text(
            "⚠️ *Unauthorized Access*\n\n"
            "You are not registered in the system.\n"
            "Please contact an administrator to get access.\n\n"
            f"Your User ID: `{user_id}`\n"
            "Share this ID with your admin.",
            parse_mode='Markdown'
        )
        return
    
    role = 'Admin' if is_admin(user_id) else 'Staff'
    
    welcome_msg = f"""
👋 Welcome to Hotel Workflow Bot, {user.first_name}!

**Your Role:** {role}

**Available Commands:**

📋 *Staff Commands:*
/clean - Mark room cleaning progress
/maintenance - Report maintenance issue
/task - Mark task as completed
/mystats - View your activity stats

"""
    
    if is_admin(user_id):
        welcome_msg += """
🔧 *Admin Commands:*
/admin - Open admin control panel
/addstaff - Register new staff member
/removestaff - Remove staff member
/liststaff - View all staff members
/today - View today's reports
/weekly - View weekly summary
/staffguide - Admin guide for managing staff
"""
    
    welcome_msg += "\n💡 Tip: Click any command to use it!"
    
    await update.message.reply_text(welcome_msg, parse_mode='Markdown')

async def getid_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user their Telegram ID"""
    user_id = update.effective_user.id
    user_name = update.effective_user.first_name
    
    await update.message.reply_text(
        f"👤 *Your Information*\n\n"
        f"Name: {user_name}\n"
        f"User ID: `{user_id}`\n\n"
        f"💡 Share this ID with an admin to get access.",
        parse_mode='Markdown'
    )

# ============= STAFF FUNCTIONS =============

async def clean_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clean command"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized. Contact admin for access.")
        return ConversationHandler.END
    
    context.user_data['action'] = 'cleaning'
    await update.message.reply_text(
        "🧹 *Room Cleaning*\n\nPlease enter the room number:",
        parse_mode='Markdown'
    )
    return CLEANING_ROOM

async def maintenance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /maintenance command"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized. Contact admin for access.")
        return ConversationHandler.END
    
    context.user_data['action'] = 'maintenance'
    await update.message.reply_text(
        "🔧 *Maintenance Report*\n\nPlease enter the room number:",
        parse_mode='Markdown'
    )
    return MAINTENANCE_ROOM

async def task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /task command"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized. Contact admin for access.")
        return ConversationHandler.END
    
    context.user_data['action'] = 'task'
    await update.message.reply_text(
        "📝 *Task Management*\n\nPlease enter the task name:",
        parse_mode='Markdown'
    )
    return TASK_NAME_STATE

async def mystats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show user's activity statistics"""
    user = update.effective_user
    user_id = user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized.")
        return
    
    if not sheets_client:
        await update.message.reply_text("❌ Statistics unavailable.")
        return
    
    try:
        sheet = sheets_client.open(SPREADSHEET_NAME)
        today = datetime.now().strftime('%Y-%m-%d')
        
        cleaning_ws = sheet.worksheet('Cleaning Log')
        cleaning_data = cleaning_ws.get_all_records()
        user_cleaning_today = len([r for r in cleaning_data if str(r.get('Staff ID', '')) == str(user_id) and today in str(r.get('Timestamp', ''))])
        user_cleaning_total = len([r for r in cleaning_data if str(r.get('Staff ID', '')) == str(user_id)])
        
        maintenance_ws = sheet.worksheet('Maintenance Log')
        maintenance_data = maintenance_ws.get_all_records()
        user_maintenance_today = len([r for r in maintenance_data if str(r.get('Staff ID', '')) == str(user_id) and today in str(r.get('Timestamp', ''))])
        user_maintenance_total = len([r for r in maintenance_data if str(r.get('Staff ID', '')) == str(user_id)])
        
        tasks_ws = sheet.worksheet('Task Completion Log')
        tasks_data = tasks_ws.get_all_records()
        user_tasks_today = len([r for r in tasks_data if str(r.get('Staff ID', '')) == str(user_id) and today in str(r.get('Timestamp', ''))])
        user_tasks_total = len([r for r in tasks_data if str(r.get('Staff ID', '')) == str(user_id)])
        
        stats = f"""
📊 *Your Activity Stats*

**Today ({today}):**
🧹 Cleaning: {user_cleaning_today} rooms
🔧 Maintenance: {user_maintenance_today} reports
✅ Tasks: {user_tasks_today} completed

**All Time:**
🧹 Cleaning: {user_cleaning_total} rooms
🔧 Maintenance: {user_maintenance_total} reports
✅ Tasks: {user_tasks_total} completed

Keep up the great work! 💪
"""
        
        await update.message.reply_text(stats, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Failed to get user stats: {e}")
        await update.message.reply_text("❌ Failed to load statistics.")

# ============= ADMIN COMMANDS =============

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    keyboard = [
        [
            InlineKeyboardButton("📊 Today's Reports", callback_data='admin_today'),
            InlineKeyboardButton("📈 Weekly Summary", callback_data='admin_weekly')
        ],
        [
            InlineKeyboardButton("👥 Staff List", callback_data='admin_staff'),
            InlineKeyboardButton("📋 Full Reports", callback_data='admin_fullreport')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 *Admin Control Panel*\n\nSelect an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def today_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate today's report"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    if not sheets_client:
        await update.message.reply_text("❌ Google Sheets not available.")
        return
    
    try:
        sheet = sheets_client.open(SPREADSHEET_NAME)
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get cleaning data
        cleaning_ws = sheet.worksheet('Cleaning Log')
        cleaning_data = cleaning_ws.get_all_records()
        today_cleaning = [r for r in cleaning_data if today in str(r.get('Timestamp', ''))]
        
        # Get maintenance data
        maintenance_ws = sheet.worksheet('Maintenance Log')
        maintenance_data = maintenance_ws.get_all_records()
        today_maintenance = [r for r in maintenance_data if today in str(r.get('Timestamp', ''))]
        
        # Get task data
        tasks_ws = sheet.worksheet('Task Completion Log')
        tasks_data = tasks_ws.get_all_records()
        today_tasks = [r for r in tasks_data if today in str(r.get('Timestamp', ''))]
        
        # Build report
        report = f"📊 *Today's Report* ({today})\n\n"
        
        # Cleaning section
        report += f"🧹 *Cleaning:* {len(today_cleaning)} rooms processed\n"
        if today_cleaning:
            report += "Recent updates:\n"
            for item in today_cleaning[-3:]:
                room = item.get('Room Number', 'N/A')
                status = item.get('Status', 'N/A')
                staff = item.get('Staff Name', 'Unknown')
                report += f"  • Room {room} → {status} ({staff})\n"
        else:
            report += "  No entries yet\n"
        
        report += "\n"
        
        # Maintenance section
        report += f"🔧 *Maintenance:* {len(today_maintenance)} issues reported\n"
        if today_maintenance:
            report += "Recent reports:\n"
            for item in today_maintenance[-3:]:
                room = item.get('Room Number', 'N/A')
                issue = str(item.get('Issue', 'N/A'))[:40]
                priority = item.get('Priority', 'N/A')
                report += f"  • Room {room}: {issue} ({priority})\n"
        else:
            report += "  No issues reported\n"
        
        report += "\n"
        
        # Tasks section
        report += f"✅ *Tasks:* {len(today_tasks)} completed\n"
        if today_tasks:
            report += "Recent tasks:\n"
            for item in today_tasks[-3:]:
                task = item.get('Task Name', 'N/A')
                staff = item.get('Staff Name', 'Unknown')
                report += f"  • {task} ({staff})\n"
        else:
            report += "  No tasks completed\n"
        
        report += "\n📊 Use /admin for more options."
        
        await update.message.reply_text(report, parse_mode='Markdown')
        logger.info(f"Today's report generated for admin {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to generate today's report: {e}")
        await update.message.reply_text(f"❌ Failed to generate report: {str(e)}")

async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate weekly summary"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    if not sheets_client:
        await update.message.reply_text("❌ Google Sheets not available.")
        return
    
    try:
        sheet = sheets_client.open(SPREADSHEET_NAME)
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        # Get cleaning data
        cleaning_ws = sheet.worksheet('Cleaning Log')
        cleaning_data = cleaning_ws.get_all_records()
        week_cleaning = [r for r in cleaning_data if str(r.get('Timestamp', '')) >= week_ago]
        
        # Get maintenance data
        maintenance_ws = sheet.worksheet('Maintenance Log')
        maintenance_data = maintenance_ws.get_all_records()
        week_maintenance = [r for r in maintenance_data if str(r.get('Timestamp', '')) >= week_ago]
        
        # Get task data
        tasks_ws = sheet.worksheet('Task Completion Log')
        tasks_data = tasks_ws.get_all_records()
        week_tasks = [r for r in tasks_data if str(r.get('Timestamp', '')) >= week_ago]
        
        # Build report
        report = f"📈 *Weekly Summary*\n({week_ago} to {today})\n\n"
        
        report += f"🧹 *Cleaning:* {len(week_cleaning)} rooms cleaned\n"
        report += f"🔧 *Maintenance:* {len(week_maintenance)} issues reported\n"
        report += f"✅ *Tasks:* {len(week_tasks)} tasks completed\n\n"
        
        # Top performers
        report += "📊 *Top Performers:*\n"
        staff_activity = {}
        for item in week_cleaning + week_maintenance + week_tasks:
            staff_name = item.get('Staff Name', 'Unknown')
            if staff_name and staff_name != 'Unknown':
                staff_activity[staff_name] = staff_activity.get(staff_name, 0) + 1
        
        if staff_activity:
            sorted_staff = sorted(staff_activity.items(), key=lambda x: x[1], reverse=True)
            for i, (name, count) in enumerate(sorted_staff[:5], 1):
                emoji = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][i-1]
                report += f"{emoji} {name}: {count} activities\n"
        else:
            report += "No staff activity this week.\n"
        
        report += "\n📊 Use /admin for more options."
        
        await update.message.reply_text(report, parse_mode='Markdown')
        logger.info(f"Weekly report generated for admin {user_id}")
        
    except Exception as e:
        logger.error(f"Failed to generate weekly report: {e}")
        await update.message.reply_text(f"❌ Failed to generate report: {str(e)}")

async def liststaff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all staff members"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    if not staff_registry:
        await update.message.reply_text("📭 No staff members registered yet.\n\nUse /addstaff to add members.")
        return
    
    staff_list = "👥 *Registered Staff Members*\n\n"
    
    admins = [info for sid, info in staff_registry.items() if info['role'] == 'admin']
    staff = [info for sid, info in staff_registry.items() if info['role'] == 'staff']
    
    if admins:
        staff_list += "👨‍💼 *Admins:*\n"
        for info in admins:
            staff_list += f"• {info['name']} (Added: {info['added_date'][:10]})\n"
        staff_list += "\n"
    
    if staff:
        staff_list += "👔 *Staff:*\n"
        for info in staff:
            staff_list += f"• {info['name']} (Added: {info['added_date'][:10]})\n"
    
    staff_list += f"\n📊 Total: {len(staff_registry)} members"
    
    await update.message.reply_text(staff_list, parse_mode='Markdown')

async def removestaff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove staff member"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    if not staff_registry:
        await update.message.reply_text("📭 No staff members registered yet.")
        return
    
    keyboard = []
    for sid, info in staff_registry.items():
        keyboard.append([InlineKeyboardButton(
            f"❌ {info['name']} ({info['role']})",
            callback_data=f'remove_{sid}'
        )])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "🗑️ *Remove Staff Member*\n\nSelect staff to remove:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def staffguide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin guide"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    guide = """
👨‍💼 *Admin Guide: Managing Staff*

**Adding Staff:**
1. Use /addstaff
2. Enter staff's User ID (they get it via /getid)
3. Enter their full name
4. Select role (Staff/Admin)

**Viewing Staff:**
Use /liststaff to see all registered staff

**Removing Staff:**
Use /removestaff and select from list

**Roles:**
👔 Staff - Can log activities
👨‍💼 Admin - Can manage staff & view reports

**Daily Operations:**
• /today - Today's activity report
• /weekly - Weekly summary
• /admin - Quick admin panel

Need help? Contact the bot developer.
"""
    
    await update.message.reply_text(guide, parse_mode='Markdown')

# ============= STAFF MANAGEMENT CONVERSATION =============

async def addstaff_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add staff conversation"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return ConversationHandler.END
    
    await update.message.reply_text(
        "➕ *Add New Staff Member*\n\n"
        "Please provide the staff member's Telegram User ID.\n"
        "They can get it by messaging /getid to this bot.\n\n"
        "Send /cancel to abort.",
        parse_mode='Markdown'
    )
    return STAFF_ID

async def receive_staff_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive staff ID"""
    try:
        staff_id = int(update.message.text.strip())
        context.user_data['new_staff_id'] = staff_id
        
        await update.message.reply_text(
            f"✅ User ID: `{staff_id}`\n\n"
            "Now, please enter the staff member's full name:",
            parse_mode='Markdown'
        )
        return STAFF_NAME
    except ValueError:
        await update.message.reply_text("❌ Invalid ID. Please enter a numeric user ID:")
        return STAFF_ID

async def receive_staff_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive staff name"""
    staff_name = update.message.text.strip()
    context.user_data['new_staff_name'] = staff_name
    
    keyboard = [
        [InlineKeyboardButton("👔 Staff", callback_data='role_staff')],
        [InlineKeyboardButton("👨‍💼 Admin", callback_data='role_admin')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ Name: {staff_name}\n\n"
        "Select role for this staff member:",
        reply_markup=reply_markup
    )
    return STAFF_ROLE

async def finalize_staff_addition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finalize staff addition"""
    query = update.callback_query
    await query.answer()
    
    role = 'admin' if query.data == 'role_admin' else 'staff'
    staff_id = context.user_data.get('new_staff_id')
    staff_name = context.user_data.get('new_staff_name')
    
    staff_registry[staff_id] = {
        'name': staff_name,
        'role': role,
        'added_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'active'
    }
    user_roles[staff_id] = role
    
    log_to_sheet('Staff Registry', [
        staff_id,
        staff_name,
        role,
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'active'
    ])
    
    await query.edit_message_text(
        f"✅ *Staff Added Successfully!*\n\n"
        f"Name: {staff_name}\n"
        f"User ID: `{staff_id}`\n"
        f"Role: {role.upper()}\n\n"
        f"They can now use the bot.",
        parse_mode='Markdown'
    )
    
    try:
        await context.bot.send_message(
            chat_id=staff_id,
            text=f"🎉 Welcome to Hotel Workflow Bot!\n\n"
                 f"You've been registered as: *{role.upper()}*\n"
                 f"Send /start to begin.",
            parse_mode='Markdown'
        )
    except:
        pass
    
    context.user_data.clear()
    return ConversationHandler.END

async def cancel_conversation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel conversation"""
    context.user_data.clear()
    await update.message.reply_text("❌ Operation cancelled.")
    return ConversationHandler.END

# ============= BUTTON CALLBACKS =============

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle button callbacks"""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    user = query.from_user
    user_id = user.id
    
    # Cleaning status selection
    if data.startswith('clean_status_'):
        status = data.replace('clean_status_', '').replace('_', ' ')
        room = context.user_data.get('room_number')
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_data = [timestamp, room, user.first_name, user.id, status, '']
        
        if log_to_sheet('Cleaning Log', log_data):
            await query.edit_message_text(f"✅ Room {room} marked as: *{status}*", parse_mode='Markdown')
            await notify_admins(
                context,
                f"🧹 *Cleaning Update*\nRoom: {room}\nStatus: {status}\nStaff: {user.first_name}"
            )
        else:
            await query.edit_message_text("❌ Failed to log. Please try again.")
        
        context.user_data.clear()
    
    # Maintenance priority selection
    elif data.startswith('maint_priority_'):
        priority = data.replace('maint_priority_', '').upper()
        room = context.user_data.get('room_number')
        issue = context.user_data.get('issue_description')
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_data = [timestamp, room, issue, user.first_name, user.id, priority, 'Open']
        
        if log_to_sheet('Maintenance Log', log_data):
            await query.edit_message_text(
                f"✅ *Maintenance Reported*\n\n"
                f"Room: {room}\n"
                f"Issue: {issue}\n"
                f"Priority: {priority}",
                parse_mode='Markdown'
            )
            await notify_admins(
                context,
                f"⚠️ *Maintenance Report*\nRoom: {room}\nIssue: {issue}\nPriority: {priority}\nBy: {user.first_name}"
            )
        else:
            await query.edit_message_text("❌ Failed to log. Please try again.")
        
        context.user_data.clear()
    
    # Admin panel callbacks - generate reports directly
    elif data == 'admin_today':
        if not is_admin(user_id):
            await query.answer("❌ Access denied")
            return
        
        if not sheets_client:
            await query.edit_message_text("❌ Google Sheets not available.")
            return
        
        try:
            sheet = sheets_client.open(SPREADSHEET_NAME)
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get all data
            cleaning_ws = sheet.worksheet('Cleaning Log')
            cleaning_data = cleaning_ws.get_all_records()
            today_cleaning = [r for r in cleaning_data if today in str(r.get('Timestamp', ''))]
            
            maintenance_ws = sheet.worksheet('Maintenance Log')
            maintenance_data = maintenance_ws.get_all_records()
            today_maintenance = [r for r in maintenance_data if today in str(r.get('Timestamp', ''))]
            
            tasks_ws = sheet.worksheet('Task Completion Log')
            tasks_data = tasks_ws.get_all_records()
            today_tasks = [r for r in tasks_data if today in str(r.get('Timestamp', ''))]
            
            # Build report
            report = f"📊 *Today's Report* ({today})\n\n"
            
            report += f"🧹 *Cleaning:* {len(today_cleaning)} rooms processed\n"
            if today_cleaning:
                report += "Recent updates:\n"
                for item in today_cleaning[-3:]:
                    room = item.get('Room Number', 'N/A')
                    status = item.get('Status', 'N/A')
                    staff = item.get('Staff Name', 'Unknown')
                    report += f"  • Room {room} → {status} ({staff})\n"
            else:
                report += "  No entries yet\n"
            
            report += "\n"
            
            report += f"🔧 *Maintenance:* {len(today_maintenance)} issues reported\n"
            if today_maintenance:
                report += "Recent reports:\n"
                for item in today_maintenance[-3:]:
                    room = item.get('Room Number', 'N/A')
                    issue = str(item.get('Issue', 'N/A'))[:40]
                    priority = item.get('Priority', 'N/A')
                    report += f"  • Room {room}: {issue} ({priority})\n"
            else:
                report += "  No issues reported\n"
            
            report += "\n"
            
            report += f"✅ *Tasks:* {len(today_tasks)} completed\n"
            if today_tasks:
                report += "Recent tasks:\n"
                for item in today_tasks[-3:]:
                    task = item.get('Task Name', 'N/A')
                    staff = item.get('Staff Name', 'Unknown')
                    report += f"  • {task} ({staff})\n"
            else:
                report += "  No tasks completed\n"
            
            await query.edit_message_text(report, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Failed to generate today's report from callback: {e}")
            await query.edit_message_text(f"❌ Failed to generate report: {str(e)}")
    
    elif data == 'admin_weekly':
        if not is_admin(user_id):
            await query.answer("❌ Access denied")
            return
        
        if not sheets_client:
            await query.edit_message_text("❌ Google Sheets not available.")
            return
        
        try:
            sheet = sheets_client.open(SPREADSHEET_NAME)
            week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
            today = datetime.now().strftime('%Y-%m-%d')
            
            # Get all data
            cleaning_ws = sheet.worksheet('Cleaning Log')
            cleaning_data = cleaning_ws.get_all_records()
            week_cleaning = [r for r in cleaning_data if str(r.get('Timestamp', '')) >= week_ago]
            
            maintenance_ws = sheet.worksheet('Maintenance Log')
            maintenance_data = maintenance_ws.get_all_records()
            week_maintenance = [r for r in maintenance_data if str(r.get('Timestamp', '')) >= week_ago]
            
            tasks_ws = sheet.worksheet('Task Completion Log')
            tasks_data = tasks_ws.get_all_records()
            week_tasks = [r for r in tasks_data if str(r.get('Timestamp', '')) >= week_ago]
            
            # Build report
            report = f"📈 *Weekly Summary*\n({week_ago} to {today})\n\n"
            
            report += f"🧹 *Cleaning:* {len(week_cleaning)} rooms cleaned\n"
            report += f"🔧 *Maintenance:* {len(week_maintenance)} issues reported\n"
            report += f"✅ *Tasks:* {len(week_tasks)} tasks completed\n\n"
            
            # Top performers
            report += "📊 *Top Performers:*\n"
            staff_activity = {}
            for item in week_cleaning + week_maintenance + week_tasks:
                staff_name = item.get('Staff Name', 'Unknown')
                if staff_name and staff_name != 'Unknown':
                    staff_activity[staff_name] = staff_activity.get(staff_name, 0) + 1
            
            if staff_activity:
                sorted_staff = sorted(staff_activity.items(), key=lambda x: x[1], reverse=True)
                for i, (name, count) in enumerate(sorted_staff[:5], 1):
                    emoji = ['🥇', '🥈', '🥉', '4️⃣', '5️⃣'][i-1]
                    report += f"{emoji} {name}: {count} activities\n"
            else:
                report += "No staff activity this week.\n"
            
            await query.edit_message_text(report, parse_mode='Markdown')
            
        except Exception as e:
            logger.error(f"Failed to generate weekly report from callback: {e}")
            await query.edit_message_text(f"❌ Failed to generate report: {str(e)}")
    
    elif data == 'admin_staff':
        if not is_admin(user_id):
            await query.answer("❌ Access denied")
            return
        
        if not staff_registry:
            await query.edit_message_text("📭 No staff members registered yet.\n\nUse /addstaff to add members.")
            return
        
        staff_list = "👥 *Registered Staff Members*\n\n"
        
        admins = [info for sid, info in staff_registry.items() if info['role'] == 'admin']
        staff = [info for sid, info in staff_registry.items() if info['role'] == 'staff']
        
        if admins:
            staff_list += "👨‍💼 *Admins:*\n"
            for info in admins:
                staff_list += f"• {info['name']} (Added: {info['added_date'][:10]})\n"
            staff_list += "\n"
        
        if staff:
            staff_list += "👔 *Staff:*\n"
            for info in staff:
                staff_list += f"• {info['name']} (Added: {info['added_date'][:10]})\n"
        
        staff_list += f"\n📊 Total: {len(staff_registry)} members"
        
        await query.edit_message_text(staff_list, parse_mode='Markdown')
    
    elif data == 'admin_fullreport':
        await query.edit_message_text(
            f"📋 *Full Reports in Google Sheets*\n\n"
            f"Sheet: {SPREADSHEET_NAME}\n\n"
            "Access Google Sheets for complete data.",
            parse_mode='Markdown'
        )
    
    elif data.startswith('remove_'):
        staff_id = int(data.replace('remove_', ''))
        if staff_id in staff_registry:
            staff_name = staff_registry[staff_id]['name']
            del staff_registry[staff_id]
            if staff_id in user_roles:
                del user_roles[staff_id]
            await query.edit_message_text(f"✅ '{staff_name}' has been removed.")
            
            try:
                await context.bot.send_message(
                    chat_id=staff_id,
                    text="⚠️ Your access has been revoked. Contact admin if needed."
                )
            except:
                pass
        else:
            await query.edit_message_text("❌ Staff member not found.")

# ============= TEXT INPUT HANDLER =============

async def handle_cleaning_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle room number input for cleaning"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized.")
        return ConversationHandler.END
    
    room_number = update.message.text.strip()
    context.user_data['room_number'] = room_number
    
    keyboard = [[InlineKeyboardButton(status, callback_data=f'clean_status_{status.replace(" ", "_")}')] for status in CLEANING_STATUSES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"✅ Room {room_number} selected.\n\nSelect status:",
        reply_markup=reply_markup
    )
    return CLEANING_STATUS

async def handle_maintenance_room(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle room number input for maintenance"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized.")
        return ConversationHandler.END
    
    room_number = update.message.text.strip()
    context.user_data['room_number'] = room_number
    
    await update.message.reply_text("🔧 Describe the issue:")
    return MAINTENANCE_ISSUE

async def handle_maintenance_issue(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle issue description for maintenance"""
    issue = update.message.text.strip()
    context.user_data['issue_description'] = issue
    
    keyboard = [[InlineKeyboardButton(f"{'🔴' if p == 'Critical' else '🟠' if p == 'High' else '🟡'} {p}", 
                                   callback_data=f'maint_priority_{p.lower()}')] for p in MAINTENANCE_PRIORITIES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"Room: {context.user_data['room_number']}\n"
        f"Issue: {issue}\n\n"
        f"Select priority:",
        reply_markup=reply_markup
    )
    return MAINTENANCE_PRIORITY

async def handle_task_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle task name input"""
    user = update.effective_user
    user_id = user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized.")
        return ConversationHandler.END
    
    task_name = update.message.text.strip()
    
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_data = [timestamp, task_name, user.first_name, user.id, 'Completed']
    
    if log_to_sheet('Task Completion Log', log_data):
        await update.message.reply_text(f"✅ Task completed: {task_name}")
        await notify_admins(
            context,
            f"📝 *Task Completed*\nTask: {task_name}\nBy: {user.first_name}"
        )
    else:
        await update.message.reply_text("❌ Failed to log task.")
    
    context.user_data.clear()
    return ConversationHandler.END

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show help message for non-command messages"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text(
            "⚠️ *Unauthorized Access*\n\n"
            "You are not registered in the system.\n"
            "Please contact an administrator to get access.\n\n"
            f"Your User ID: `{user_id}`",
            parse_mode='Markdown'
        )
        return
    
    help_msg = """
📋 *Available Commands:*

🧹 *Staff Commands:*
/clean - Mark room cleaning progress
/maintenance - Report maintenance issue
/task - Mark task as completed
/mystats - View your activity stats

"""
    
    if is_admin(user_id):
        help_msg += """🔧 *Admin Commands:*
/admin - Open admin control panel
/addstaff - Register new staff member
/removestaff - Remove staff member
/liststaff - View all staff members
/today - View today's reports
/weekly - View weekly summary
/staffguide - Admin guide for managing staff
"""
    
    help_msg += "\n💡 Send /start to see the welcome message"
    
    await update.message.reply_text(help_msg, parse_mode='Markdown')

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle fallback text input - show help"""
    await show_help(update, context)

# ============= MAIN =============

def main():
    """Start the bot"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Staff management conversation handler
    staff_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("addstaff", addstaff_start)],
        states={
            STAFF_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_staff_id)],
            STAFF_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_staff_name)],
            STAFF_ROLE: [CallbackQueryHandler(finalize_staff_addition, pattern='^role_')]
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)]
    )
    
    # Cleaning conversation handler
    clean_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("clean", clean_command)],
        states={
            CLEANING_ROOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_cleaning_room)],
            CLEANING_STATUS: [CallbackQueryHandler(button_callback, pattern='^clean_status_')]
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)]
    )
    
    # Maintenance conversation handler
    maintenance_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("maintenance", maintenance_command)],
        states={
            MAINTENANCE_ROOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_maintenance_room)],
            MAINTENANCE_ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_maintenance_issue)],
            MAINTENANCE_PRIORITY: [CallbackQueryHandler(button_callback, pattern='^maint_priority_')]
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)]
    )
    
    # Task conversation handler
    task_conv_handler = ConversationHandler(
        entry_points=[CommandHandler("task", task_command)],
        states={
            TASK_NAME_STATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_task_name)]
        },
        fallbacks=[CommandHandler("cancel", cancel_conversation)]
    )
    
    # Basic commands
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getid", getid_command))
    
    # Staff commands with conversation handlers
    application.add_handler(clean_conv_handler)
    application.add_handler(maintenance_conv_handler)
    application.add_handler(task_conv_handler)
    application.add_handler(CommandHandler("mystats", mystats_command))
    
    # Admin commands
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("today", today_report))
    application.add_handler(CommandHandler("weekly", weekly_report))
    application.add_handler(CommandHandler("liststaff", liststaff_command))
    application.add_handler(CommandHandler("removestaff", removestaff_command))
    application.add_handler(CommandHandler("staffguide", staffguide_command))
    
    # Conversation handler for staff management
    application.add_handler(staff_conv_handler)
    
    # Callback and text handlers (these should be last)
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    
    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()