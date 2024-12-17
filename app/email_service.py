import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from config import EMAIL_HOST, EMAIL_USER, EMAIL_PASS, WEBSITE_URL

logger = logging.getLogger(__name__)

class EmailService:
    def __init__(self):
        self.host = EMAIL_HOST
        self.user = EMAIL_USER
        self.password = EMAIL_PASS
        self.from_email = EMAIL_USER

    def send_email(self, to_email, subject, html_content):
        """Send an email with HTML content."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.from_email
            msg['To'] = to_email

            html_part = MIMEText(html_content, 'html')
            msg.attach(html_part)

            with smtplib.SMTP_SSL(self.host, 465) as server:
                server.login(self.user, self.password)
                server.send_message(msg)

            logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False

    def send_verification_email(self, to_email, token):
        """Send email verification link."""
        verification_link = f"{WEBSITE_URL}/verify-email?token={token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #007AFF;">Verify Your Email Address</h2>
                    <p>Thank you for registering with Smart Alarm! Please click the button below to verify your email address:</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{verification_link}" 
                           style="background-color: #007AFF; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Verify Email
                        </a>
                    </p>
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
                        {verification_link}
                    </p>
                    <p>This link will expire in 24 hours.</p>
                    <p>If you didn't create an account with Smart Alarm, please ignore this email.</p>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(
            to_email,
            "Verify Your Smart Alarm Email Address",
            html_content
        )

    def send_password_reset_email(self, to_email, token):
        """Send password reset link."""
        reset_link = f"{WEBSITE_URL}/reset-password?token={token}"
        
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #007AFF;">Reset Your Password</h2>
                    <p>We received a request to reset your Smart Alarm password. Click the button below to create a new password:</p>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{reset_link}" 
                           style="background-color: #007AFF; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Reset Password
                        </a>
                    </p>
                    <p>Or copy and paste this link in your browser:</p>
                    <p style="background-color: #f5f5f5; padding: 10px; border-radius: 5px;">
                        {reset_link}
                    </p>
                    <p>This link will expire in 1 hour.</p>
                    <p>If you didn't request a password reset, please ignore this email.</p>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(
            to_email,
            "Reset Your Smart Alarm Password",
            html_content
        )

    def send_welcome_email(self, to_email, username):
        """Send welcome email after verification."""
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #007AFF;">Welcome to Smart Alarm!</h2>
                    <p>Hi {username},</p>
                    <p>Thank you for verifying your email address. Your Smart Alarm account is now fully activated!</p>
                    <p>Here are some things you can do next:</p>
                    <ul>
                        <li>Set up your first alarm</li>
                        <li>Customize your display settings</li>
                        <li>Configure weather alerts</li>
                        <li>Choose your favorite alarm sounds</li>
                    </ul>
                    <p style="text-align: center; margin: 30px 0;">
                        <a href="{WEBSITE_URL}/dashboard" 
                           style="background-color: #007AFF; color: white; padding: 12px 24px; 
                                  text-decoration: none; border-radius: 5px; display: inline-block;">
                            Go to Dashboard
                        </a>
                    </p>
                    <p>If you have any questions or need assistance, please don't hesitate to contact our support team.</p>
                </div>
            </body>
        </html>
        """
        
        return self.send_email(
            to_email,
            "Welcome to Smart Alarm!",
            html_content
        ) 