import os
import jwt
import json
import logging
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import uuid
from email_validator import validate_email, EmailNotValidError
from sqlalchemy.exc import IntegrityError

# Local imports
from config import *
from database import get_db, User, VerificationToken, PasswordResetToken, UserSettings, Device, Alarm
from email_service import EmailService
from alarm import AlarmManager
from weather import WeatherManager
from hardware import HardwareController

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Initialize components
alarm_manager = AlarmManager()
weather_manager = WeatherManager(api_key=WEATHER_API_KEY)
hardware_controller = HardwareController()

# JWT Secret Key
JWT_SECRET = os.getenv('JWT_SECRET', 'your-secret-key-here')
JWT_EXPIRATION = timedelta(days=7)

# Initialize email service
email_service = EmailService()

def token_required(f):
    """Decorator to check valid JWT token."""
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        
        # Get token from header
        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            try:
                token = auth_header.split(" ")[1]
            except IndexError:
                return jsonify({'success': False, 'message': 'Invalid token format'}), 401

        if not token:
            return jsonify({'success': False, 'message': 'Token is missing'}), 401

        try:
            # Verify token
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            current_user = data
        except jwt.ExpiredSignatureError:
            return jsonify({'success': False, 'message': 'Token has expired'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'success': False, 'message': 'Invalid token'}), 401

        return f(current_user, *args, **kwargs)

    return decorated

# Authentication endpoints
@app.route('/api/auth/verify', methods=['POST'])
def verify_google_token():
    """Verify Google OAuth token and return JWT token."""
    try:
        token = request.json.get('credential')
        if not token:
            return jsonify({'success': False, 'message': 'No token provided'}), 400

        # Verify Google token
        idinfo = id_token.verify_oauth2_token(
            token, google_requests.Request(), GOOGLE_CLIENT_ID)

        # Create JWT token
        jwt_token = jwt.encode({
            'id': idinfo['sub'],
            'name': idinfo['name'],
            'email': idinfo['email'],
            'picture': idinfo['picture'],
            'exp': datetime.utcnow() + JWT_EXPIRATION
        }, JWT_SECRET, algorithm="HS256")

        return jsonify({
            'success': True,
            'token': jwt_token,
            'user': {
                'id': idinfo['sub'],
                'name': idinfo['name'],
                'email': idinfo['email'],
                'picture': idinfo['picture']
            }
        })

    except ValueError as e:
        logger.error(f"Token verification failed: {str(e)}")
        return jsonify({'success': False, 'message': 'Invalid token'}), 401

@app.route('/api/auth/register', methods=['POST'])
def register():
    """Register a new user with email."""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')
        username = data.get('username')

        if not all([email, password, username]):
            return jsonify({
                'success': False,
                'message': 'Email, password, and username are required'
            }), 400

        # Validate email
        try:
            valid = validate_email(email)
            email = valid.email
        except EmailNotValidError as e:
            return jsonify({
                'success': False,
                'message': str(e)
            }), 400

        # Validate password
        if len(password) < 8:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters long'
            }), 400

        db = next(get_db())
        
        # Check if user exists
        existing_user = db.query(User).filter(
            (User.email == email) | (User.username == username)
        ).first()
        
        if existing_user:
            return jsonify({
                'success': False,
                'message': 'Email or username already exists'
            }), 400

        # Create user
        user = User(
            email=email,
            username=username,
            is_active=False,
            is_verified=False
        )
        user.set_password(password)
        
        # Create verification token
        token = str(uuid.uuid4())
        verification = VerificationToken(
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=24)
        )
        user.verification_tokens.append(verification)
        
        # Create default settings
        settings = UserSettings()
        user.settings = settings

        db.add(user)
        db.commit()

        # Send verification email
        if email_service.send_verification_email(email, token):
            return jsonify({
                'success': True,
                'message': 'Registration successful. Please check your email to verify your account.'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Registration successful but failed to send verification email.'
            }), 500

    except Exception as e:
        logger.error(f"Registration error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Registration failed'
        }), 500

@app.route('/api/auth/verify-email', methods=['POST'])
def verify_email():
    """Verify email with token."""
    try:
        token = request.json.get('token')
        if not token:
            return jsonify({
                'success': False,
                'message': 'Verification token is required'
            }), 400

        db = next(get_db())
        verification = db.query(VerificationToken).filter_by(
            token=token,
            is_used=False
        ).first()

        if not verification or not verification.is_valid():
            return jsonify({
                'success': False,
                'message': 'Invalid or expired verification token'
            }), 400

        # Update user and token
        user = verification.user
        user.is_verified = True
        user.is_active = True
        verification.is_used = True
        db.commit()

        # Send welcome email
        email_service.send_welcome_email(user.email, user.username)

        return jsonify({
            'success': True,
            'message': 'Email verified successfully'
        })

    except Exception as e:
        logger.error(f"Email verification error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Email verification failed'
        }), 500

