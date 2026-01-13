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
AWAITING_ROOM, AWAITING_STATUS, AWAITING_ISSUE, AWAITING_TASK = range(4)
AWAITING_STAFF_ID, AWAITING_STAFF_ROLE, AWAITING_STAFF_NAME, AWAITING_PRIORITY = range(4, 8)

# Role management
user_roles = {}
staff_registry = {}  # {user_id: {'name': str, 'role': str, 'added_date': str, 'status': str}}

# Cleaning status options
CLEANING_STATUSES = ['Not Started', 'In Progress', 'Done', 'Pending Review']

# Maintenance priority options
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
        
        # Ensure worksheets exist
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
    """Check if user is authorized (admin or registered staff)"""
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

# Command Handlers

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
            "Your User ID: `{}`\n"
            "Share this ID with your admin.".format(user_id),
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
/reset - Reset daily task lists
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

async def clean_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /clean command with interactive buttons"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized. Contact admin for access.")
        return
    
    keyboard = [
        [InlineKeyboardButton("🏨 Enter Room Number", callback_data='clean_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🧹 *Room Cleaning*\n\nClick below to start:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def maintenance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /maintenance command with interactive buttons"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized. Contact admin for access.")
        return
    
    keyboard = [
        [InlineKeyboardButton("🔧 Report Issue", callback_data='maintenance_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 *Maintenance Report*\n\nClick below to start:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def task_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /task command with interactive buttons"""
    user_id = update.effective_user.id
    
    if not is_authorized(user_id):
        await update.message.reply_text("❌ Unauthorized. Contact admin for access.")
        return
    
    keyboard = [
        [InlineKeyboardButton("✅ Mark Task Complete", callback_data='task_start')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "📝 *Task Management*\n\nClick below to start:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

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

async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /admin command - show admin control panel"""
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
            InlineKeyboardButton("➕ Add Staff", callback_data='admin_addstaff')
        ],
        [
            InlineKeyboardButton("🔄 Reset Tasks", callback_data='admin_reset'),
            InlineKeyboardButton("📋 Full Reports", callback_data='admin_fullreport')
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "🔧 *Admin Control Panel*\n\nSelect an option:",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def addstaff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start add staff conversation"""
    # Handle both Update and CallbackQuery objects
    if hasattr(update, 'effective_user'):
        user_id = update.effective_user.id
        reply_func = update.message.reply_text
    else:  # CallbackQuery
        user_id = update.from_user.id
        reply_func = update.edit_message_text
    
    if not is_admin(user_id):
        await reply_func("❌ Access denied. Admin only.")
        return ConversationHandler.END
    
    await reply_func(
        "➕ *Add New Staff Member*\n\n"
        "Please provide the staff member's Telegram User ID.\n"
        "They can get it by messaging /getid to this bot.\n\n"
        "Send /cancel to abort.",
        parse_mode='Markdown'
    )
    return AWAITING_STAFF_ID

async def receive_staff_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive staff ID and ask for name"""
    try:
        staff_id = int(update.message.text.strip())
        context.user_data['new_staff_id'] = staff_id
        
        await update.message.reply_text(
            f"✅ User ID: `{staff_id}`\n\n"
            "Now, please enter the staff member's full name:",
            parse_mode='Markdown'
        )
        return AWAITING_STAFF_NAME
    except ValueError:
        await update.message.reply_text("❌ Invalid ID. Please enter a numeric user ID:")
        return AWAITING_STAFF_ID

async def receive_staff_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Receive staff name and ask for role"""
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
    return AWAITING_STAFF_ROLE

async def finalize_staff_addition(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Finalize staff addition"""
    query = update.callback_query
    await query.answer()
    
    role = 'admin' if query.data == 'role_admin' else 'staff'
    staff_id = context.user_data['new_staff_id']
    staff_name = context.user_data['new_staff_name']
    
    # Add to registry
    staff_registry[staff_id] = {
        'name': staff_name,
        'role': role,
        'added_date': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'active'
    }
    user_roles[staff_id] = role
    
    # Log to Google Sheets
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
    
    # Notify the new staff member
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
    
    return ConversationHandler.END

async def removestaff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Remove staff member"""
    # Handle both Update and CallbackQuery objects
    if hasattr(update, 'effective_user'):
        user_id = update.effective_user.id
        reply_func = update.message.reply_text
    else:  # CallbackQuery
        user_id = update.from_user.id
        reply_func = update.edit_message_text
    
    if not is_admin(user_id):
        await reply_func("❌ Access denied. Admin only.")
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

async def liststaff_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """List all staff members"""
    # Handle both Update and CallbackQuery objects
    if hasattr(update, 'effective_user'):
        user_id = update.effective_user.id
        reply_func = update.message.reply_text
    else:  # CallbackQuery
        user_id = update.from_user.id
        reply_func = update.edit_message_text
    
    if not is_admin(user_id):
        await reply_func("❌ Access denied. Admin only.")
        return
    
    if not staff_registry:
        await reply_func("📭 No staff members registered yet.\n\nUse /addstaff to add members.")
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

async def staffguide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show admin guide for managing staff"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    guide = """
👨‍💼 *Admin Guide: Managing Staff*

**How to Add Staff Members:**

1. Use the command: /addstaff
2. Enter the staff member's User ID (they get it with /getid)
3. Enter their full name
4. Select their role (Staff or Admin)
5. They'll receive a welcome message and can start using the bot

**How to View Staff:**

Use: /liststaff
Shows all registered staff with their roles and join dates.

**How to Remove Staff:**

Use: /removestaff
Select the staff member to remove from the list.

**Roles Explanation:**

👔 *Staff:* Can log cleaning, maintenance, and tasks
👨‍💼 *Admin:* Can manage staff, view reports, and reset tasks

**Tips:**
• Always verify User IDs before adding staff
• Staff need to send /getid command to get their User ID
• Use /today for daily reports
• Use /weekly for weekly summaries
• Use /liststaff to manage staff efficiently

**Workflow for New Staff:**
1. New staff member sends /getid to bot
2. They share the User ID with you
3. You use /addstaff with their ID
4. System automatically welcomes them
5. They send /start to begin working

Need more help? Contact the bot developer.
"""
    
    await update.message.reply_text(guide, parse_mode='Markdown')

async def today_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /today command - view today's reports"""
    # Handle both Update and CallbackQuery objects
    if hasattr(update, 'effective_user'):
        user_id = update.effective_user.id
        reply_func = update.message.reply_text
    else:  # CallbackQuery
        user_id = update.from_user.id
        reply_func = update.edit_message_text
    
    if not is_admin(user_id):
        await reply_func("❌ Access denied. Admin only.")
        return
    
    if not sheets_client:
        await reply_func("❌ Google Sheets not available.")
        return
    
    try:
        sheet = sheets_client.open(SPREADSHEET_NAME)
        today = datetime.now().strftime('%Y-%m-%d')
        
        cleaning_ws = sheet.worksheet('Cleaning Log')
        cleaning_data = cleaning_ws.get_all_records()
        today_cleaning = [r for r in cleaning_data if today in str(r.get('Timestamp', ''))]
        
        maintenance_ws = sheet.worksheet('Maintenance Log')
        maintenance_data = maintenance_ws.get_all_records()
        today_maintenance = [r for r in maintenance_data if today in str(r.get('Timestamp', ''))]
        
        tasks_ws = sheet.worksheet('Task Completion Log')
        tasks_data = tasks_ws.get_all_records()
        today_tasks = [r for r in tasks_data if today in str(r.get('Timestamp', ''))]
        
        report = f"""
📊 *Today's Report* ({today})

🧹 *Cleaning:* {len(today_cleaning)} rooms processed
"""
        
        # Show cleaning details with safe indexing
        if today_cleaning and len(today_cleaning) > 0:
            report += "\nRecent cleaning activities:\n"
            for item in today_cleaning[-3:]:
                room = item.get('Room Number', 'N/A')
                status = item.get('Status', 'N/A')
                staff = item.get('Staff Name', 'Unknown')
                report += f"  • Room {room} - {status} (by {staff})\n"
        
        report += f"\n🔧 *Maintenance:* {len(today_maintenance)} issues reported\n"
        
        # Show maintenance details with safe indexing
        if today_maintenance and len(today_maintenance) > 0:
            report += "Recent maintenance reports:\n"
            for item in today_maintenance[-3:]:
                room = item.get('Room Number', 'N/A')
                issue = item.get('Issue', 'N/A')
                priority = item.get('Priority', 'N/A')
                staff = item.get('Staff Name', 'Unknown')
                report += f"  • Room {room}: {issue[:30]}... (Priority: {priority}, by {staff})\n"
        
        report += f"\n✅ *Tasks:* {len(today_tasks)} completed\n"
        
        # Show task details with safe indexing
        if today_tasks and len(today_tasks) > 0:
            report += "Recently completed tasks:\n"
            for item in today_tasks[-3:]:
                task = item.get('Task Name', 'N/A')
                staff = item.get('Staff Name', 'Unknown')
                report += f"  • {task} (by {staff})\n"
        
        report += "\nUse /admin for more options."
        
        await reply_func(report, parse_mode='Markdown')
        
    except IndexError as e:
        logger.error(f"Index error in today's report: {e}")
        await reply_func("❌ Error generating report. The data might be empty or corrupted. Please try again later.")
    except Exception as e:
        logger.error(f"Failed to generate today's report: {e}")
        await reply_func("❌ Failed to generate report. Please try again later.")

async def weekly_report(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate weekly summary"""
    # Handle both Update and CallbackQuery objects
    if hasattr(update, 'effective_user'):
        user_id = update.effective_user.id
        reply_func = update.message.reply_text
    else:  # CallbackQuery
        user_id = update.from_user.id
        reply_func = update.edit_message_text
    
    if not is_admin(user_id):
        await reply_func("❌ Access denied. Admin only.")
        return
    
    if not sheets_client:
        await reply_func("❌ Google Sheets not available.")
        return
    
    try:
        sheet = sheets_client.open(SPREADSHEET_NAME)
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        today = datetime.now().strftime('%Y-%m-%d')
        
        cleaning_ws = sheet.worksheet('Cleaning Log')
        cleaning_data = cleaning_ws.get_all_records()
        week_cleaning = [r for r in cleaning_data if str(r.get('Timestamp', '')) >= week_ago]
        
        maintenance_ws = sheet.worksheet('Maintenance Log')
        maintenance_data = maintenance_ws.get_all_records()
        week_maintenance = [r for r in maintenance_data if str(r.get('Timestamp', '')) >= week_ago]
        
        tasks_ws = sheet.worksheet('Task Completion Log')
        tasks_data = tasks_ws.get_all_records()
        week_tasks = [r for r in tasks_data if str(r.get('Timestamp', '')) >= week_ago]
        
        report = f"""
📈 *Weekly Summary*
(From {week_ago} to {today})

🧹 *Cleaning:* {len(week_cleaning)} rooms processed
🔧 *Maintenance:* {len(week_maintenance)} issues reported
✅ *Tasks:* {len(week_tasks)} completed

📊 *Top Performers:*
"""
        
        # Count activities by staff with safe access
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
            report += "No activity recorded this week.\n"
        
        await reply_func(report, parse_mode='Markdown')
        
    except Exception as e:
        logger.error(f"Failed to generate weekly report: {e}")
        await reply_func("❌ Failed to generate weekly report.")

async def reset_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /reset command"""
    user_id = update.effective_user.id
    
    if not is_admin(user_id):
        await update.message.reply_text("❌ Access denied. Admin only.")
        return
    
    keyboard = [
        [InlineKeyboardButton("✅ Yes, Reset", callback_data='confirm_reset')],
        [InlineKeyboardButton("❌ Cancel", callback_data='cancel_reset')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        "⚠️ *Reset Daily Tasks*\n\n"
        "This will clear today's pending tasks.\n"
        "Completed tasks will remain in logs.\n\n"
        "Are you sure?",
        reply_markup=reply_markup,
        parse_mode='Markdown'
    )

async def safe_edit_message(query, text=None, reply_markup=None, parse_mode=None):
    """Safely edit message, handling the case where nothing changed"""
    try:
        if text is None:
            # If no text provided, just update the keyboard
            await query.edit_message_reply_markup(reply_markup=reply_markup)
        else:
            await query.edit_message_text(
                text=text,
                reply_markup=reply_markup,
                parse_mode=parse_mode
            )
    except TelegramError as e:
        if "Message is not modified" in str(e):
            # Message hasn't changed, just answer the query silently
            pass
        else:
            logger.error(f"Telegram error: {e}")

async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all button callbacks"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    data = query.data
    
    # Cleaning flow
    if data == 'clean_start':
        await safe_edit_message(query, text="🏨 Please enter the room number:")
        context.user_data['action'] = 'cleaning'
        return AWAITING_ROOM
    
    elif data.startswith('clean_status_'):
        status = data.replace('clean_status_', '').replace('_', ' ')
        room = context.user_data.get('room_number')
        user = query.from_user
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_data = [timestamp, room, user.first_name, user.id, status, '']
        
        if log_to_sheet('Cleaning Log', log_data):
            await safe_edit_message(query, text=f"✅ Room {room} marked as: *{status}*", parse_mode='Markdown')
            await notify_admins(
                context,
                f"🧹 *Cleaning Update*\nRoom: {room}\nStatus: {status}\nStaff: {user.first_name}"
            )
        else:
            await safe_edit_message(query, text="❌ Failed to log. Please try again.")
    
    # Maintenance flow
    elif data == 'maintenance_start':
        await safe_edit_message(query, text="🏨 Please enter the room number for maintenance:")
        context.user_data['action'] = 'maintenance'
        return AWAITING_ROOM
    
    elif data.startswith('maint_issue_'):
        # Skip to priority selection after issue is captured
        priority_keyboard = [[InlineKeyboardButton(f"🔴 {p}", callback_data=f'maint_priority_{p.lower()}')] for p in MAINTENANCE_PRIORITIES]
        await safe_edit_message(
            query,
            text=f"📍 Room: {context.user_data.get('room_number')}\n"
                f"⚠️ Issue: {context.user_data.get('issue_description')}\n\n"
                f"Select priority level:",
            reply_markup=InlineKeyboardMarkup(priority_keyboard)
        )
    
    elif data.startswith('maint_priority_'):
        priority = data.replace('maint_priority_', '').upper()
        room = context.user_data.get('room_number')
        issue = context.user_data.get('issue_description')
        user = query.from_user
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_data = [timestamp, room, issue, user.first_name, user.id, priority, 'Open']
        
        if log_to_sheet('Maintenance Log', log_data):
            await safe_edit_message(
                query,
                text=f"✅ *Maintenance Reported*\n\n"
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
            await safe_edit_message(query, text="❌ Failed to log. Please try again.")
    
    # Task flow
    elif data == 'task_start':
        await safe_edit_message(query, text="📝 Please enter the task name:")
        context.user_data['action'] = 'task'
        return AWAITING_TASK
    
    # Admin panel callbacks
    elif data == 'admin_today':
        await today_report(query, context)
    
    elif data == 'admin_weekly':
        await weekly_report(query, context)
    
    elif data == 'admin_staff':
        await liststaff_command(query, context)
    
    elif data == 'admin_addstaff':
        await addstaff_command(query, context)
    
    elif data == 'admin_reset':
        await safe_edit_message(query, text="🔄 Daily tasks have been reset.")
    
    elif data == 'admin_fullreport':
        await safe_edit_message(
            query,
            text="📋 *Full Reports Available in Google Sheets*\n\n"
                f"Sheet: {SPREADSHEET_NAME}\n\n"
                "Access your Google Sheets to view complete data.",
            parse_mode='Markdown'
        )
    
    elif data.startswith('remove_'):
        staff_id = int(data.replace('remove_', ''))
        if staff_id in staff_registry:
            staff_name = staff_registry[staff_id]['name']
            del staff_registry[staff_id]
            if staff_id in user_roles:
                del user_roles[staff_id]
            await safe_edit_message(query, text=f"✅ Staff member '{staff_name}' has been removed.")
        else:
            await safe_edit_message(query, text="❌ Staff member not found.")
    
    elif data == 'confirm_reset':
        await safe_edit_message(query, text="✅ Tasks reset for the day.")
    
    elif data == 'cancel_reset':
        await query.edit_message_text("❌ Reset cancelled.")

async def handle_text_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text input for various flows"""
    user_id = update.effective_user.id
    text = update.message.text.strip()
    action = context.user_data.get('action')
    
    if action == 'cleaning':
        if 'room_number' not in context.user_data:
            context.user_data['room_number'] = text
            
            # Show status options
            keyboard = [[InlineKeyboardButton(status, callback_data=f'clean_status_{status.replace(" ", "_")}')] for status in CLEANING_STATUSES]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"Room {text} selected.\n\nSelect cleaning status:",
                reply_markup=reply_markup
            )
    
    elif action == 'maintenance':
        if 'room_number' not in context.user_data:
            context.user_data['room_number'] = text
            await update.message.reply_text("🔧 Please describe the maintenance issue:")
        elif 'issue_description' not in context.user_data:
            context.user_data['issue_description'] = text
            
            # Show priority options
            keyboard = [[InlineKeyboardButton(f"{'🔴' if p == 'Critical' else '🟠' if p == 'High' else '🟡'} {p}", 
                                           callback_data=f'maint_priority_{p.lower()}')] for p in MAINTENANCE_PRIORITIES]
            reply_markup = InlineKeyboardMarkup(keyboard)
            
            await update.message.reply_text(
                f"Room: {context.user_data['room_number']}\n"
                f"Issue: {text}\n\n"
                f"Select priority level:",
                reply_markup=reply_markup
            )
    
    elif action == 'task':
        if 'task_name' not in context.user_data:
            context.user_data['task_name'] = text
            user = update.effective_user
            
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            log_data = [timestamp, text, user.first_name, user.id, 'Completed']
            
            if log_to_sheet('Task Completion Log', log_data):
                await update.message.reply_text(f"✅ Task completed: {text}")
                await notify_admins(
                    context,
                    f"📝 *Task Completed*\nTask: {text}\nCompleted by: {user.first_name}"
                )
            else:
                await update.message.reply_text("❌ Failed to log task. Please try again.")

def main():
    """Start the bot"""
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_BOT_TOKEN not set!")
        return
    
    # Create application
    application = Application.builder().token(TELEGRAM_TOKEN).build()
    
    # Add conversation handler for staff management
    add_staff_conv = ConversationHandler(
        entry_points=[CommandHandler("addstaff", addstaff_command)],
        states={
            AWAITING_STAFF_ID: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_staff_id)],
            AWAITING_STAFF_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_staff_name)],
            AWAITING_STAFF_ROLE: [CallbackQueryHandler(finalize_staff_addition)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    
    # Add conversation handler for interactive actions
    action_conv = ConversationHandler(
        entry_points=[
            CallbackQueryHandler(button_callback, pattern='^(clean_start|maintenance_start|task_start)$')
        ],
        states={
            AWAITING_ROOM: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            AWAITING_STATUS: [CallbackQueryHandler(button_callback, pattern='^clean_status_')],
            AWAITING_ISSUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)],
            AWAITING_PRIORITY: [CallbackQueryHandler(button_callback, pattern='^maint_priority_')],
            AWAITING_TASK: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input)]
        },
        fallbacks=[CommandHandler("cancel", lambda u, c: ConversationHandler.END)]
    )
    
    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("getid", getid_command))
    application.add_handler(CommandHandler("clean", clean_command))
    application.add_handler(CommandHandler("maintenance", maintenance_command))
    application.add_handler(CommandHandler("task", task_command))
    application.add_handler(CommandHandler("mystats", mystats_command))
    application.add_handler(CommandHandler("admin", admin_panel))
    application.add_handler(CommandHandler("liststaff", liststaff_command))
    application.add_handler(CommandHandler("removestaff", removestaff_command))
    application.add_handler(CommandHandler("staffguide", staffguide_command))
    application.add_handler(CommandHandler("today", today_report))
    application.add_handler(CommandHandler("weekly", weekly_report))
    application.add_handler(CommandHandler("reset", reset_tasks))
    
    application.add_handler(add_staff_conv)
    application.add_handler(action_conv)
    
    application.add_handler(CallbackQueryHandler(button_callback))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_input))
    
    # Start bot
    logger.info("Bot starting...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
