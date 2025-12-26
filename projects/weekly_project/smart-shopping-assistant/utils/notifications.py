import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List
import requests
import logging

logger = logging.getLogger(__name__)

class NotificationManager:
    """Handle email and WhatsApp notifications"""
    
    def __init__(self):
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.email_user = os.getenv("EMAIL_USER")
        self.email_password = os.getenv("EMAIL_PASSWORD")
        self.whatsapp_api_key = os.getenv("WHATSAPP_API_KEY")
    
    def send_email_alert(self, to_email: str, subject: str, body: str) -> bool:
        """Send email alert"""
        try:
            msg = MIMEMultipart()
            msg['From'] = self.email_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            msg.attach(MIMEText(body, 'html'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Email sent to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Email send failed: {e}")
            return False
    
    def send_price_drop_alert(self, product_name: str, old_price: float, new_price: float, 
                             product_url: str, to_email: str) -> bool:
        """Send price drop alert email"""
        savings = old_price - new_price
        savings_percent = (savings / old_price) * 100
        
        subject = f"🎉 Price Drop Alert: {product_name}"
        
        body = f"""
        <html>
        <body>
            <h2>🎉 Great News! Price Drop Detected</h2>
            <h3>{product_name}</h3>
            
            <div style="background-color: #f0f8ff; padding: 20px; border-radius: 10px; margin: 20px 0;">
                <p><strong>💰 Old Price:</strong> <span style="text-decoration: line-through;">₹{old_price:,.0f}</span></p>
                <p><strong>💸 New Price:</strong> <span style="color: green; font-size: 1.2em;">₹{new_price:,.0f}</span></p>
                <p><strong>🎯 You Save:</strong> <span style="color: red; font-weight: bold;">₹{savings:,.0f} ({savings_percent:.1f}%)</span></p>
            </div>
            
            <p><a href="{product_url}" style="background-color: #4CAF50; color: white; padding: 15px 25px; text-decoration: none; border-radius: 5px;">🛒 Buy Now</a></p>
            
            <p><small>This alert was sent by Smart Shopping Assistant</small></p>
        </body>
        </html>
        """
        
        return self.send_email_alert(to_email, subject, body)
    
    def send_whatsapp_message(self, phone: str, message: str) -> bool:
        """Send WhatsApp message using API"""
        try:
            # Example using Twilio WhatsApp API
            url = "https://api.twilio.com/2010-04-01/Accounts/YOUR_ACCOUNT_SID/Messages.json"
            
            data = {
                'From': 'whatsapp:+14155238886',  # Twilio sandbox number
                'To': f'whatsapp:+{phone}',
                'Body': message
            }
            
            auth = ('YOUR_ACCOUNT_SID', 'YOUR_AUTH_TOKEN')
            
            response = requests.post(url, data=data, auth=auth)
            
            if response.status_code == 201:
                logger.info(f"WhatsApp message sent to {phone}")
                return True
            else:
                logger.error(f"WhatsApp send failed: {response.text}")
                return False
                
        except Exception as e:
            logger.error(f"WhatsApp send error: {e}")
            return False
    
    def send_test_email(self) -> bool:
        """Send test email"""
        subject = "🧪 Smart Shopping Assistant - Test Email"
        body = """
        <html>
        <body>
            <h2>🧪 Test Email</h2>
            <p>This is a test email from Smart Shopping Assistant.</p>
            <p>If you receive this, your email notifications are working correctly! ✅</p>
            
            <div style="background-color: #e8f5e8; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <p><strong>✅ Email system is operational</strong></p>
                <p>📧 SMTP Configuration: Working</p>
                <p>🔔 Notifications: Enabled</p>
            </div>
            
            <p><small>Sent at: {datetime.now()}</small></p>
        </body>
        </html>
        """
        
        from datetime import datetime
        formatted_body = body.format(datetime=datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        
        return self.send_email_alert(self.email_user, subject, formatted_body)
