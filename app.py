from flask import Flask, request, jsonify
from flask_cors import CORS
import stripe
import os

app = Flask(__name__)
CORS(app, origins=["https://tigerviolet.co.uk"])  # allow your website only

# Stripe secret key (replace with your own test/live key)
stripe.api_key = "STRIPE_SECRET_KEY"

# Pre-created shipping rate IDs from Stripe dashboard
STANDARD_SHIPPING_ID = "shr_standard"  # e.g., £4.99
FREE_SHIPPING_ID = "shr_free"          # £0 shipping

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.json or {}
    cart = data.get("cart", [])
    subtotal = float(data.get("subtotal", 0))

    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    # Build line items
    line_items = [
        {"price": item["stripePriceId"], "quantity": item["quantity"]}
        for item in cart
    ]

    # Decide which shipping rate to use
    shipping_rate_id = "shr_1TIsvV0HGQpKk5h8AFJw0TJJ" if subtotal >= 50 else "shr_1TIsvB0HGQpKk5h8AdLVDDFK"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            shipping_address_collection={"allowed_countries": ["GB"]},
            shipping_options=[{"shipping_rate": shipping_rate_id}],
            success_url="https://tigerviolet.co.uk/success",
            cancel_url="https://tigerviolet.co.uk/cancel",
        )
        return jsonify({"url": session.url})
    except Exception as e:
        print(f"Stripe error: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route("/success")
def success():
    return "<h1>Payment successful! Thank you for your purchase.</h1>"

@app.route("/cancel")
def cancel():
    return "<h1>Payment canceled. You can try again.</h1>"

@app.route("/ping")
def ping():
    return "ok", 200

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
