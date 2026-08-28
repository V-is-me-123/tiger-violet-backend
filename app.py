from flask import Flask, request, jsonify
from flask_cors import CORS
from supabase import create_client
import stripe
import os
import time

app = Flask(__name__)
CORS(app, origins=["https://tigerviolet.co.uk"])  # allow your website only

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


def normalize_collection(value):
    normalized = str(value or "").strip().lower()
    return normalized if normalized in ALLOWED_COLLECTIONS else "stars"


def normalize_type(value):
    normalized = str(value or "").strip().lower()
    return normalized if normalized in ALLOWED_TYPES else "earrings"


def normalize_color(value):
    normalized = str(value or "").strip()
    if len(normalized) == 7 and normalized.startswith("#"):
        try:
            int(normalized[1:], 16)
            return normalized
        except ValueError:
            pass
    return "#000000"


def normalize_price(value):
    try:
        price = float(value)
    except (TypeError, ValueError):
        return None
    return price if price >= 0 else None


def normalize_product(data, existing_created_at=None):
    product_id = str(data.get("id") or "").strip()
    return {
        "id": product_id,
        "name": str(data.get("name") or "").strip(),
        "price": normalize_price(data.get("price")),
        "image": str(data.get("image") or "").strip(),
        "stripePriceId": str(data.get("stripePriceId") or "").strip(),
        "collection": normalize_collection(data.get("collection")),
        "type": normalize_type(data.get("type")),
        "color": normalize_color(data.get("color")),
        "parentId": str(data.get("parentId") or product_id).strip() or product_id,
        "createdAt": existing_created_at or int(time.time() * 1000),
        "description": str(data.get("description") or "").strip(),
    }


def validate_product(product, raw_collection, raw_type):
    if not product["id"]:
        return "Product ID is required."
    if not product["id"].replace("-", "").replace("_", "").isalnum():
        return "Product ID can only contain letters, numbers, hyphens, and underscores."
    if not product["name"]:
        return "Product name is required."
    if product["price"] is None:
        return "Price must be a valid number."
    if not product["image"]:
        return "Image is required."
    if not product["stripePriceId"]:
        return "Stripe Price ID is required."
    if str(raw_collection or "").strip().lower() not in ALLOWED_COLLECTIONS:
        return "Collection must be one of: stars, flowers, animals, fruits."
    if str(raw_type or "").strip().lower() not in ALLOWED_TYPES:
        return "Type must be earrings or keyrings."
    return None


def load_products():
    res = supabase.table("products").select("*").execute()
    return {p["id"]: p for p in res.data}

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
