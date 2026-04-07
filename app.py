from flask import Flask, request, jsonify
from flask_cors import CORS
import stripe
import os

import json   
import time   

app = Flask(__name__)
CORS(app, origins=["https://tigerviolet.co.uk"])  # allow your website only

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

PRODUCTS_FILE = "products.json"

def load_products():
    try:
        with open(PRODUCTS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_products(products):
    with open(PRODUCTS_FILE, "w") as f:
        json.dump(products, f, indent=2)

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
    shipping_rate_id = "shr_1TIsvV0HGQpKk5h8AFJw0TJJ"

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

@app.route("/products", methods=["GET"])
def get_products():
    return jsonify(load_products())

@app.route("/add-product", methods=["POST"])
def add_product():
    auth = request.headers.get("Authorization")

    if auth != os.environ.get("ADMIN_SECRET"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json
    products = load_products()

    product_id = data.get("id")

    products[product_id] = {
        **data,
        "createdAt": int(time.time() * 1000)
    }

    save_products(products)

    return jsonify({"success": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
