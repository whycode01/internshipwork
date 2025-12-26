"""
Notification Service for Smart Shopping Assistant
Handles various types of notifications including email, desktop, and in-app alerts
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
import os
from typing import Dict, List, Optional
import json
import logging

logger = logging.getLogger(__name__)

class NotificationService:
    """Service for handling various types of notifications"""
    
    def __init__(self):
        self.email_config = {
            'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
            'smtp_port': int(os.getenv('SMTP_PORT', 587)),
            'sender_email': os.getenv('EMAIL_USER'),
            'sender_password': os.getenv('EMAIL_PASSWORD')
        }
        self.notifications_file = "data/notifications.json"
        self.ensure_data_directory()
    
    def ensure_data_directory(self):
        """Ensure data directory exists"""
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(self.notifications_file):
            with open(self.notifications_file, 'w') as f:
                json.dump([], f)
    
    def send_price_alert_email(self, product_name: str, current_price: float, 
                              target_price: float, product_url: str, 
                              recipient_email: str) -> bool:
        """Send price alert via email"""
        try:
            if not self.email_config['sender_email'] or not self.email_config['sender_password']:
                logger.warning("Email credentials not configured")
                return False
            
            # Create message
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = recipient_email
            msg['Subject'] = f"🎉 Price Alert: {product_name}"
            
            # Email body
            body = f"""
Great news! The price for your tracked product has dropped!

📦 Product: {product_name}
💰 Current Price: ₹{current_price:,.2f}
🎯 Your Target: ₹{target_price:,.2f}
💵 Savings: ₹{target_price - current_price:,.2f}

🔗 Buy now: {product_url}

