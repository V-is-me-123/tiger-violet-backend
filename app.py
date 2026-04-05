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
    "1": "price_1SomPd0HGQpKk5h8Dxsdwxoq",  # Purple Sparkle Stars
    "2": "price_1N0defXyz987654",  # Decorative Lamp
    "3": "price_1N0ghiXyz111222"   # Stylish Planter
}

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.json
    cart = data.get("cart", [])

    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    line_items = []
    for item in cart:
        line_items.append({
            "price": item["stripePriceId"],
            "quantity": item["quantity"]
        })

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url="https://tigerviolet.co.uk/success",
            cancel_url="https://tigerviolet.co.uk/cancel",
        )
        return jsonify({"url": session.url})
    except Exception as e:
        return jsonify(error=str(e)), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Get port from Render
    app.run(host="0.0.0.0", port=port, debug=True)  # Bind to 0.0.0.0
