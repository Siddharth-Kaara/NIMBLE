import os
import stripe
import requests
from flask import Flask, jsonify, request, send_from_directory, redirect
from dotenv import load_dotenv
import json
from flask_cors import CORS
import logging
import sys

# Load environment variables from .env file
load_dotenv()

# Configure logging with immediate flushing
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("nimble-server")

# Force stdout and stderr to flush immediately
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Flask app setup
app = Flask(__name__, static_folder="public")
app.logger.setLevel(logging.INFO)

# Configure CORS
CORS(app, resources={
    r"/*": {
        "origins": "*",
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization"]
    }
})

# Add explicit CORS configuration
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    return response

app.debug = True

# API keys and configuration
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
CRYPTLEX_TOKEN = os.getenv("CRYPTLEX_TOKEN")
WORKER_URL = os.getenv('CLOUDFLARE_WORKER_URL', 'https://stripe-webhook-test.siddharth-g.workers.dev/')
YOUR_DOMAIN = os.getenv('DOMAIN_URL', "http://localhost:4242")

# Logging helper
def log_info(message):
    logger.info(message)
    sys.stdout.flush()

def log_error(message):
    logger.error(message)
    sys.stdout.flush()

# Serve static files
@app.route("/")
def serve_index():
    log_info("Serving index.html")
    return send_from_directory("public", "index.html")

@app.route("/<path:filename>")
def serve_static(filename):
    return send_from_directory("public", filename)

# Get Stripe Publishable Key
@app.route("/get-stripe-key", methods=["GET"])
def get_stripe_key():
    log_info("Getting Stripe publishable key")
    return jsonify({"publicKey": STRIPE_PUBLISHABLE_KEY})

# Get product IDs
@app.route("/get-product-ids", methods=["GET"])
def get_product_ids():
    log_info("Fetching product IDs...")
    product_id = os.getenv("CRYPTLEX_PRODUCT_ID")
    versions = {
        "web": os.getenv("CRYPTLEX_VERSION_WEB_ID"),
        "mobile": os.getenv("CRYPTLEX_VERSION_MOBILE_ID"),
        "combo": os.getenv("CRYPTLEX_VERSION_COMBO_ID"),
        "cross": os.getenv("CRYPTLEX_VERSION_CROSS_ID")
    }
    log_info(f"Product ID: {product_id}")
    log_info(f"Versions: {versions}")
    return jsonify({
        "productId": product_id,
        "versions": versions
    })

# Check for active license
@app.route("/check-active-license", methods=["POST"])
def check_active_license():
    try:
        data = request.get_json()
        user_email = data.get("userEmail")
        log_info(f"\n=== Checking active license for email: {user_email} ===")
        
        if not user_email:
            log_error("User email is required")
            return jsonify({"error": "User email is required"}), 400

        query_params = {
            "user.email": user_email,
            "expired": False,
            "revoked": False,
            "suspended": False,
            "limit": 1
        }
        endpoint = "https://api.eu.cryptlex.com/v3/licenses?" + "&".join(f"{k}={v}" for k, v in query_params.items())
        response = requests.get(endpoint, headers={"Authorization": f"Bearer {CRYPTLEX_TOKEN}"})
        
        if response.status_code == 200:
            existing_license = response.json()
            if existing_license and len(existing_license) > 0:
                log_info(f"Found active license with key: {existing_license[0].get('key')}")
                return jsonify({
                    "hasActiveLicense": True,
                    "message": "This user already has an active license. Please contact support."
                })
            log_info("No active license found - allowing checkout")
            return jsonify({"hasActiveLicense": False})
        else:
            log_error(f"Error checking license: {response.text}")
            return jsonify({"error": "Failed to check license status"}), 500

    except Exception as e:
        log_error(f"Error in /check-active-license: {e}")
        return jsonify({"error": str(e)}), 500

# Get price ID for product version
def get_price_id(product_version_id):
    price_mapping = {
        os.getenv("CRYPTLEX_VERSION_WEB_ID"): os.getenv("STRIPE_PRICE_WEB_ID"),
        os.getenv("CRYPTLEX_VERSION_MOBILE_ID"): os.getenv("STRIPE_PRICE_MOBILE_ID"),
        os.getenv("CRYPTLEX_VERSION_COMBO_ID"): os.getenv("STRIPE_PRICE_COMBO_ID"),
        os.getenv("CRYPTLEX_VERSION_CROSS_ID"): os.getenv("STRIPE_PRICE_CROSS_ID")
    }
    price_id = price_mapping.get(product_version_id)
    if not price_id:
        raise ValueError(f"No matching Stripe price for version ID: {product_version_id}")
    return price_id