Happy shopping!
Smart Shopping Assistant
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port'])
            server.starttls()
            server.login(self.email_config['sender_email'], self.email_config['sender_password'])
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Price alert email sent to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send product available alert: {e}")
            return False

    def send_test_email(self, recipient_email: str) -> bool:
        """Send a test email to verify email configuration"""
        try:
            if not self.email_config['sender_email'] or not self.email_config['sender_password']:
                logger.warning("Email credentials not configured")
                return False

            # Check if using placeholder password
            if self.email_config['sender_password'] == "your_16_character_app_password_here":
                logger.error("Please update EMAIL_PASSWORD in .env with your Gmail App Password")
                return False

            # Create test message
            msg = MIMEMultipart()
            msg['From'] = self.email_config['sender_email']
            msg['To'] = recipient_email
            msg['Subject'] = "🧪 Smart Shopping Assistant - Test Email"

            # Email body
            body = f"""
            <html>
            <body>
                <h2>🎉 Email Test Successful!</h2>
                <p>This is a test email from your Smart Shopping Assistant.</p>
                <p><strong>Sent at:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>If you received this email, your notification system is working correctly!</p>
                
                <h3>📧 Email Setup Instructions</h3>
                <p>If you're having trouble receiving emails, please:</p>
                <ol>
                    <li>Enable 2-Factor Authentication on your Gmail account</li>
                    <li>Generate an App Password in Google Account Settings</li>
                    <li>Update the EMAIL_PASSWORD in your .env file with the 16-character App Password</li>
                </ol>
                
                <hr>
                <p><small>Smart Shopping Assistant - Find the best deals across multiple websites</small></p>
            </body>
            </html>
            """
            
            msg.attach(MIMEText(body, 'html'))

            # Send email with better error handling
            with smtplib.SMTP(self.email_config['smtp_server'], self.email_config['smtp_port']) as server:
                server.starttls()
                server.login(self.email_config['sender_email'], self.email_config['sender_password'])
                text = msg.as_string()
                server.sendmail(self.email_config['sender_email'], recipient_email, text)

            logger.info(f"Test email sent successfully to {recipient_email}")
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"SMTP Authentication failed. Please check your Gmail App Password: {e}")
            return False
        except Exception as e:
            logger.error(f"Failed to send test email: {e}")
            return False
    
    def create_desktop_notification(self, title: str, message: str, 
                                   notification_type: str = "info") -> bool:
        """Create desktop notification"""
        try:
            # Try to use plyer for cross-platform notifications
            try:
                from plyer import notification
                notification.notify(
                    title=title,
                    message=message,
                    timeout=10
                )
                return True
            except ImportError:
                logger.warning("plyer not installed - desktop notifications disabled")
                return False
                
        except Exception as e:
            logger.error(f"Failed to create desktop notification: {e}")
            return False
    
    def save_in_app_notification(self, title: str, message: str, 
                                notification_type: str = "info", 
                                product_id: Optional[int] = None) -> bool:
        """Save notification for in-app display"""
        try:
            notification = {
                'id': int(datetime.now().timestamp() * 1000),
                'title': title,
                'message': message,
                'type': notification_type,
                'product_id': product_id,
                'timestamp': datetime.now().isoformat(),
                'read': False
            }
            
            # Load existing notifications
            with open(self.notifications_file, 'r') as f:
                notifications = json.load(f)
            
            # Add new notification
            notifications.append(notification)
            
            # Keep only last 100 notifications
            notifications = notifications[-100:]
            
            # Save back
            with open(self.notifications_file, 'w') as f:
                json.dump(notifications, f, indent=2)
            
            logger.info(f"In-app notification saved: {title}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save in-app notification: {e}")
            return False
    
    def get_unread_notifications(self) -> List[Dict]:
        """Get all unread notifications"""
        try:
            with open(self.notifications_file, 'r') as f:
                notifications = json.load(f)
            
            return [n for n in notifications if not n.get('read', False)]
            
        except Exception as e:
            logger.error(f"Failed to get notifications: {e}")
            return []
    
    def get_all_notifications(self, limit: int = 50) -> List[Dict]:
        """Get all notifications with limit"""
        try:
            with open(self.notifications_file, 'r') as f:
                notifications = json.load(f)
            
            # Sort by timestamp (newest first)
            notifications.sort(key=lambda x: x['timestamp'], reverse=True)
            return notifications[:limit]
            
        except Exception as e:
            logger.error(f"Failed to get all notifications: {e}")
            return []
    
    def mark_notification_as_read(self, notification_id: int) -> bool:
        """Mark notification as read"""
        try:
            with open(self.notifications_file, 'r') as f:
                notifications = json.load(f)
            
            for notification in notifications:
                if notification['id'] == notification_id:
                    notification['read'] = True
                    break
            
            with open(self.notifications_file, 'w') as f:
                json.dump(notifications, f, indent=2)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to mark notification as read: {e}")
            return False
    
    def send_price_drop_alert(self, product_name: str, old_price: float, 
                             new_price: float, product_url: str,
                             target_price: Optional[float] = None,
                             recipient_email: Optional[str] = None) -> Dict[str, bool]:
        """Send comprehensive price drop alert"""
        results = {
            'email': False,
            'desktop': False,
            'in_app': False
        }
        
        # Calculate savings
        savings = old_price - new_price
        savings_percent = (savings / old_price) * 100
        
        # Create notification content
        title = f"💰 Price Drop Alert: {product_name}"
        
        if target_price and new_price <= target_price:
            message = f"🎉 Target reached! Price dropped to ₹{new_price:,.2f} (was ₹{old_price:,.2f}). Save ₹{savings:,.2f} ({savings_percent:.1f}% off)!"
        else:
            message = f"📉 Price dropped to ₹{new_price:,.2f} (was ₹{old_price:,.2f}). Save ₹{savings:,.2f} ({savings_percent:.1f}% off)!"
        
        # Send email if configured and requested
        if recipient_email and target_price and new_price <= target_price:
            results['email'] = self.send_price_alert_email(
                product_name, new_price, target_price, product_url, recipient_email
            )
        
        # Send desktop notification
        results['desktop'] = self.create_desktop_notification(title, message)
        
        # Save in-app notification
        results['in_app'] = self.save_in_app_notification(
            title, message, 
            'success' if target_price and new_price <= target_price else 'info'
        )
        
        return results
    
    def send_product_available_alert(self, product_name: str, product_url: str,
                                   recipient_email: Optional[str] = None) -> Dict[str, bool]:
        """Send product availability alert"""
        results = {
            'email': False,
            'desktop': False,
            'in_app': False
        }
        
        title = f"🔔 Product Available: {product_name}"
        message = f"The product '{product_name}' is now available for purchase!"
        
        # Send desktop notification
        results['desktop'] = self.create_desktop_notification(title, message)
        
        # Save in-app notification
        results['in_app'] = self.save_in_app_notification(title, message, 'info')
        
        return results