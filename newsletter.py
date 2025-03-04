import os
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("newsletter.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("newsletter")

# Load environment variables
load_dotenv()

# Email configuration
EMAIL_CONFIG = {
    'smtp': {
        'host': 'smtp.gmail.com',
        'port': 587,
        'username': os.getenv('EMAIL_USERNAME', 'your-email@gmail.com'),
        'password': os.getenv('EMAIL_PASSWORD', 'your-app-password'),
        'from_email': os.getenv('EMAIL_FROM', 'your-email@gmail.com')
    },
    'newsletter': {
        'thank_you_page': '/index.html',
        'error_redirect': '/index.html',
        'admin_email': os.getenv('ADMIN_EMAIL', os.getenv('EMAIL_FROM', 'your-email@gmail.com'))
    }
}

def validate_email(email):
    """
    Validate email format
    """
    email_regex = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(email_regex, email) is not None

def send_confirmation_email(email):
    """
    Send a confirmation email to the subscriber
    """
    from_email = EMAIL_CONFIG['smtp']['from_email']
    username = EMAIL_CONFIG['smtp']['username']
    password = EMAIL_CONFIG['smtp']['password']
    
    if not username or not password or not from_email:
        logger.warning("Email credentials not configured. Skipping confirmation email.")
        return False, "Email sending is not configured"
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = email
    msg['Subject'] = "Thank you for subscribing to NIMBLE Newsletter"
    
    # Email content
    html = f"""
    <html>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333C4E;">Thank You for Subscribing!</h2>
            <p>Hello,</p>
            <p>Thank you for subscribing to the NIMBLE Automation newsletter. We're excited to keep you updated with the latest news, features, and tips about our testing framework.</p>
            <p>You'll receive our newsletter periodically with valuable content to help you get the most out of NIMBLE.</p>
            <p>If you have any questions, feel free to contact us at <a href="mailto:nimble@viom.tech">nimble@viom.tech</a>.</p>
            <p>Best regards,<br>The NIMBLE Team</p>
        </div>
    </body>
    </html>
    """
    
    text = f"""
    Thank You for Subscribing!
    
    Hello,
    
    Thank you for subscribing to the NIMBLE Automation newsletter. We're excited to keep you updated with the latest news, features, and tips about our testing framework.
    
    You'll receive our newsletter periodically with valuable content to help you get the most out of NIMBLE.
    
    If you have any questions, feel free to contact us at nimble@viom.tech.
    
    Best regards,
    The NIMBLE Team
    """
    
    # Attach parts
    part1 = MIMEText(text, 'plain')
    part2 = MIMEText(html, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    try:
        # Connect to server
        server = smtplib.SMTP(EMAIL_CONFIG['smtp']['host'], EMAIL_CONFIG['smtp']['port'])
        server.starttls()
        
        # Login
        server.login(username, password)
        
        # Send email
        server.sendmail(from_email, email, msg.as_string())
        server.quit()
        
        logger.info(f"Confirmation email sent to {email}")
        return True, "Confirmation email sent"
    except Exception as e:
        logger.error(f"Failed to send confirmation email: {str(e)}")
        return False, str(e)

def send_admin_notification(email):
    """
    Send a notification to the admin about a new subscriber
    """
    from_email = EMAIL_CONFIG['smtp']['from_email']
    username = EMAIL_CONFIG['smtp']['username']
    password = EMAIL_CONFIG['smtp']['password']
    admin_email = EMAIL_CONFIG['newsletter']['admin_email']
    
    if not username or not password or not from_email:
        logger.warning("Email credentials not configured. Skipping admin notification.")
        return False, "Email sending is not configured"
    
    # Create message
    msg = MIMEMultipart()
    msg['From'] = from_email
    msg['To'] = admin_email
    msg['Subject'] = "New Newsletter Subscriber"
    
    # Email content
    text = f"""
    New Newsletter Subscriber
    
    A new user has subscribed to the NIMBLE newsletter:
    
    Email: {email}
    
    This is an automated notification.
    """
    
    msg.attach(MIMEText(text, 'plain'))
    
    try:
        # Connect to server
        server = smtplib.SMTP(EMAIL_CONFIG['smtp']['host'], EMAIL_CONFIG['smtp']['port'])
        server.starttls()
        
        # Login
        server.login(username, password)
        
        # Send email
        server.sendmail(from_email, admin_email, msg.as_string())
        server.quit()
        
        logger.info(f"Admin notification sent about new subscriber: {email}")
        return True, "Admin notification sent"
    except Exception as e:
        logger.error(f"Failed to send admin notification: {str(e)}")
        return False, str(e)

def save_subscriber(email):
    """
    Save subscriber email to a file
    """
    try:
        with open("subscribers.txt", "a", encoding="utf-8") as file:
            file.write(f"{email}\n")
        logger.info(f"Subscriber saved: {email}")
        return True
    except Exception as e:
        logger.error(f"Failed to save subscriber: {str(e)}")
        return False

def process_newsletter_subscription(request):
    """
    Process newsletter subscription form
    """
    from flask import redirect
    import urllib.parse
    
    logger.info("Newsletter subscription received")
    
    try:
        # Get form data
        email = request.form.get('email', '')
        
        # Validate email
        if not email or not validate_email(email):
            error_message = "Please provide a valid email address"
            logger.warning(f"Invalid email: {email}")
            encoded_error = urllib.parse.quote(error_message)
            return redirect(f"{EMAIL_CONFIG['newsletter']['error_redirect']}?newsletter_error={encoded_error}")
        
        # Save subscriber
        if not save_subscriber(email):
            error_message = "Failed to save your subscription"
            encoded_error = urllib.parse.quote(error_message)
            return redirect(f"{EMAIL_CONFIG['newsletter']['error_redirect']}?newsletter_error={encoded_error}")
        
        # Send confirmation email (non-blocking)
        send_confirmation_email(email)
        
        # Send admin notification (non-blocking)
        send_admin_notification(email)
        
        # Redirect to thank you page
        return redirect(f"{EMAIL_CONFIG['newsletter']['thank_you_page']}?newsletter_success=true")
            
    except Exception as e:
        logger.error(f"Unexpected error in newsletter processing: {str(e)}")
        encoded_error = urllib.parse.quote("An unexpected error occurred")
        return redirect(f"{EMAIL_CONFIG['newsletter']['error_redirect']}?newsletter_error={encoded_error}") 