@app.route('/api/auth/login', methods=['POST'])
def login():
    """Login with email and password."""
    try:
        data = request.json
        email = data.get('email')
        password = data.get('password')

        if not all([email, password]):
            return jsonify({
                'success': False,
                'message': 'Email and password are required'
            }), 400

        db = next(get_db())
        user = db.query(User).filter_by(email=email).first()

        if not user or not user.check_password(password):
            return jsonify({
                'success': False,
                'message': 'Invalid email or password'
            }), 401

        if not user.is_verified:
            return jsonify({
                'success': False,
                'message': 'Please verify your email before logging in'
            }), 401

        # Update last login
        user.last_login = datetime.utcnow()
        db.commit()

        # Create JWT token
        jwt_token = jwt.encode({
            'id': user.id,
            'email': user.email,
            'username': user.username,
            'exp': datetime.utcnow() + JWT_EXPIRATION
        }, JWT_SECRET, algorithm="HS256")

        return jsonify({
            'success': True,
            'token': jwt_token,
            'user': {
                'id': user.id,
                'email': user.email,
                'username': user.username,
                'profile_picture': user.profile_picture
            }
        })

    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Login failed'
        }), 500

@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """Send password reset email."""
    try:
        email = request.json.get('email')
        if not email:
            return jsonify({
                'success': False,
                'message': 'Email is required'
            }), 400

        db = next(get_db())
        user = db.query(User).filter_by(email=email).first()

        if not user:
            return jsonify({
                'success': True,
                'message': 'If an account exists with this email, you will receive a password reset link'
            })

        # Create reset token
        token = str(uuid.uuid4())
        reset_token = PasswordResetToken(
            token=token,
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )
        user.password_reset_tokens.append(reset_token)
        db.commit()

        # Send reset email
        if email_service.send_password_reset_email(email, token):
            return jsonify({
                'success': True,
                'message': 'Password reset instructions have been sent to your email'
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Failed to send password reset email'
            }), 500

    except Exception as e:
        logger.error(f"Password reset request error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Failed to process password reset request'
        }), 500

@app.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """Reset password with token."""
    try:
        data = request.json
        token = data.get('token')
        new_password = data.get('password')

        if not all([token, new_password]):
            return jsonify({
                'success': False,
                'message': 'Token and new password are required'
            }), 400

        if len(new_password) < 8:
            return jsonify({
                'success': False,
                'message': 'Password must be at least 8 characters long'
            }), 400

        db = next(get_db())
        reset_token = db.query(PasswordResetToken).filter_by(
            token=token,
            is_used=False
        ).first()

        if not reset_token or not reset_token.is_valid():
            return jsonify({
                'success': False,
                'message': 'Invalid or expired reset token'
            }), 400

        # Update password and token
        user = reset_token.user
        user.set_password(new_password)
        reset_token.is_used = True
        db.commit()

        return jsonify({
            'success': True,
            'message': 'Password reset successful'
        })

    except Exception as e:
        logger.error(f"Password reset error: {str(e)}")
        return jsonify({
            'success': False,
            'message': 'Password reset failed'
        }), 500

# Alarm endpoints
@app.route('/api/alarms', methods=['GET'])
@token_required
def get_alarms(current_user):
    """Get all alarms for the user."""
    return jsonify({
        'success': True,
        'alarms': alarm_manager.alarms
    })

