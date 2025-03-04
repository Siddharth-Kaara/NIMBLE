#RUN THIS SCRIPT ONCE TO CREATE THE PRICES FOR THE PRODUCTS

import stripe
import os
from dotenv import load_dotenv

load_dotenv()
stripe.api_key = os.getenv('STRIPE_SECRET_KEY')

# Define your product versions and prices
versions = [
    {"version": "web", "cryptlex_id": os.getenv("CRYPTLEX_VERSION_WEB_ID"), "stripe_id": os.getenv("STRIPE_PRODUCT_WEB_ID"), "amount": 9900},
    {"version": "mobile", "cryptlex_id": os.getenv("CRYPTLEX_VERSION_MOBILE_ID"), "stripe_id": os.getenv("STRIPE_PRODUCT_MOBILE_ID"), "amount": 9900},
    {"version": "combo", "cryptlex_id": os.getenv("CRYPTLEX_VERSION_COMBO_ID"), "stripe_id": os.getenv("STRIPE_PRODUCT_COMBO_ID"), "amount": 14900},
    {"version": "cross", "cryptlex_id": os.getenv("CRYPTLEX_VERSION_CROSS_ID"), "stripe_id": os.getenv("STRIPE_PRODUCT_CROSS_ID"), "amount": 19900}
]

for v in versions:
    price = stripe.Price.create(
        unit_amount=v["amount"],
        currency="usd",
        recurring={"interval": "month"},
        product=v["stripe_id"]
    )
    print(f"Created Price for {v['version']}: {price.id}")