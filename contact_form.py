import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import re
from dotenv import load_dotenv
import urllib.parse

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("contact_form.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("contact_form")

# Now load environment variables from .env file
try:
    load_dotenv()
    logger.info("Loaded environment variables from .env file")
    
    # Log environment variable status (without showing actual values)
    email_username = os.getenv('EMAIL_USERNAME')
    email_password = os.getenv('EMAIL_PASSWORD')
    email_from = os.getenv('EMAIL_FROM')
    
    logger.info(f"EMAIL_USERNAME is {'set' if email_username else 'NOT SET'}")
    logger.info(f"EMAIL_PASSWORD is {'set' if email_password else 'NOT SET'}")
    logger.info(f"EMAIL_FROM is {'set' if email_from else 'NOT SET'}")
except Exception as e:
    logger.error(f"Error loading environment variables: {str(e)}")

# Email configuration
EMAIL_CONFIG = {
    'recipient_email': 'siddharth.g@kaaratech.com', #nimble.viom
    'smtp': {
        'host': 'smtp.gmail.com',
        'port': 587,
        'username': os.getenv('EMAIL_USERNAME'),
        'password': os.getenv('EMAIL_PASSWORD'),
        'encryption': 'tls',
        'from_email': os.getenv('EMAIL_FROM'),
        'from_name': 'NIMBLE Website'
    },
    'form': {
        'subject': 'New Contact Form Submission - NIMBLE',
        'thank_you_page': '/thankyou.html',
        'error_redirect': '/index.html#contact'
    },
    'validation': {
        'name_max_length': 100,
        'message_max_length': 2000,
        'phone_pattern': r'^[0-9+\-\(\) ]{6,20}$'
    }
}

def validate_form_data(name, email, phone, message):
    """
    Validate form data according to rules
    Returns (is_valid, error_message)
    """
    # Check if required fields are present
    if not all([name, email, phone, message]):
        return False, "All fields are required"
    
    # Validate name length
    if len(name) > EMAIL_CONFIG['validation']['name_max_length']:
        return False, f"Name must be less than {EMAIL_CONFIG['validation']['name_max_length']} characters"
    
    # Validate email format
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    if not re.match(email_pattern, email):
        return False, "Please enter a valid email address"
    
    # Validate phone format
    if not re.match(EMAIL_CONFIG['validation']['phone_pattern'], phone):
        return False, "Please enter a valid phone number (6-20 digits)"
    
    # Validate message length
    if len(message) > EMAIL_CONFIG['validation']['message_max_length']:
        return False, f"Message must be less than {EMAIL_CONFIG['validation']['message_max_length']} characters"
    
    return True, ""

def send_email(name, email, phone, message):
    """
    Send email using SMTP
    Returns (success, error_message)
    """
    # Log the attempt
    logger.info(f"Attempting to send email from form submission by {name} <{email}>")
    
    # Check if email credentials are set
    smtp_settings = EMAIL_CONFIG['smtp']
    if not smtp_settings['username'] or not smtp_settings['password']:
        error_msg = "Email credentials not configured. Please set EMAIL_USERNAME and EMAIL_PASSWORD environment variables."
        logger.error(error_msg)
        return False, error_msg
    
    # Check if from_email is set
    if not smtp_settings['from_email']:
        smtp_settings['from_email'] = smtp_settings['username']
        logger.warning(f"EMAIL_FROM not set, using username as sender: {smtp_settings['from_email']}")
    
    # Prepare email content
    subject = EMAIL_CONFIG['form']['subject']
    recipient = EMAIL_CONFIG['recipient_email']
    
    # Log SMTP configuration (without password)
    logger.info(f"SMTP Configuration: Host={smtp_settings['host']}, Port={smtp_settings['port']}, "
                f"Username={smtp_settings['username']}, From={smtp_settings['from_email']}")
    
    # Create HTML and plain text versions
    html_content = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            h2 {{ color: #4183C4; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
            .field {{ margin-bottom: 20px; }}
            .label {{ font-weight: bold; }}
            .value {{ margin-top: 5px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h2>New Contact Form Submission</h2>
            <div class="field">
                <div class="label">Name:</div>
                <div class="value">{name}</div>
            </div>
            <div class="field">
                <div class="label">Email:</div>
                <div class="value">{email}</div>
            </div>
            <div class="field">
                <div class="label">Phone:</div>
                <div class="value">{phone}</div>
            </div>
            <div class="field">
                <div class="label">Message:</div>
                <div class="value">{message}</div>
            </div>
        </div>
    </body>
    </html>
    """
    
    text_content = f"""
    New Contact Form Submission
    
    Name: {name}
    Email: {email}
    Phone: {phone}
    Message: {message}
    """
    
    # Create message
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = f"{EMAIL_CONFIG['smtp']['from_name']} <{EMAIL_CONFIG['smtp']['from_email']}>"
    msg['To'] = recipient
    msg['Reply-To'] = email
    
    # Attach parts
    part1 = MIMEText(text_content, 'plain')
    part2 = MIMEText(html_content, 'html')
    msg.attach(part1)
    msg.attach(part2)
    
    try:
        # Connect to SMTP server
        logger.info(f"Connecting to SMTP server {smtp_settings['host']}:{smtp_settings['port']}...")
        server = smtplib.SMTP(smtp_settings['host'], smtp_settings['port'])
        server.ehlo()
        
        # Use TLS if specified
        if smtp_settings['encryption'] == 'tls':
            logger.info("Starting TLS encryption...")
            server.starttls()
            server.ehlo()
        
        # Login to SMTP server
        logger.info(f"Logging in with username: {smtp_settings['username']}...")
        server.login(smtp_settings['username'], smtp_settings['password'])
        
        # Send email
        logger.info(f"Sending email from {smtp_settings['from_email']} to {recipient}...")
        server.sendmail(smtp_settings['from_email'], recipient, msg.as_string())
        server.quit()
        
        logger.info(f"Email sent successfully to {recipient}")
        return True, ""
    
    except smtplib.SMTPAuthenticationError as e:
        error_message = "Email authentication failed. "
        if "Application-specific password required" in str(e):
            error_message += "You need to use an App Password for your Gmail account. Go to your Google Account → Security → App Passwords to create one."
        else:
            error_message += f"Please check your email credentials. Error: {str(e)}"
        logger.error(error_message)
        return False, error_message
        
    except Exception as e:
        error_message = f"Failed to send email: {str(e)}"
        logger.error(error_message)
        # Log more details about the exception
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception details: {e}")
        return False, error_message

def test_email_configuration():
    """
    Test the email configuration
    Returns HTML with test results
    """
    results = []
    
    # Test 1: Configuration check
    results.append({
        'title': 'Configuration Check',
        'status': 'success',
        'message': f"Recipient email: {EMAIL_CONFIG['recipient_email']}"
    })
    
    # Test 2: SMTP Settings check
    smtp_settings = EMAIL_CONFIG['smtp']
    if smtp_settings['username'] == 'your-email@gmail.com' or not smtp_settings['password']:
        results.append({
            'title': 'SMTP Settings',
            'status': 'warning',
            'message': "SMTP settings not configured yet. Please set EMAIL_USERNAME and EMAIL_PASSWORD environment variables."
        })
    else:
        results.append({
            'title': 'SMTP Settings',
            'status': 'success',
            'message': f"SMTP server: {smtp_settings['host']}:{smtp_settings['port']}, Username: {smtp_settings['username']}"
        })
    
    # Test 3: Send test email
    if smtp_settings['username'] != 'your-email@gmail.com' and smtp_settings['password']:
        success, error = send_email(
            "Test User", 
            "test@example.com", 
            "123-456-7890", 
            "This is a test message from the NIMBLE website contact form."
        )
        
        if success:
            results.append({
                'title': 'Test Email',
                'status': 'success',
                'message': f"Test email sent successfully to {EMAIL_CONFIG['recipient_email']}"
            })
        else:
            results.append({
                'title': 'Test Email',
                'status': 'error',
                'message': f"Failed to send test email: {error}"
            })
    else:
        results.append({
            'title': 'Test Email',
            'status': 'info',
            'message': "Skipped test email sending because SMTP settings are not configured."
        })
    
    # Generate HTML
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Email Configuration Test</title>
        <style>
            body { font-family: Arial, sans-serif; line-height: 1.6; padding: 20px; max-width: 800px; margin: 0 auto; }
            h1 { color: #333; border-bottom: 1px solid #eee; padding-bottom: 10px; }
            h2 { margin-top: 30px; color: #444; }
            .success { color: green; }
            .error { color: red; }
            .warning { color: orange; }
            .info { color: blue; }
            .result { margin-bottom: 20px; padding: 15px; border-radius: 5px; background-color: #f9f9f9; }
            .summary { margin-top: 40px; background-color: #f5f5f5; padding: 20px; border-radius: 5px; }
            .back-button { display: inline-block; margin-top: 20px; padding: 10px 20px; background-color: #4183C4; color: white; text-decoration: none; border-radius: 5px; }
        </style>
    </head>
    <body>
        <h1>Email Configuration Test</h1>
    """
    
    for result in results:
        html += f"""
        <div class="result">
            <h2>{result['title']}</h2>
            <p class="{result['status']}">
                {'✓ ' if result['status'] == 'success' else '⚠ ' if result['status'] == 'warning' else '✗ ' if result['status'] == 'error' else 'ℹ '}
                {result['message']}
            </p>
        </div>
        """
    
    html += """
        <div class="summary">
            <h2>Summary</h2>
            <p>To ensure emails are sent correctly:</p>
            <ol>
                <li>Make sure the recipient email address is correct in the EMAIL_CONFIG</li>
                <li>Set the EMAIL_USERNAME and EMAIL_PASSWORD environment variables</li>
                <li>For Gmail users, you'll need to use an App Password (requires 2FA to be enabled)</li>
                <li>Test the contact form on your website to verify everything is working</li>
            </ol>
        </div>
        
        <a href="/" class="back-button">Back to Website</a>
    </body>
    </html>
    """
    
    return html

def process_contact_form(request):
    """
    Process contact form submission
    This function handles the form validation and email sending
    """
    from flask import redirect
    
    logger.info("Contact form submission received")
    
    try:
        # Get form data
        name = request.form.get('name', '')
        email = request.form.get('email', '')
        phone = request.form.get('phone', '')
        message = request.form.get('message', '')
        
        # Log form data (excluding message for brevity)
        logger.info(f"Form data received - Name: {name}, Email: {email}, Phone: {phone}")
        
        # Validate form data
        logger.info("Validating form data...")
        is_valid, error_message = validate_form_data(name, email, phone, message)
        
        if not is_valid:
            # Log validation error
            logger.warning(f"Form validation failed: {error_message}")
            
            # Redirect back to form with error - properly encode the error message
            encoded_error = urllib.parse.quote(error_message)
            error_url = f"{EMAIL_CONFIG['form']['error_redirect']}?error={encoded_error}"
            logger.info(f"Redirecting to: {error_url}")
            return redirect(error_url)
        
        # Send email
        logger.info("Form validation successful. Attempting to send email...")
        success, error = send_email(name, email, phone, message)
        
        if success:
            # Redirect to thank you page
            logger.info(f"Email sent successfully. Redirecting to: {EMAIL_CONFIG['form']['thank_you_page']}")
            return redirect(EMAIL_CONFIG['form']['thank_you_page'])
        else:
            # Redirect back to form with error - properly encode the error message
            logger.warning(f"Failed to send email: {error}")
            encoded_error = urllib.parse.quote(error)
            error_url = f"{EMAIL_CONFIG['form']['error_redirect']}?error={encoded_error}"
            logger.info(f"Redirecting to: {error_url}")
            return redirect(error_url)
            
    except Exception as e:
        logger.error(f"Unexpected error in contact form processing: {str(e)}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        encoded_error = urllib.parse.quote("An unexpected error occurred")
        return redirect(f"/index.html#contact?error={encoded_error}") 