import os
from datetime import datetime, timedelta
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from werkzeug.security import generate_password_hash, check_password_hash
from urllib.parse import quote_plus
from config import DB_HOST, DB_NAME, DB_USER, DB_PASS

# Properly escape special characters in the password
DB_PASS_ESCAPED = quote_plus(DB_PASS)

# Database URL with escaped password
DATABASE_URL = f"mysql+pymysql://{DB_USER}:{DB_PASS_ESCAPED}@{DB_HOST}/{DB_NAME}"

try:
    # Create SQLAlchemy engine and session
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    print(f"Error creating database engine: {str(e)}")
    raise

# Create base class for declarative models
Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True)
    username = Column(String(50), unique=True, index=True)
    password_hash = Column(String(255))
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    google_id = Column(String(255), unique=True, nullable=True)
    profile_picture = Column(String(255), nullable=True)
    
    # Relationships
    verification_tokens = relationship("VerificationToken", back_populates="user")
    password_reset_tokens = relationship("PasswordResetToken", back_populates="user")
    alarms = relationship("Alarm", back_populates="user")
    settings = relationship("UserSettings", back_populates="user", uselist=False)
    devices = relationship("Device", back_populates="user")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class VerificationToken(Base):
    __tablename__ = "verification_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)

    # Relationship
    user = relationship("User", back_populates="verification_tokens")

    def is_valid(self):
        return not self.is_used and datetime.utcnow() <= self.expires_at

class PasswordResetToken(Base):
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    token = Column(String(255), unique=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    is_used = Column(Boolean, default=False)

    # Relationship
    user = relationship("User", back_populates="password_reset_tokens")

    def is_valid(self):
        return not self.is_used and datetime.utcnow() <= self.expires_at

class Alarm(Base):
    __tablename__ = "alarms"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String(100))
    time = Column(String(5))  # HH:MM format
    days = Column(String(50))  # Comma-separated days
    sound_file = Column(String(255))
    is_enabled = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    device_id = Column(Integer, ForeignKey("devices.id"))

    # Relationship
    user = relationship("User", back_populates="alarms")
    device = relationship("Device", back_populates="alarms")

class UserSettings(Base):
    __tablename__ = "user_settings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True)
    theme = Column(String(20), default='dark')
    time_format = Column(String(3), default='24h')
    date_format = Column(String(10), default='iso')
    temperature_unit = Column(String(1), default='C')
    default_sound = Column(String(255), default='standard_alarm.mp3')
    rgb_enabled = Column(Boolean, default=True)
    rgb_pattern = Column(String(20), default='default')
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship
    user = relationship("User", back_populates="settings")

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(String(64), unique=True, index=True)  # Unique identifier for each device
    user_id = Column(Integer, ForeignKey("users.id"))
    name = Column(String(100))  # User-friendly device name
    model = Column(String(50))  # Device model (e.g., "RPi3")
    status = Column(String(20))  # online/offline/error
    last_seen = Column(DateTime)
    firmware_version = Column(String(20))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship("User", back_populates="devices")
    alarms = relationship("Alarm", back_populates="device")

# Database dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Create all tables
def init_db():
    Base.metadata.create_all(bind=engine) 