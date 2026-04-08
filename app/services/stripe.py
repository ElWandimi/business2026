import stripe
from flask import current_app

def get_stripe_api_key():
    return current_app.config.get('STRIPE_SECRET_KEY')

def create_stripe_customer(user):
    stripe.api_key = get_stripe_api_key()
    customer = stripe.Customer.create(
        email=user.email,
        name=user.full_name,
        metadata={'user_id': user.id}
    )
    return customer

def add_payment_method(customer_id, payment_method_id):
    stripe.api_key = get_stripe_api_key()
    payment_method = stripe.PaymentMethod.retrieve(payment_method_id)
    payment_method.attach(customer=customer_id)
    return payment_method

def get_stripe_customer(customer_id):
    stripe.api_key = get_stripe_api_key()
    return stripe.Customer.retrieve(customer_id)