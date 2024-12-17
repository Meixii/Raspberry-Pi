#!/usr/bin/env python3
import os
import sys
import time
import logging
import threading
import uuid
import json
import requests
from urllib3.exceptions import InsecureRequestWarning
from dotenv import load_dotenv

# Suppress only the single warning from urllib3 needed.
requests.packages.urllib3.disable_warnings(category=InsecureRequestWarning)

# Local module imports
from display import Display
from alarm import AlarmManager
from weather import WeatherManager
from hardware import HardwareController
from api import app as api_app

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('smart_alarm.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class SmartAlarm:
    def __init__(self):
        """Initialize the Smart Alarm system."""
        load_dotenv()  # Load environment variables
        
        # Check for device ID
        self.device_id = self._get_or_create_device_id()
        self.is_registered = self._check_device_registration()
        
        # Initialize display first for registration screen
        self.display = Display()
        
        if not self.is_registered:
            logger.info(f"Device not registered. Device ID: {self.device_id}")
            # Show registration screen
            self.display.show_registration_screen(self.device_id)
            return
        
        # Initialize other components only if device is registered
        self.alarm_manager = AlarmManager()
        self.weather_manager = WeatherManager(api_key=os.getenv('WEATHER_API_KEY'))
        self.hardware = HardwareController()
        
        self.running = False
        logger.info("Smart Alarm system initialized")

    def _get_or_create_device_id(self):
        """Get existing device ID or create a new one."""
        device_file = 'device_id.json'
        if os.path.exists(device_file):
            with open(device_file, 'r') as f:
                data = json.load(f)
                return data['device_id']
        
        # Generate new device ID (shorter version)
        device_id = str(uuid.uuid4())[:8]
        with open(device_file, 'w') as f:
            json.dump({'device_id': device_id}, f)
        return device_id

    def _check_device_registration(self):
        """Check if device is registered with the web service."""
        try:
            response = requests.get(
                f"{os.getenv('API_BASE_URL')}/api/devices/check/{self.device_id}",
                verify=False,  # Temporarily disable SSL verification
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Error checking device registration: {str(e)}")
            return False

    def start(self):
        """Start the Smart Alarm system."""
        if not self.is_registered:
            # Just keep showing registration screen and checking
            while not self._check_device_registration():
                time.sleep(5)
            # Once registered, reinitialize
            self.__init__()
        
        self.running = True
        logger.info("Starting Smart Alarm system")
        
        try:
            while self.running:
                # Update display with current time and date
                self.display.update_time()
                
                # Check and update weather information
                weather_data = self.weather_manager.get_current_weather()
                if weather_data:
                    self.display.update_weather(weather_data)
                
                # Check for active alarms
                if self.alarm_manager.check_alarms():
                    self.trigger_alarm()
                
                # Check for weather alerts
                alerts = self.weather_manager.get_alerts()
                if alerts:
                    self.display.show_alerts(alerts)
                
                # Update upcoming events
                events = self.alarm_manager.get_upcoming_events()
                if events:
                    self.display.update_events(events)
                
                # Small delay to prevent excessive CPU usage
                time.sleep(1)
                
        except KeyboardInterrupt:
            logger.info("Keyboard interrupt received")
            self.stop()
        except Exception as e:
            logger.error(f"Error in main loop: {str(e)}")
            self.stop()

    def stop(self):
        """Stop the Smart Alarm system."""
        self.running = False
        if hasattr(self, 'hardware'):
            self.hardware.cleanup()
        logger.info("Smart Alarm system stopped")

    def trigger_alarm(self):
        """Handle alarm triggering."""
        try:
            # Get alarm configuration
            config = self.alarm_manager.get_current_alarm_config()
            
            # Trigger RGB lights if enabled
            if config.get('rgb_enabled', True):
                self.hardware.start_light_sequence(config.get('rgb_pattern', 'default'))
            
            # Play alarm sound
            self.hardware.play_alarm_sound(config.get('sound_file', 'standard_alarm.mp3'))
            
            # Update display for alarm state
            self.display.show_alarm_active(config)
            
        except Exception as e:
            logger.error(f"Error triggering alarm: {str(e)}")

def run_api_server():
    """Run the Flask API server."""
    api_app.run(host='0.0.0.0', port=5000)

def run_alarm_system():
    """Run the main alarm system."""
    smart_alarm = SmartAlarm()
    smart_alarm.start()

if __name__ == "__main__":
    # Start API server in a separate thread
    api_thread = threading.Thread(target=run_api_server)
    api_thread.daemon = True  # Thread will be terminated when main program exits
    api_thread.start()
    logger.info("API server started")

    # Start main alarm system
    run_alarm_system() 