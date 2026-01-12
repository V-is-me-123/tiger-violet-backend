from flask import Flask, request, jsonify
from flask_cors import CORS
import stripe
import os

app = Flask(__name__)
CORS(app)  # Allow requests from frontend

# Stripe secret key from environment variable
stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# Map your product IDs to Stripe price IDs
PRICE_IDS = {
    "1": "price_1SoSho0HGQpKk5h8UH5Mk3WW",  # Purple Sparkle Stars
    "2": "price_1N0defXyz987654",  # Decorative Lamp
    "3": "price_1N0ghiXyz111222"   # Stylish Planter
}

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.get_json()
    product_id = data.get("product_id")
    if product_id not in PRICE_IDS:
        return jsonify({"error": "Invalid product"}), 400

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price": PRICE_IDS[product_id],
                "quantity": 1
            }],
            mode="payment",
            success_url="https://tigerviolet.netlify.app/success.html",
            cancel_url="https://tigerviolet.netlify.app/cancel.html",
        )
        return jsonify({"url": checkout_session.url})

    except Exception as e:
        print("STRIPE ERROR:", e) 
        return jsonify(error=str(e)), 400

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Get port from Render
    app.run(host="0.0.0.0", port=port, debug=True)  # Bind to 0.0.0.0
