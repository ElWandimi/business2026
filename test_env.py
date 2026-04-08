#!/usr/bin/env python3
"""
Test script to verify environment variables are loaded correctly.
Run with: python test_env.py
"""

import os
from dotenv import load_dotenv
from pathlib import Path

print("="*60)
print("Environment Variables Test")
print("="*60)

# Check if .env file exists
env_path = Path('.env')
if env_path.exists():
    print(f"✅ .env file found: {env_path.absolute()}")
    print(f"   File size: {env_path.stat().st_size} bytes")
    
    # Load the .env file
    load_dotenv()
    print("✅ .env file loaded successfully")
else:
    print(f"❌ .env file NOT found at: {env_path.absolute()}")
    print("   Please create a .env file in the project root directory")

print("\n" + "-"*60)
print("Checking Stripe Keys:")
print("-"*60)

# Check Stripe keys
stripe_public = os.environ.get('STRIPE_PUBLIC_KEY')
stripe_secret = os.environ.get('STRIPE_SECRET_KEY')
stripe_webhook = os.environ.get('STRIPE_WEBHOOK_SECRET')

if stripe_public:
    masked_public = stripe_public[:15] + "..." + stripe_public[-10:] if len(stripe_public) > 25 else "***masked***"
    print(f"✅ STRIPE_PUBLIC_KEY: {masked_public}")
else:
    print("❌ STRIPE_PUBLIC_KEY is not set")

if stripe_secret:
    masked_secret = stripe_secret[:15] + "..." + stripe_secret[-10:] if len(stripe_secret) > 25 else "***masked***"
    print(f"✅ STRIPE_SECRET_KEY: {masked_secret}")
else:
    print("❌ STRIPE_SECRET_KEY is not set")

if stripe_webhook:
    masked_webhook = stripe_webhook[:10] + "..." + stripe_webhook[-10:] if len(stripe_webhook) > 20 else "***masked***"
    print(f"✅ STRIPE_WEBHOOK_SECRET: {masked_webhook}")
else:
    print("⚠️ STRIPE_WEBHOOK_SECRET is not set (optional for development)")

print("\n" + "-"*60)
print("Other Environment Variables:")
print("-"*60)

# Check other important variables
variables_to_check = [
    'SECRET_KEY',
    'DATABASE_URL',
    'FLASK_APP',
    'FLASK_ENV',
    'MAIL_SERVER',
    'MAIL_USERNAME',
    'ADMIN_USERNAME'
]

for var in variables_to_check:
    value = os.environ.get(var)
    if value:
        if var in ['SECRET_KEY', 'MAIL_PASSWORD', 'ADMIN_PASSWORD']:
            # Mask sensitive values
            masked_value = value[:5] + "..." + value[-5:] if len(value) > 10 else "***masked***"
        elif len(value) > 10:
            masked_value = value[:10] + "..."
        else:
            masked_value = value
        print(f"✅ {var}: {masked_value}")
    else:
        print(f"⚠️ {var} is not set")

# Check if .env file has commented out lines
print("\n" + "-"*60)
print("Checking for commented out lines in .env:")
print("-"*60)

if env_path.exists():
    with open(env_path, 'r') as f:
        lines = f.readlines()
        commented_keys = []
        for line in lines:
            line = line.strip()
            if line.startswith('#') and 'STRIPE' in line:
                commented_keys.append(line)
        
        if commented_keys:
            print("⚠️ Found commented Stripe keys in .env:")
            for key in commented_keys:
                print(f"   {key}")
            print("\n   Remove the '#' at the beginning of these lines to enable them.")
        else:
            print("✅ No commented Stripe keys found")

print("="*60)