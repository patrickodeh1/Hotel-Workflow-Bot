#!/usr/bin/env python3
"""Test script to debug Google Sheets integration"""

import os
import logging
from datetime import datetime, timedelta
from google.oauth2.service_account import Credentials
import gspread
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)
logger = logging.getLogger(__name__)

GOOGLE_CREDENTIALS_FILE = os.getenv('GOOGLE_CREDENTIALS_FILE', 'credentials.json')
SPREADSHEET_NAME = os.getenv('SPREADSHEET_NAME', 'Hotel Workflow Data')

def test_sheets_connection():
    """Test Google Sheets connection"""
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=scopes)
        client = gspread.authorize(creds)
        
        print(f"✅ Successfully authenticated with Google Sheets")
        
        try:
            sheet = client.open(SPREADSHEET_NAME)
            print(f"✅ Found spreadsheet: {SPREADSHEET_NAME}")
        except gspread.SpreadsheetNotFound:
            print(f"❌ Spreadsheet not found: {SPREADSHEET_NAME}")
            return False
        
        # Check worksheets
        worksheets = {ws.title: ws for ws in sheet.worksheets()}
        print(f"\n📋 Available worksheets:")
        for ws_name in worksheets:
            print(f"  - {ws_name}")
        
        # Test reading from each worksheet
        print(f"\n📊 Testing data access:")
        
        for ws_name in ['Cleaning Log', 'Maintenance Log', 'Task Completion Log', 'Staff Registry']:
            try:
                ws = sheet.worksheet(ws_name)
                records = ws.get_all_records()
                print(f"  ✅ {ws_name}: {len(records)} records")
                if records:
                    print(f"      Headers: {list(records[0].keys())}")
                    print(f"      Sample: {records[0]}")
            except Exception as e:
                print(f"  ❌ {ws_name}: {e}")
        
        return True
        
    except FileNotFoundError:
        print(f"❌ Credentials file not found: {GOOGLE_CREDENTIALS_FILE}")
        return False
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False

def test_data_logging():
    """Test logging data to sheets"""
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open(SPREADSHEET_NAME)
        
        print(f"\n✍️  Testing data logging:")
        
        # Test cleaning log
        test_data = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '101',
            'Test Staff',
            '123456',
            'In Progress',
            'Test entry'
        ]
        
        try:
            cleaning_ws = sheet.worksheet('Cleaning Log')
            cleaning_ws.append_row(test_data)
            print(f"  ✅ Successfully logged to Cleaning Log")
        except Exception as e:
            print(f"  ❌ Failed to log to Cleaning Log: {e}")
        
        # Test maintenance log
        test_data = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            '102',
            'Test issue',
            'Test Staff',
            '123456',
            'High',
            'Open'
        ]
        
        try:
            maintenance_ws = sheet.worksheet('Maintenance Log')
            maintenance_ws.append_row(test_data)
            print(f"  ✅ Successfully logged to Maintenance Log")
        except Exception as e:
            print(f"  ❌ Failed to log to Maintenance Log: {e}")
        
        # Test task log
        test_data = [
            datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'Test Task',
            'Test Staff',
            '123456',
            'Completed'
        ]
        
        try:
            tasks_ws = sheet.worksheet('Task Completion Log')
            tasks_ws.append_row(test_data)
            print(f"  ✅ Successfully logged to Task Completion Log")
        except Exception as e:
            print(f"  ❌ Failed to log to Task Completion Log: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Data logging test failed: {e}")
        return False

def test_report_generation():
    """Test report generation"""
    try:
        scopes = [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ]
        creds = Credentials.from_service_account_file(GOOGLE_CREDENTIALS_FILE, scopes=scopes)
        client = gspread.authorize(creds)
        sheet = client.open(SPREADSHEET_NAME)
        
        print(f"\n📈 Testing report generation:")
        
        today = datetime.now().strftime('%Y-%m-%d')
        week_ago = (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Test today's report
        print(f"\n  Today's date: {today}")
        cleaning_ws = sheet.worksheet('Cleaning Log')
        cleaning_data = cleaning_ws.get_all_records()
        today_cleaning = [r for r in cleaning_data if today in str(r.get('Timestamp', ''))]
        print(f"  🧹 Today's cleaning entries: {len(today_cleaning)}")
        
        maintenance_ws = sheet.worksheet('Maintenance Log')
        maintenance_data = maintenance_ws.get_all_records()
        today_maintenance = [r for r in maintenance_data if today in str(r.get('Timestamp', ''))]
        print(f"  🔧 Today's maintenance entries: {len(today_maintenance)}")
        
        tasks_ws = sheet.worksheet('Task Completion Log')
        tasks_data = tasks_ws.get_all_records()
        today_tasks = [r for r in tasks_data if today in str(r.get('Timestamp', ''))]
        print(f"  ✅ Today's task entries: {len(today_tasks)}")
        
        # Test weekly report
        print(f"\n  Week range: {week_ago} to {today}")
        week_cleaning = [r for r in cleaning_data if str(r.get('Timestamp', '')) >= week_ago]
        print(f"  🧹 Week's cleaning entries: {len(week_cleaning)}")
        
        week_maintenance = [r for r in maintenance_data if str(r.get('Timestamp', '')) >= week_ago]
        print(f"  🔧 Week's maintenance entries: {len(week_maintenance)}")
        
        week_tasks = [r for r in tasks_data if str(r.get('Timestamp', '')) >= week_ago]
        print(f"  ✅ Week's task entries: {len(week_tasks)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Report generation test failed: {e}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("Hotel Bot - Google Sheets Integration Test")
    print("=" * 60)
    
    if test_sheets_connection():
        test_data_logging()
        test_report_generation()
    
    print("\n" + "=" * 60)
    print("Tests completed!")
    print("=" * 60)
