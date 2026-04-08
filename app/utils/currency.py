# app/utils/currency.py
from flask import session
from flask_login import current_user

EXCHANGE_RATES = {
    'USD': 1.0,
    'EUR': 0.92,
    'GBP': 0.79,
    'JPY': 148.50,
    'CAD': 1.36,
    'AUD': 1.52,
    'CNY': 7.19,
    'KES': 130.00,  # 1 USD = 130 KES (example rate)
}

CURRENCY_SYMBOLS = {
    'USD': '$',
    'EUR': '€',
    'GBP': '£',
    'JPY': '¥',
    'CAD': 'C$',
    'AUD': 'A$',
    'CNY': '¥',
    'KES': 'KSh',   # Kenyan Shilling symbol
}

def get_current_currency():
    """Return the currency code from session or user preference."""
    if current_user.is_authenticated and current_user.currency:
        return current_user.currency
    return session.get('currency', 'USD')

def convert_price(amount):
    """Convert amount from USD to current currency."""
    currency = get_current_currency()
    rate = EXCHANGE_RATES.get(currency, 1.0)
    return amount * rate

def format_currency(amount):
    """Format amount in current currency with symbol."""
    currency = get_current_currency()
    converted = convert_price(amount)
    symbol = CURRENCY_SYMBOLS.get(currency, '$')
    if currency == 'JPY':
        return f"{symbol}{int(converted):,}"
    return f"{symbol}{converted:,.2f}"