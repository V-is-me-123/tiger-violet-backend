from flask import Flask, request, jsonify
import stripe

app = Flask(__name__)

# Stripe secret key (replace with your own test key)
stripe.api_key = "STRIPE_SECRET_KEY"


@app.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    data = request.json or {}
    cart = data.get("cart", [])
    subtotal = float(data.get("subtotal", 0))

    if not cart:
        return jsonify({"error": "Cart is empty"}), 400

    line_items = []
    for item in cart:
        line_items.append({
            "price": item["stripePriceId"],
            "quantity": item["quantity"],
        })

    shipping_cost = 0 if subtotal >= 50 else 499

    try:
        session_kwargs = {
            "payment_method_types": ["card"],
            "line_items": line_items,
            "mode": "payment",
            "success_url": "https://tigerviolet.co.uk/success",
            "cancel_url": "https://tigerviolet.co.uk/cancel",
        }

        if shipping_cost > 0:
            shipping_rate = stripe.shipping_rate.create(
                display_name="Standard Shipping",
                type="fixed_amount",
                fixed_amount={
                    "amount": shipping_cost,
                    "currency": "gbp",
                },
                delivery_estimate={
                    "minimum": {"unit": "business_day", "value": 3},
                    "maximum": {"unit": "business_day", "value": 5},
                },
            )

            session_kwargs["shipping_address_collection"] = {
                "allowed_countries": ["GB"],
            }
            session_kwargs["shipping_options"] = [{
                "shipping_rate": shipping_rate.id,
            }]

        session = stripe.checkout.Session.create(**session_kwargs)
        return jsonify({"url": session.url})
    except Exception as e:
        print(f"Stripe error: {str(e)}")
        return jsonify(error=str(e)), 500


@app.route("/success")
def success():
    return "<h1>Payment successful! Thank you for your purchase.</h1>"


@app.route("/cancel")
def cancel():
    return "<h1>Payment canceled. You can try again.</h1>"


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000)
