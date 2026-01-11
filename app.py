from flask import Flask, request, jsonify
from flask_cors import CORS
import stripe
import os

app = Flask(__name__)
CORS(app)  # Allow requests from frontend

# Stripe secret key from environment variable (safe)
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# Map product IDs to Stripe price IDs (replace with your test/live IDs)
PRICE_IDS = {
    "1": "prod_Tm0j3IZyhD8JuT",  # Purple Sparkle Stars
    "2": "price_def456",  # Decorative Lamp
    "3": "price_ghi789"   # Stylish Planter
}

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.get_json()
    product_id = data.get("product_id", "1")
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": PRICE_IDS.get(product_id, "price_abc123"),
                "quantity": 1
            }],
            mode="payment",
            success_url="https://tigerviolet.netlify.app/success.html",
            cancel_url="https://tigerviolet.netlify.app/cancel.html",
        )
        return jsonify({"url": checkout_session.url})
    except Exception as e:
        return jsonify(error=str(e)), 400

if __name__ == "__main__":
    app.run(port=5000, debug=True)
