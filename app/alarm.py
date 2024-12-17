import os
import json
import logging
import requests
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
from config import ALARM_CONFIG, LIGHT_PATTERNS, TIME_FORMATS, PATHS

logger = logging.getLogger(__name__)

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

class AlarmManager:
    def __init__(self):
        """Initialize the alarm manager."""
        self.alarms = []
        self.events = []
        self.config = self._load_config()
        self.creds = self._get_google_credentials()
        self.last_sync = None
        self.sync_interval = timedelta(minutes=5)
        logger.info("Alarm manager initialized")

    def _load_config(self):
        """Load alarm configuration."""
        try:
            return {
                'default_sound': ALARM_CONFIG['DEFAULT_SOUND'],
                'rgb_enabled': True,
                'rgb_pattern': LIGHT_PATTERNS['default'],
                'time_format': TIME_FORMATS['24h'],
                'sounds_dir': PATHS['SOUNDS_DIR']
            }
        except Exception as e:
            logger.error(f"Error loading config: {str(e)}")
            return {
                'default_sound': 'standard_alarm.mp3',
                'rgb_enabled': True,
                'rgb_pattern': 'default',
                'time_format': '24h',
                'sounds_dir': 'sounds'
            }

    def _get_google_credentials(self):
        """Get Google Calendar API credentials."""
        creds = None
        if os.path.exists('token.json'):
            try:
                creds = Credentials.from_authorized_user_file('token.json', SCOPES)
            except Exception as e:
                logger.error(f"Error loading credentials: {str(e)}")

        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                try:
                    creds.refresh(Request())
                except Exception as e:
                    logger.error(f"Error refreshing credentials: {str(e)}")
                    return None
            else:
                try:
                    flow = InstalledAppFlow.from_client_secrets_file(
                        'credentials.json', SCOPES)
                    creds = flow.run_local_server(port=0)
                    # Save the credentials for the next run
                    with open('token.json', 'w') as token:
                        token.write(creds.to_json())
                except Exception as e:
                    logger.error(f"Error in OAuth flow: {str(e)}")
                    return None

        return creds

    def sync_calendar_events(self):
        """Sync events from Google Calendar."""
        if not self.creds:
            logger.error("No valid credentials available")
            return

        try:
            service = build('calendar', 'v3', credentials=self.creds)
            
            # Get the start of today and end of next week
            now = datetime.utcnow().isoformat() + 'Z'
            week_later = (datetime.utcnow() + timedelta(days=7)).isoformat() + 'Z'
            
            events_result = service.events().list(
                calendarId='primary',
                timeMin=now,
                timeMax=week_later,
                maxResults=10,
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            
            # Process events
            self.events = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                
                # Convert to datetime object
                if 'T' in start:  # DateTime
                    start_time = datetime.fromisoformat(start.replace('Z', '+00:00'))
                else:  # Date only
                    start_time = datetime.strptime(start, '%Y-%m-%d')
                
                self.events.append({
                    'id': event['id'],
                    'title': event['summary'],
                    'start_time': start_time,
                    'description': event.get('description', ''),
                    'has_alarm': bool(event.get('reminders', {}).get('useDefault', True))
                })
            
            self.last_sync = datetime.now()
            logger.info(f"Synced {len(self.events)} calendar events")
            
        except Exception as e:
            logger.error(f"Error syncing calendar events: {str(e)}")

    def check_alarms(self):
        """Check if any alarms should be triggered."""
        now = datetime.now()
        
        # Sync calendar if needed
        if not self.last_sync or (now - self.last_sync) > self.sync_interval:
            self.sync_calendar_events()
        
        # Check regular alarms
        for alarm in self.alarms:
            if self._should_trigger_alarm(alarm, now):
                return True
        
        # Check calendar events
        for event in self.events:
            if event['has_alarm']:
                # Trigger 15 minutes before event
                trigger_time = event['start_time'] - timedelta(minutes=15)
                if self._is_trigger_time(trigger_time, now):
                    return True
        
        return False

    def _should_trigger_alarm(self, alarm, current_time):
        """Check if a specific alarm should be triggered."""
        if not alarm.get('enabled', False):
            return False
            
        alarm_time = datetime.strptime(alarm['time'], '%H:%M').time()
        current_time = current_time.time()
        
        # Check if it's time to trigger
        if self._is_trigger_time(alarm_time, current_time):
            # Check recurrence
            if alarm.get('recurring', False):
                # Check if today is in recurring days
                if current_time.strftime('%A').lower() in alarm.get('days', []):
                    return True
            else:
                # One-time alarm
                if alarm.get('date'):
                    alarm_date = datetime.strptime(alarm['date'], '%Y-%m-%d').date()
                    if alarm_date == current_time.date():
                        return True
                else:
                    return True
        
        return False

    def _is_trigger_time(self, alarm_time, current_time):
        """Check if current time matches trigger time."""
        # Convert to comparable format
        if isinstance(alarm_time, datetime):
            alarm_time = alarm_time.time()
        if isinstance(current_time, datetime):
            current_time = current_time.time()
            
        return (alarm_time.hour == current_time.hour and
                alarm_time.minute == current_time.minute)

    def get_current_alarm_config(self):
        """Get configuration for currently triggering alarm."""
        return {
            'sound_file': self.config.get('default_sound', 'standard_alarm.mp3'),
            'rgb_enabled': self.config.get('rgb_enabled', True),
            'rgb_pattern': self.config.get('rgb_pattern', 'default')
        }

    def get_upcoming_events(self):
        """Get list of upcoming events."""
        now = datetime.now()
        upcoming = []
        
        # Add regular alarms
        for alarm in self.alarms:
            if alarm.get('enabled', False):
                alarm_time = datetime.strptime(alarm['time'], '%H:%M').time()
                if alarm_time > now.time():
                    upcoming.append({
                        'title': alarm.get('title', 'Alarm'),
                        'time': alarm_time.strftime(self._get_time_format())
                    })
        
        # Add calendar events
        for event in self.events:
            if event['start_time'] > now:
                upcoming.append({
                    'title': event['title'],
                    'time': event['start_time'].strftime(self._get_time_format())
                })
        
        # Sort by time and limit to next 5 events
        upcoming.sort(key=lambda x: datetime.strptime(x['time'], self._get_time_format()))
        return upcoming[:5]

    def _get_time_format(self):
        """Get time format based on configuration."""
        return '%I:%M %p' if self.config.get('time_format') == '12h' else '%H:%M'

    def add_alarm(self, alarm_data):
        """Add a new alarm."""
        self.alarms.append(alarm_data)
        logger.info(f"Added new alarm: {alarm_data}")

    def remove_alarm(self, alarm_id):
        """Remove an alarm by ID."""
        self.alarms = [a for a in self.alarms if a.get('id') != alarm_id]
        logger.info(f"Removed alarm: {alarm_id}")

    def update_config(self, new_config):
        """Update alarm configuration."""
        self.config.update(new_config)
        logger.info("Updated alarm configuration") 