# Create Stripe Checkout Session
@app.route("/create-checkout-session", methods=["POST"])
async def create_checkout_session():
    try:
        data = request.get_json()
        log_info("\n=== Starting Checkout Session Creation ===")
        log_info(f"Received data: {json.dumps(data, indent=2)}")

        org_email = data["organizationEmail"]
        user_email = data["userEmail"]
        org_domain = org_email.split('@')[1].lower()
        user_domain = user_email.split('@')[1].lower()
        
        special_domains = ['gmail.com', 'outlook.com', 'hotmail.com', 'yahoo.com']
        if org_domain != user_domain and org_domain not in special_domains:
            error_msg = f"User email domain ({user_domain}) must match organization domain ({org_domain})"
            log_error(error_msg)
            return jsonify({"error": error_msg}), 400

        customers = stripe.Customer.list(email=org_email, limit=1)
        if customers.data:
            stripe_customer = customers.data[0]
            log_info(f"Found existing Stripe customer: {stripe_customer.id}")
        else:
            stripe_customer = stripe.Customer.create(
                email=org_email,
                name=org_domain.split('.')[0].upper(),
                metadata={"organization_domain": org_domain}
            )
            log_info(f"Created new Stripe customer: {stripe_customer.id}")

        price_id = get_price_id(data["productVersionId"])
        user_info = f"{data['firstName']} {data['lastName']} ({user_email})"
        log_info(f"User Info for metadata: {user_info}")

        checkout_metadata = {
            "productId": data["productId"],
            "productVersionId": data["productVersionId"],
            "userEmail": user_email,
            "organizationEmail": org_email,
            "firstName": data["firstName"],
            "lastName": data["lastName"]
        }

        subscription_metadata = {
            "User Info": user_info,
            "Product ID": data["productId"],
            "Organization Email": org_email
            # License ID added by worker.js via webhook
        }

        session = stripe.checkout.Session.create(
            customer=stripe_customer.id,
            payment_method_types=["card"],
            mode="subscription",
            success_url=request.host_url + "success.html",
            cancel_url=request.host_url + "cancel.html",
            line_items=[{"price": price_id, "quantity": 1}],
            metadata=checkout_metadata,
            subscription_data={
                "metadata": subscription_metadata,
                "description": f"Subscription for {user_info}"  

            }
        )
        
        log_info("=== Checkout Session Created Successfully ===\n")
        return jsonify({"id": session.id})
    except Exception as e:
        log_error(f"Error in create_checkout_session: {str(e)}")
        return jsonify({"error": str(e)}), 400


@app.route("/contact/submit", methods=["POST"])
def handle_contact_form_python():
    """
    Handle contact form submission with a more Python-like endpoint
    """
    from contact_form import process_contact_form
    return process_contact_form(request)


@app.route("/newsletter/subscribe", methods=["POST"])
def handle_newsletter_subscription():
    """
    Handle newsletter subscription
    """
    from newsletter import process_newsletter_subscription
    return process_newsletter_subscription(request)


if __name__ == "__main__":
    required_env_vars = [
        'STRIPE_SECRET_KEY',
        'STRIPE_PUBLISHABLE_KEY',
        'CRYPTLEX_TOKEN',
        'CLOUDFLARE_WORKER_URL',
        'STRIPE_PRICE_WEB_ID',
        'STRIPE_PRICE_MOBILE_ID',
        'STRIPE_PRICE_COMBO_ID',
        'STRIPE_PRICE_CROSS_ID'
    ]
    
    # Optional environment variables with defaults
    optional_env_vars = {
        'EMAIL_USERNAME': 'Email username for contact form',
        'EMAIL_PASSWORD': 'Email password for contact form',
        'EMAIL_FROM': 'Sender email for contact form'
    }
    
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    if missing_vars:
        log_error(f"Missing environment variables: {', '.join(missing_vars)}")
        sys.exit(1)
    
    # Log optional variables status
    for var, description in optional_env_vars.items():
        if not os.getenv(var):
            log_info(f"Optional variable {var} not set: {description}")
    
    # Get port from environment or default to 4242 for local dev
    port = int(os.getenv("PORT", 4242))
    log_info(f"Starting server on 0.0.0.0:{port}...")
    app.run(host="0.0.0.0", port=port, debug=True)