from flask import Flask, request, jsonify
import stripe

app = Flask(__name__)

# Stripe secret key (replace with your own test key)
stripe.api_key = "STRIPE_SECRET_KEY"

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
    cart = data.get("cart", [])
    subtotal = data.get("subtotal", 0)

    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    line_items = []
    for item in cart:
        line_items.append({
            "price": item["stripePriceId"],
            "quantity": item["quantity"]
        })

    # Add shipping if subtotal < 50
    shipping_cost = 0 if subtotal >= 50 else 499  # £4.99 in pence
    if shipping_cost > 0:
        line_items.append({
            "price_data": {
                "currency": "gbp",
                "product_data": {
                    "name": "Shipping",
                },
                "unit_amount": shipping_cost,
            },
            "quantity": 1,
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

@app.route("/success")
def success():
    return "<h1>Payment successful! Thank you for your purchase.</h1>"

@app.route("/cancel")
def cancel():
    return "<h1>Payment canceled. You can try again.</h1>"

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)

