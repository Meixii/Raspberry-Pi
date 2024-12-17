import sys
import json
import uuid
import requests
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QLabel, QPushButton, QStackedWidget)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont, QPixmap, QImage
import qrcode
from PIL import Image
import io

class SmartAlarmGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.device_id = self.load_or_generate_device_id()
        self.api_url = 'http://192.168.1.49:5000/api'
        self.init_ui()
        
    def load_or_generate_device_id(self):
        try:
            with open('device_id.json', 'r') as f:
                data = json.load(f)
                return data['device_id']
        except FileNotFoundError:
            # Generate new device ID
            device_id = str(uuid.uuid4())
            with open('device_id.json', 'w') as f:
                json.dump({'device_id': device_id}, f)
            return device_id

    def init_ui(self):
        self.setWindowTitle('Smart Alarm')
        self.setGeometry(0, 0, 800, 480)  # RPi 7" display resolution
        
        # Create main widget and layout
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        layout = QVBoxLayout(main_widget)
        
        # Create stacked widget for different screens
        self.stacked_widget = QStackedWidget()
        layout.addWidget(self.stacked_widget)
        
        # Create different screens
        self.setup_registration_screen()
        self.setup_clock_screen()
        self.setup_alarm_screen()
        
        # Start with registration check
        self.check_registration()

    def setup_registration_screen(self):
        registration_widget = QWidget()
        layout = QVBoxLayout(registration_widget)
        
        # Title
        title = QLabel('Device Registration')
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 24))
        layout.addWidget(title)
        
        # QR Code
        self.qr_label = QLabel()
        self.qr_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.qr_label)
        
        # Instructions
        instructions = QLabel('Scan this QR code with the Smart Alarm website\nto register your device')
        instructions.setAlignment(Qt.AlignCenter)
        instructions.setFont(QFont('Arial', 14))
        layout.addWidget(instructions)
        
        # Device ID display
        device_id_label = QLabel(f'Device ID: {self.device_id}')
        device_id_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(device_id_label)
        
        self.stacked_widget.addWidget(registration_widget)
        self.generate_qr_code()

    def setup_clock_screen(self):
        clock_widget = QWidget()
        layout = QVBoxLayout(clock_widget)
        
        # Time display
        self.time_label = QLabel()
        self.time_label.setAlignment(Qt.AlignCenter)
        self.time_label.setFont(QFont('Arial', 72))
        layout.addWidget(self.time_label)
        
        # Date display
        self.date_label = QLabel()
        self.date_label.setAlignment(Qt.AlignCenter)
        self.date_label.setFont(QFont('Arial', 24))
        layout.addWidget(self.date_label)
        
        # Weather display
        self.weather_label = QLabel()
        self.weather_label.setAlignment(Qt.AlignCenter)
        self.weather_label.setFont(QFont('Arial', 18))
        layout.addWidget(self.weather_label)
        
        self.stacked_widget.addWidget(clock_widget)
        
        # Update time every second
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_clock)
        self.timer.start(1000)

    def setup_alarm_screen(self):
        alarm_widget = QWidget()
        layout = QVBoxLayout(alarm_widget)
        
        # Alarm title
        title = QLabel('⏰ Alarm!')
        title.setAlignment(Qt.AlignCenter)
        title.setFont(QFont('Arial', 36))
        layout.addWidget(title)
        
        # Snooze button
        snooze_btn = QPushButton('Snooze (5 min)')
        snooze_btn.setFont(QFont('Arial', 18))
        snooze_btn.clicked.connect(self.handle_snooze)
        layout.addWidget(snooze_btn)
        
        # Stop button
        stop_btn = QPushButton('Stop Alarm')
        stop_btn.setFont(QFont('Arial', 18))
        stop_btn.clicked.connect(self.handle_stop_alarm)
        layout.addWidget(stop_btn)
        
        self.stacked_widget.addWidget(alarm_widget)

    def generate_qr_code(self):
        # Generate QR code with device ID
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(self.device_id)
        qr.make(fit=True)
        qr_image = qr.make_image(fill_color="black", back_color="white")
        
        # Convert PIL image to QPixmap
        buffer = io.BytesIO()
        qr_image.save(buffer, format='PNG')
        buffer.seek(0)
        image_data = buffer.read()
        
        qimage = QImage.fromData(image_data)
        qpixmap = QPixmap.fromImage(qimage)
        self.qr_label.setPixmap(qpixmap.scaled(300, 300, Qt.KeepAspectRatio))

    def check_registration(self):
        try:
            response = requests.get(f'{self.api_url}/device/{self.device_id}/status')
            if response.ok and response.json().get('registered'):
                self.stacked_widget.setCurrentIndex(1)  # Show clock screen
            else:
                self.stacked_widget.setCurrentIndex(0)  # Show registration screen
        except requests.RequestException:
            # If can't reach server, default to registration screen
            self.stacked_widget.setCurrentIndex(0)

    def update_clock(self):
        from datetime import datetime
        now = datetime.now()
        self.time_label.setText(now.strftime('%H:%M:%S'))
        self.date_label.setText(now.strftime('%A, %B %d, %Y'))
        
        # Update weather every 15 minutes
        if now.minute % 15 == 0 and now.second == 0:
            self.update_weather()

    def update_weather(self):
        try:
            response = requests.get(f'{self.api_url}/device/{self.device_id}/weather')
            if response.ok:
                weather_data = response.json()
                self.weather_label.setText(
                    f"{weather_data['temperature']}°C | {weather_data['condition']}"
                )
        except requests.RequestException:
            self.weather_label.setText("Weather Unavailable")

    def handle_snooze(self):
        try:
            requests.post(f'{self.api_url}/device/{self.device_id}/alarm/snooze')
            self.stacked_widget.setCurrentIndex(1)  # Return to clock screen
        except requests.RequestException:
            pass  # Handle offline snooze locally

    def handle_stop_alarm(self):
        try:
            requests.post(f'{self.api_url}/device/{self.device_id}/alarm/stop')
            self.stacked_widget.setCurrentIndex(1)  # Return to clock screen
        except requests.RequestException:
            pass  # Handle offline stop locally

def main():
    app = QApplication(sys.argv)
    gui = SmartAlarmGUI()
    gui.showFullScreen()  # Show fullscreen on RPi touch display
    sys.exit(app.exec_())

if __name__ == '__main__':
    main() 