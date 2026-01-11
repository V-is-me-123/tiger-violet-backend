from flask import Flask, request, jsonify
import stripe
from flask_cors import CORS
import os


app = Flask(__name__)

stripe.api_key = os.environ.get("STRIPE_SECRET_KEY")

# All products with IDs, names, and prices (in pence)
PRODUCTS = {
    "1": {"name": "Elegant Vase", "price": 2499, "currency": "gbp"},
    "2": {"name": "Decorative Lamp", "price": 1800, "currency": "gbp"},
    "3": {"name": "Stylish Planter", "price": 1250, "currency": "gbp"},
    "4": {"name": "Modern Candle Holder", "price": 1500, "currency": "gbp"},
    "5": {"name": "Glass Bowl", "price": 2000, "currency": "gbp"},
    "6": {"name": "Decorative Tray", "price": 2250, "currency": "gbp"}
}

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.json
    product_id = data.get("product_id")

    if product_id not in PRODUCTS:
        return jsonify({"error": "Invalid product ID"}), 400

    product = PRODUCTS[product_id]

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": product["currency"],
                    "product_data": {"name": product["name"]},
                    "unit_amount": product["price"],
                },
                "quantity": 1,
            }],
            mode="payment",
            success_url="http://localhost:5000/success",
            cancel_url="http://localhost:5000/cancel",
        )
        return jsonify({"url": session.url})
    except Exception as e:
        return jsonify(error=str(e)), 500

@app.route("/success")
def success():
    return "<h1>Payment successful! Thank you for your purchase.</h1>"

@app.route("/cancel")
def cancel():
    return "<h1>Payment canceled. You can try again.</h1>"

if __name__ == "__main__":
    app.run(port=5000, debug=True)
