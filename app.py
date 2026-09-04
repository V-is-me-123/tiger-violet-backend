from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
import stripe
import os
import time

app = Flask(__name__)
CORS(app, origins=["https://tigerviolet.co.uk"])

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

ALLOWED_COLLECTIONS = {"stars", "flowers", "animals", "fruits"}
ALLOWED_TYPES = {"earrings", "keyrings"}
ALLOWED_FIELDS = [
    "id", "name", "price", "image",
    "stripePriceId", "type", "collection",
    "color", "parentId", "createdAt", "description"
]

def load_products():
    res = supabase.table("products").select("*").execute()
    return {p["id"]: p for p in res.data}

def validate_product(data):
    if not str(data.get("id", "")).strip():
        return "Product ID is required."
    if not str(data.get("name", "")).strip():
        return "Product name is required."
    try:
        price = float(data.get("price"))
        if price < 0:
            raise ValueError
    except (TypeError, ValueError):
        return "Price must be a valid, non-negative number."
    if not str(data.get("image", "")).strip():
        return "Image is required."
    if not str(data.get("stripePriceId", "")).strip():
        return "Stripe Price ID is required."
    if str(data.get("collection", "")).lower() not in ALLOWED_COLLECTIONS:
        return "Collection must be one of: " + ", ".join(sorted(ALLOWED_COLLECTIONS))
    if str(data.get("type", "")).lower() not in ALLOWED_TYPES:
        return "Type must be earrings or keyrings."
    return None


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.json or {}
    cart = data.get("cart", [])

    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    line_items = [
        {"price": item["stripePriceId"], "quantity": item["quantity"]}
        for item in cart
    ]
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
    data = request.json or {}
    password = data.get("password")
    if password == os.environ.get("ADMIN_SECRET"):
        return jsonify({"ok": True})
    return jsonify({"ok": False}), 401

@app.route("/add-product", methods=["POST"])
def add_product():
    auth = request.headers.get("Authorization")
    if auth != os.environ.get("ADMIN_SECRET"):
        return jsonify({"error": "Unauthorized"}), 403

    data = request.json or {}
    original_id = str(data.get("originalId") or "").strip()

    validation_error = validate_product(data)
    if validation_error:
        return jsonify({"error": validation_error}), 400

    data["createdAt"] = data.get("createdAt") or int(time.time() * 1000)
    clean_data = {k: v for k, v in data.items() if k in ALLOWED_FIELDS}
    clean_data["collection"] = str(clean_data["collection"]).lower()
    clean_data["type"] = str(clean_data["type"]).lower()

    # If the ID changed (a rename during edit), remove the old row so it
    # doesn't get left behind as an orphaned duplicate.
    if original_id and original_id != clean_data["id"]:
        supabase.table("products").delete().eq("id", original_id).execute()

    supabase.table("products").upsert(clean_data).execute()
    return jsonify({"status": "ok", "product": clean_data})

@app.route("/remove-product", methods=["POST"])
def remove_product():
    auth = request.headers.get("Authorization")
    if auth != os.environ.get("ADMIN_SECRET"):
        return jsonify({"error": "Unauthorized"}), 403

    product_id = (request.json or {}).get("id")
    supabase.table("products").delete().eq("id", product_id).execute()
    return jsonify({"success": True})

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
