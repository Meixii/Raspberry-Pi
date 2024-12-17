# Smart Alarm System - Raspberry Pi Application

This is the Raspberry Pi application component of the Smart Alarm System. It handles the display, alarms, weather information, and hardware control.

## Features

- Real-time clock display with configurable time and date formats
- Weather information display with alerts
- Google Calendar integration for events and alarms
- RGB LED light control with various patterns
- Customizable alarm sounds
- Touch-screen friendly interface
- Multiple theme support

## Hardware Requirements

1. Raspberry Pi 3 Model B V1.2
2. Raspberry Pi Display V1.1
3. 1x8 RGB Module WS2812B
4. 8 Ohms 0.5W Mylar Type Speakers (2pcs)
5. DS3231 w/ AT24C32 EEPROM Real-Time Clock Module

## Installation

1. Install required system packages:
```bash
sudo apt-get update
sudo apt-get install -y python3-pip python3-dev python3-pillow
sudo apt-get install -y libsdl2-mixer-2.0-0 libjpeg-dev zlib1g-dev
```

2. Install Python dependencies:
```bash
pip3 install -r requirements.txt
```

3. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Configure Google Calendar API:
- Place your `credentials.json` file in the app directory
- Run the application once to complete OAuth setup

## Configuration

The system can be configured through:
1. Environment variables
2. Web interface at https://smartalarm.zgkaizen.xyz
3. Configuration files in the app directory

### Available Sound Files

The following alarm sounds are available in the `sounds` directory:
- `bomb-timer.mp3` - Intense countdown-style alarm
- `classic.mp3` - Traditional alarm sound
- `digital.mp3` - Digital alarm tone
- `digital-2.mp3` - Alternative digital alarm tone
- `generic.mp3` - Standard alarm sound
- `lofi-alarm.mp3` - Gentle lo-fi style alarm
- `morning-dew.mp3` - Soft nature-based wake up sound
- `morning-joy.mp3` - Uplifting morning melody
- `oversimplified.mp3` - Minimalist alarm tone
- `star-dust.mp3` - Ambient space-themed sound
- `unnamed.mp3` - Additional alarm sound
- `very-loud.mp3` - High-intensity alarm
- `wind-up.mp3` - Gradual wake-up sound

## Usage

1. Start the application:
```bash
python3 main.py
```

2. Access the web interface at https://smartalarm.zgkaizen.xyz to:
- Configure alarms
- Set up Google Calendar integration
- Customize themes and display settings
- Configure weather preferences
- Manage sound and light settings

## File Structure

- `main.py` - Main application entry point
- `display.py` - Display interface management
- `alarm.py` - Alarm and calendar management
- `weather.py` - Weather data handling
- `hardware.py` - Hardware control (LED, sound)
- `config.py` - Configuration settings
- `credentials.json` - Google OAuth credentials
- `requirements.txt` - Python dependencies

## Troubleshooting

1. Display Issues:
   - Check display connection and power
   - Verify display configuration in `config.py`
   - Check system logs for errors

2. Sound Issues:
   - Verify speaker connections
   - Check volume settings
   - Ensure sound files exist in the sounds directory

3. LED Issues:
   - Check LED strip connections
   - Verify GPIO pin configuration
   - Check power supply

4. Calendar Integration:
   - Verify internet connection
   - Check Google API credentials
   - Ensure proper OAuth setup

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support, please visit:
- Website: https://smartalarm.zgkaizen.xyz
- Email: melix@smartalarm.zgkaizen.xyz 

## Development Notes

### Pre-Deployment Checklist

1. Remove Development Bypass Login:
   - Delete the bypass button HTML from `website/index.html`:
     ```html
     <div class="dev-bypass">
         <button id="bypass-login-btn" class="bypass-btn">
             <i class="material-icons">build</i>
             Development Bypass
         </button>
     </div>
     ```
   - Remove bypass button styles from `website/css/styles.css`:
     ```css
     /* Development Bypass Button */
     .dev-bypass {
         margin-top: 2rem;
         padding-top: 1rem;
         border-top: 1px solid var(--border);
     }
     .bypass-btn { ... }
     .bypass-btn:hover { ... }
     .bypass-btn i { ... }
     ```
   - Remove bypass login function and event listener from `website/js/auth.js`:
     ```javascript
     // Development bypass login
     function handleBypassLogin() { ... }
     
     // Remove from event listeners
     document.getElementById('bypass-login-btn').addEventListener('click', handleBypassLogin);
     ```

2. Ensure all API keys and credentials are properly secured
3. Update configuration files with production values
4. Remove any test or mock data