@app.route('/api/alarms', methods=['POST'])
@token_required
def create_alarm(current_user):
    """Create a new alarm."""
    try:
        alarm_data = request.json
        alarm_data['id'] = str(len(alarm_manager.alarms) + 1)  # Simple ID generation
        alarm_manager.add_alarm(alarm_data)
        return jsonify({
            'success': True,
            'alarm': alarm_data
        })
    except Exception as e:
        logger.error(f"Error creating alarm: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/alarms/<alarm_id>', methods=['PUT'])
@token_required
def update_alarm(current_user, alarm_id):
    """Update an existing alarm."""
    try:
        alarm_data = request.json
        alarm_data['id'] = alarm_id
        alarm_manager.update_alarm(alarm_data)
        return jsonify({
            'success': True,
            'alarm': alarm_data
        })
    except Exception as e:
        logger.error(f"Error updating alarm: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/alarms/<alarm_id>', methods=['DELETE'])
@token_required
def delete_alarm(current_user, alarm_id):
    """Delete an alarm."""
    try:
        alarm_manager.remove_alarm(alarm_id)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error deleting alarm: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/alarms/<alarm_id>/toggle', methods=['POST'])
@token_required
def toggle_alarm(current_user, alarm_id):
    """Toggle alarm enabled state."""
    try:
        enabled = request.json.get('enabled', False)
        alarm = next((a for a in alarm_manager.alarms if a.get('id') == alarm_id), None)
        if alarm:
            alarm['enabled'] = enabled
            return jsonify({'success': True})
        return jsonify({'success': False, 'message': 'Alarm not found'}), 404
    except Exception as e:
        logger.error(f"Error toggling alarm: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

# Weather endpoints
@app.route('/api/weather/current', methods=['GET'])
@token_required
def get_current_weather(current_user):
    """Get current weather data."""
    try:
        weather_data = weather_manager.get_current_weather()
        return jsonify({
            'success': True,
            'weather': weather_data
        })
    except Exception as e:
        logger.error(f"Error getting weather: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/weather/forecast', methods=['GET'])
@token_required
def get_weather_forecast(current_user):
    """Get weather forecast."""
    try:
        days = request.args.get('days', 3, type=int)
        forecast = weather_manager.get_forecast(days)
        return jsonify({
            'success': True,
            'forecast': forecast
        })
    except Exception as e:
        logger.error(f"Error getting forecast: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/weather/alerts', methods=['GET'])
@token_required
def get_weather_alerts(current_user):
    """Get weather alerts."""
    try:
        alerts = weather_manager.get_alerts()
        return jsonify({
            'success': True,
            'alerts': alerts
        })
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

# Sound endpoints
@app.route('/api/sounds', methods=['GET'])
@token_required
def get_sounds(current_user):
    """Get list of available alarm sounds."""
    try:
        sounds_dir = PATHS['SOUNDS_DIR']
        sounds = []
        for filename in os.listdir(sounds_dir):
            if filename.endswith('.mp3'):
                sound_id = os.path.splitext(filename)[0]
                sounds.append({
                    'id': sound_id,
                    'name': sound_id.replace('-', ' ').title(),
                    'file': filename,
                    'isDefault': filename == alarm_manager.config.get('default_sound')
                })
        return jsonify({
            'success': True,
            'sounds': sounds
        })
    except Exception as e:
        logger.error(f"Error getting sounds: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/sounds/upload', methods=['POST'])
@token_required
def upload_sound(current_user):
    """Upload a new alarm sound."""
    try:
        if 'sound' not in request.files:
            return jsonify({'success': False, 'message': 'No sound file provided'}), 400

        sound_file = request.files['sound']
        if sound_file.filename == '':
            return jsonify({'success': False, 'message': 'No file selected'}), 400

        if not sound_file.filename.endswith('.mp3'):
            return jsonify({'success': False, 'message': 'Only MP3 files are allowed'}), 400

        filename = os.path.join(PATHS['SOUNDS_DIR'], sound_file.filename)
        sound_file.save(filename)

        return jsonify({
            'success': True,
            'sound': {
                'id': os.path.splitext(sound_file.filename)[0],
                'name': os.path.splitext(sound_file.filename)[0].replace('-', ' ').title(),
                'file': sound_file.filename,
                'isDefault': False
            }
        })
    except Exception as e:
        logger.error(f"Error uploading sound: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/sounds/<sound_id>/default', methods=['POST'])
@token_required
def set_default_sound(current_user, sound_id):
    """Set default alarm sound."""
    try:
        sounds_dir = PATHS['SOUNDS_DIR']
        sound_file = f"{sound_id}.mp3"
        if not os.path.exists(os.path.join(sounds_dir, sound_file)):
            return jsonify({'success': False, 'message': 'Sound not found'}), 404

        alarm_manager.update_config({'default_sound': sound_file})
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error setting default sound: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

# Settings endpoints
@app.route('/api/settings', methods=['GET'])
@token_required
def get_settings(current_user):
    """Get user settings."""
    return jsonify({
        'success': True,
        'settings': alarm_manager.config
    })

@app.route('/api/settings', methods=['POST'])
@token_required
def update_settings(current_user):
    """Update user settings."""
    try:
        new_settings = request.json
        alarm_manager.update_config(new_settings)
        return jsonify({'success': True})
    except Exception as e:
        logger.error(f"Error updating settings: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

@app.route('/api/settings/reset', methods=['POST'])
@token_required
def reset_settings(current_user):
    """Reset settings to defaults."""
    try:
        alarm_manager.config = alarm_manager._load_config()
        return jsonify({
            'success': True,
            'settings': alarm_manager.config
        })
    except Exception as e:
        logger.error(f"Error resetting settings: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 400

# Device management endpoints
@app.route('/api/devices', methods=['GET'])
@token_required
def get_devices(current_user):
    """Get all devices for the user."""
    try:
        db = next(get_db())
        devices = db.query(Device).filter_by(user_id=current_user['id']).all()
        return jsonify({
            'success': True,
            'devices': [{
                'id': device.id,
                'device_id': device.device_id,
                'name': device.name,
                'model': device.model,
                'status': device.status,
                'last_seen': device.last_seen.isoformat() if device.last_seen else None,
                'firmware_version': device.firmware_version
            } for device in devices]
        })
    except Exception as e:
        logger.error(f"Error getting devices: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/devices/register', methods=['POST'])
@token_required
def register_device(current_user):
    """Register a new device."""
    try:
        data = request.json
        device_id = data.get('device_id')
        name = data.get('name', f"Smart Alarm {device_id[-6:]}")
        model = data.get('model', 'RPi3')

        if not device_id:
            return jsonify({
                'success': False,
                'message': 'Device ID is required'
            }), 400

        db = next(get_db())
        
        # Check if device already exists
        existing_device = db.query(Device).filter_by(device_id=device_id).first()
        if existing_device:
            return jsonify({
                'success': False,
                'message': 'Device already registered'
            }), 400

        # Create new device
        device = Device(
            device_id=device_id,
            user_id=current_user['id'],
            name=name,
            model=model,
            status='offline',
            firmware_version='1.0.0'
        )
        
        db.add(device)
        db.commit()

        return jsonify({
            'success': True,
            'device': {
                'id': device.id,
                'device_id': device.device_id,
                'name': device.name,
                'model': device.model,
                'status': device.status
            }
        })

    except Exception as e:
        logger.error(f"Error registering device: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/devices/<device_id>', methods=['PUT'])
@token_required
def update_device(current_user, device_id):
    """Update device information."""
    try:
        data = request.json
        db = next(get_db())
        
        device = db.query(Device).filter_by(
            device_id=device_id,
            user_id=current_user['id']
        ).first()
        
        if not device:
            return jsonify({
                'success': False,
                'message': 'Device not found'
            }), 404

        # Update allowed fields
        if 'name' in data:
            device.name = data['name']
        if 'status' in data:
            device.status = data['status']
        if 'firmware_version' in data:
            device.firmware_version = data['firmware_version']
        
        device.last_seen = datetime.utcnow()
        db.commit()

        return jsonify({
            'success': True,
            'device': {
                'id': device.id,
                'device_id': device.device_id,
                'name': device.name,
                'model': device.model,
                'status': device.status,
                'last_seen': device.last_seen.isoformat(),
                'firmware_version': device.firmware_version
            }
        })

    except Exception as e:
        logger.error(f"Error updating device: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/devices/<device_id>/sync', methods=['POST'])
@token_required
def sync_device(current_user, device_id):
    """Sync device settings and alarms."""
    try:
        db = next(get_db())
        device = db.query(Device).filter_by(
            device_id=device_id,
            user_id=current_user['id']
        ).first()
        
        if not device:
            return jsonify({
                'success': False,
                'message': 'Device not found'
            }), 404

        # Get user settings and alarms
        settings = db.query(UserSettings).filter_by(user_id=current_user['id']).first()
        alarms = db.query(Alarm).filter_by(device_id=device.id).all()

        return jsonify({
            'success': True,
            'settings': {
                'theme': settings.theme,
                'time_format': settings.time_format,
                'date_format': settings.date_format,
                'temperature_unit': settings.temperature_unit,
                'default_sound': settings.default_sound,
                'rgb_enabled': settings.rgb_enabled,
                'rgb_pattern': settings.rgb_pattern
            },
            'alarms': [{
                'id': alarm.id,
                'title': alarm.title,
                'time': alarm.time,
                'days': alarm.days,
                'sound_file': alarm.sound_file,
                'is_enabled': alarm.is_enabled
            } for alarm in alarms]
        })

    except Exception as e:
        logger.error(f"Error syncing device: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

# Update alarm endpoints to include device_id
@app.route('/api/devices/<device_id>/alarms', methods=['GET'])
@token_required
def get_device_alarms(current_user, device_id):
    """Get all alarms for a specific device."""
    try:
        db = next(get_db())
        device = db.query(Device).filter_by(
            device_id=device_id,
            user_id=current_user['id']
        ).first()
        
        if not device:
            return jsonify({
                'success': False,
                'message': 'Device not found'
            }), 404

        alarms = db.query(Alarm).filter_by(device_id=device.id).all()
        return jsonify({
            'success': True,
            'alarms': [{
                'id': alarm.id,
                'title': alarm.title,
                'time': alarm.time,
                'days': alarm.days,
                'sound_file': alarm.sound_file,
                'is_enabled': alarm.is_enabled
            } for alarm in alarms]
        })

    except Exception as e:
        logger.error(f"Error getting device alarms: {str(e)}")
        return jsonify({'success': False, 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 