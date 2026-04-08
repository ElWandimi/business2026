import stripe
from flask import current_app

def create_payment_intent(amount, metadata=None):
    """
    Creates a Stripe PaymentIntent.
    Returns dict with 'success' bool and either 'client_secret' or 'error'.
    """
    try:
        stripe.api_key = current_app.config['STRIPE_SECRET_KEY']
        intent = stripe.PaymentIntent.create(
            amount=amount,
            currency='usd',                # change to your currency
            metadata=metadata or {},
            automatic_payment_methods={'enabled': True},
        )
        return {
            'success': True,
            'client_secret': intent.client_secret
        }
    except stripe.error.StripeError as e:
        # Log the error for debugging
        current_app.logger.error(f"Stripe error: {str(e)}")
        return {
            'success': False,
            'error': str(e)
        }
    except Exception as e:
        current_app.logger.error(f"Unexpected error: {str(e)}")
        return {
            'success': False,
            'error': 'An unexpected error occurred.'
        }