from flask import Flask, request, jsonify
import stripe

app = Flask(__name__)

# Stripe secret key (replace with your own test key)
stripe.api_key = "STRIPE_SECRET_KEY"

@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.json
    cart = data.get("cart", [])
    subtotal = float(data.get("subtotal", 0))  # Ensure it's a float

    print(f"DEBUG: Received subtotal: {subtotal}")  # Debug logging
    print(f"DEBUG: Cart: {cart}")  # Debug logging

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
    print(f"DEBUG: Shipping cost: {shipping_cost}")  # Debug logging

    if shipping_cost > 0:
        print("DEBUG: Adding shipping to line items")  # Debug logging
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

    print(f"DEBUG: Final line items: {line_items}")  # Debug logging

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
        print(f"DEBUG: Stripe error: {str(e)}")  # Debug logging
        return jsonify(error=str(e)), 500

@app.route("/success")
def success():
    return "<h1>Payment successful! Thank you for your purchase.</h1>"

@app.route("/cancel")
def cancel():
    return "<h1>Payment canceled. You can try again.</h1>"

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)

