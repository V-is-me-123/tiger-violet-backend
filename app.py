from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
import stripe
import os

import json   
import time   

app = Flask(__name__)
CORS(app, origins=["https://tigerviolet.co.uk"])  # allow your website only

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

PRODUCTS_FILE = "products.json"

def load_products():
    res = supabase.table("products").select("*").execute()
    return {p["id"]: p for p in res.data}

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
    shipping_rate_id = "shr_1TIsvB0HGQpKk5h8AdLVDDFK"

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

@app.route("/login", methods=["POST"])
def login():
    data = request.json
    password = data.get("password")
    if password == os.environ.get("ADMIN_SECRET"):
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 401

@app.route("/add-product", methods=["POST"])
def add_product():
    auth = request.headers.get("Authorization")

    if auth != os.environ.get("ADMIN_SECRET"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json

    # Add timestamp for "New" badge
    data["createdAt"] = int(time.time() * 1000)

    ALLOWED_FIELDS = [
    "id", "name", "price", "image",
    "stripePriceId", "type", "collection",
    "color", "parentId", "createdAt", "description"
    ]

    clean_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
    print("DATA BEING SENT:", data)
    supabase.table("products").upsert(clean_data).execute()
 
   

    return jsonify({"status": "ok"})

@app.route("/remove-product", methods=["POST"])
def remove_product():
    auth = request.headers.get("Authorization")

    if auth != os.environ.get("ADMIN_SECRET"):
        return jsonify({"error": "Unauthorized"}), 403

    product_id = request.json.get("id")

    supabase.table("products").delete().eq("id", product_id).execute()

    return jsonify({"success": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
