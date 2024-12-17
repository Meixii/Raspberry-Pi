import os
import time
import logging
import qrcode
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont

logger = logging.getLogger(__name__)

class Display:
    def __init__(self):
        """Initialize the display interface."""
        self.width = 800  # Display width
        self.height = 480  # Display height
        self.current_page = 'main'
        self.theme = self._load_theme()
        
        # Initialize display buffer
        self.image = Image.new('RGB', (self.width, self.height), self.theme['background'])
        self.draw = ImageDraw.Draw(self.image)
        
        # Load fonts
        self.fonts = self._load_fonts()
        
        logger.info("Display interface initialized")

    def _load_theme(self):
        """Load theme configuration."""
        # Default theme (can be overridden by web configuration)
        return {
            'background': '#000000',
            'text_primary': '#FFFFFF',
            'text_secondary': '#CCCCCC',
            'accent': '#007AFF',
            'warning': '#FF3B30'
        }

    def _load_fonts(self):
        """Load required fonts."""
        try:
            return {
                'large': ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf', 72),
                'medium': ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 36),
                'small': ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf', 24)
            }
        except Exception as e:
            logger.error(f"Error loading fonts: {str(e)}")
            # Fallback to default font
            return {
                'large': ImageFont.load_default(),
                'medium': ImageFont.load_default(),
                'small': ImageFont.load_default()
            }

    def clear(self):
        """Clear the display."""
        self.draw.rectangle([0, 0, self.width, self.height], fill=self.theme['background'])

    def update_time(self):
        """Update the time display."""
        now = datetime.now()
        time_str = now.strftime("%H:%M")
        date_str = now.strftime("%B %d, %Y")
        
        # Clear the time area
        self.draw.rectangle([10, 10, 400, 150], fill=self.theme['background'])
        
        # Draw time
        self.draw.text((20, 20), time_str, font=self.fonts['large'], fill=self.theme['text_primary'])
        self.draw.text((20, 100), date_str, font=self.fonts['medium'], fill=self.theme['text_secondary'])
        
        self._update_display()

    def update_weather(self, weather_data):
        """Update weather information display."""
        if not weather_data:
            return
            
        # Clear weather area
        self.draw.rectangle([410, 10, 790, 150], fill=self.theme['background'])
        
        # Draw weather information
        temp = f"{weather_data['temp_c']}°C"
        condition = weather_data['condition']['text']
        humidity = f"Humidity: {weather_data['humidity']}%"
        
        self.draw.text((420, 20), temp, font=self.fonts['large'], fill=self.theme['text_primary'])
        self.draw.text((420, 100), condition, font=self.fonts['small'], fill=self.theme['text_secondary'])
        self.draw.text((620, 100), humidity, font=self.fonts['small'], fill=self.theme['text_secondary'])
        
        self._update_display()

    def show_alerts(self, alerts):
        """Display weather alerts."""
        if not alerts:
            return
            
        # Clear alerts area
        self.draw.rectangle([10, 160, 790, 280], fill=self.theme['background'])
        
        # Display most recent/important alert
        alert = alerts[0]
        headline = alert['headline']
        severity = alert['severity']
        
        # Draw alert box
        self.draw.rectangle([10, 160, 790, 280], outline=self.theme['warning'])
        self.draw.text((20, 170), "WEATHER ALERT", font=self.fonts['medium'], fill=self.theme['warning'])
        self.draw.text((20, 220), headline[:80] + "..." if len(headline) > 80 else headline,
                      font=self.fonts['small'], fill=self.theme['text_primary'])
        
        self._update_display()

    def update_events(self, events):
        """Update upcoming events display."""
        if not events:
            return
            
        # Clear events area
        self.draw.rectangle([10, 290, 790, 470], fill=self.theme['background'])
        
        # Draw events header
        self.draw.text((20, 300), "Upcoming Events", font=self.fonts['medium'], fill=self.theme['accent'])
        
        # Display up to 3 upcoming events
        y_pos = 350
        for event in events[:3]:
            event_text = f"{event['title']} - {event['time']}"
            self.draw.text((20, y_pos), event_text, font=self.fonts['small'], fill=self.theme['text_secondary'])
            y_pos += 40
            
        self._update_display()

    def show_alarm_active(self, config):
        """Display active alarm screen."""
        self.clear()
        
        # Draw large alarm notification
        self.draw.text((self.width//2 - 100, self.height//2 - 50),
                      "ALARM",
                      font=self.fonts['large'],
                      fill=self.theme['warning'])
        
        # Draw alarm details
        if 'title' in config:
            self.draw.text((self.width//2 - 150, self.height//2 + 50),
                          config['title'],
                          font=self.fonts['medium'],
                          fill=self.theme['text_primary'])
            
        self._update_display()

    def show_registration_screen(self, device_id):
        """Display device registration screen with QR code."""
        self.clear()
        
        # Draw registration info
        title_text = "Device Registration"
        title_bbox = self.draw.textbbox((0, 0), title_text, font=self.fonts['large'])
        title_width = title_bbox[2] - title_bbox[0]
        self.draw.text((self.width//2 - title_width//2, 50),
                      title_text,
                      font=self.fonts['large'],
                      fill=self.theme['warning'])
        
        # Generate QR code
        registration_url = f"{os.getenv('WEBSITE_URL')}/devices/register/{device_id}"
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(registration_url)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Resize QR code to fit display nicely (200x200 pixels)
        qr_image = qr_image.resize((200, 200))
        
        # Convert QR code to RGB mode if it's not already
        if qr_image.mode != 'RGB':
            qr_image = qr_image.convert('RGB')
        
        # Paste QR code onto display buffer
        self.image.paste(qr_image, (self.width//2 - 100, self.height//2 - 100))
        
        # Draw instructions
        instructions = [
            "1. Scan this QR code with your phone",
            "2. Login or create an account",
            "3. Follow the registration process",
            "Device ID: " + device_id[:8]  # Show only first 8 characters
        ]
        
        y_pos = self.height//2 + 120
        for instruction in instructions:
            text_bbox = self.draw.textbbox((0, 0), instruction, font=self.fonts['small'])
            text_width = text_bbox[2] - text_bbox[0]
            self.draw.text((self.width//2 - text_width//2, y_pos),
                          instruction,
                          font=self.fonts['small'],
                          fill=self.theme['text_secondary'])
            y_pos += 30
        
        self._update_display()

    def _update_display(self):
        """Update the physical display with current buffer."""
        try:
            # Here you would implement the actual display update
            # This depends on your specific display hardware
            # For example, using framebuffer:
            # self.image.save('/dev/fb0', 'PNG')
            pass
        except Exception as e:
            logger.error(f"Error updating display: {str(e)}")

    def set_theme(self, theme_config):
        """Update the display theme."""
        self.theme.update(theme_config)
        self.clear()
        self._update_display() 