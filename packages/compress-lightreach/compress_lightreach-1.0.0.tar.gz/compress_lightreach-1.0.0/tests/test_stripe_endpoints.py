#!/usr/bin/env python3
"""
Test script for Stripe subscription endpoints.

⚠️  IMPORTANT: Make sure you're using TEST keys, not LIVE keys!
   - Test keys should be configured in .env file (lines 10-15)
   - Test keys start with sk_test_... (not sk_live_...)

Usage:
    python -m pytest tests/test_stripe_endpoints.py::test_checkout -v
    python tests/test_stripe_endpoints.py [endpoint]

Endpoints:
    checkout    - Test creating a checkout session
    webhook     - Test webhook endpoint (requires Stripe CLI)
    subscription - Test getting subscription details
    all         - Run all tests
"""

import sys
import json
import os
import requests
from typing import Optional
from pathlib import Path

# Add backend directory to path so we can import api.config
backend_dir = Path(__file__).resolve().parent.parent
backend_dir_str = str(backend_dir)
if backend_dir_str not in sys.path:
    sys.path.insert(0, backend_dir_str)

# Import api.config - handle import errors gracefully for pytest collection
try:
    from api.config import settings
except ImportError:
    # If import fails during pytest collection, create a mock settings object
    # This allows pytest to collect the file even if api.config isn't available
    class MockSettings:
        STRIPE_SECRET_KEY = ""
        STRIPE_PUBLISHABLE_KEY = ""
        STRIPE_WEBHOOK_SECRET = ""
        STRIPE_PRICE_ID_PRO = ""
    settings = MockSettings()

# Check if using test keys - only when running as script, not during pytest collection
# Pytest sets __file__ but we can detect pytest by checking if pytest is in sys.modules
_is_pytest = "pytest" in sys.modules or "_pytest" in sys.modules

if not _is_pytest:
    stripe_key = settings.STRIPE_SECRET_KEY or ""
    if stripe_key.startswith("sk_live_"):
        print("⚠️  WARNING: You're using LIVE Stripe keys!")
        print("   For testing, use TEST keys (sk_test_...)")
        print("   Update .env file with test keys from lines 10-15")
        # Check if running interactively
        if sys.stdin.isatty():
            response = input("\nContinue anyway? (yes/no): ")
            if response.lower() != "yes":
                print("Exiting. Switch to test keys and try again.")
                sys.exit(1)
        else:
            print("\n⚠️  Non-interactive mode detected. Exiting to prevent using live keys.")
            print("   Please uncomment test keys in .env file (lines 10-15) and comment out live keys.")
            sys.exit(1)
    elif not stripe_key.startswith("sk_test_") and stripe_key:
        print(f"⚠️  WARNING: Stripe key format unexpected: {stripe_key[:10]}...")
        print("   Expected test key format: sk_test_...")
    elif not stripe_key:
        print("⚠️  WARNING: STRIPE_SECRET_KEY not set in .env file")
        print("   Please configure test keys in .env file (lines 10-15)")
        if not sys.stdin.isatty():
            sys.exit(1)

# Configuration
BASE_URL = "http://localhost:8000"  # Change if your API runs on different host/port
API_BASE = f"{BASE_URL}/api/v1"


def test_checkout(email: Optional[str] = None):
    """Test creating a checkout session."""
    print("\n" + "="*60)
    print("Testing: POST /api/v1/checkout")
    print("="*60)
    
    url = f"{API_BASE}/checkout"
    payload = {
        "plan_tier": "pro",
        "email": email or "test@example.com",
    }
    
    print(f"URL: {url}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    try:
        response = requests.post(url, json=payload)
        print(f"\nStatus Code: {response.status_code}")
        
        # Try to parse JSON response
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
        except (ValueError, json.JSONDecodeError):
            print(f"Response (raw): {response.text}")
            response_data = {}
        
        if response.status_code == 200:
            if "checkout_url" in response_data:
                print(f"\n✅ SUCCESS! Checkout URL: {response_data['checkout_url']}")
                print(f"   Session ID: {response_data.get('session_id', 'N/A')}")
                return True
            else:
                print(f"\n❌ FAILED: Response missing checkout_url")
                return False
        else:
            print(f"\n❌ FAILED: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to {BASE_URL}")
        print("   Make sure your API server is running: python run_api.py")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def test_webhook():
    """Test webhook endpoint (requires Stripe CLI)."""
    print("\n" + "="*60)
    print("Testing: POST /api/v1/webhook")
    print("="*60)
    print("\n⚠️  Webhook testing requires Stripe CLI")
    print("\nTo test webhooks locally:")
    print("1. Install Stripe CLI: https://stripe.com/docs/stripe-cli")
    print("2. Login: stripe login")
    print("3. Forward webhooks: stripe listen --forward-to localhost:8000/api/v1/webhook")
    print("4. Trigger test event: stripe trigger checkout.session.completed")
    print("\nFor production testing, use Stripe Dashboard → Webhooks → Send test webhook")
    return None


def test_get_subscription(subscription_id: int = 1):
    """Test getting subscription details."""
    print("\n" + "="*60)
    print(f"Testing: GET /api/v1/subscription/{subscription_id}")
    print("="*60)
    
    url = f"{API_BASE}/subscription/{subscription_id}"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"\nStatus Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Response: {json.dumps(data, indent=2)}")
            print("\n✅ SUCCESS!")
            return True
        elif response.status_code == 404:
            print(f"\n⚠️  Subscription {subscription_id} not found")
            print("   Create a subscription first via checkout")
            return False
        else:
            print(f"\n❌ FAILED: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to {BASE_URL}")
        print("   Make sure your API server is running: python run_api.py")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def test_cancel_subscription(subscription_id: int = 1):
    """Test canceling a subscription."""
    print("\n" + "="*60)
    print(f"Testing: POST /api/v1/subscription/{subscription_id}/cancel")
    print("="*60)
    
    url = f"{API_BASE}/subscription/{subscription_id}/cancel"
    print(f"URL: {url}")
    
    try:
        response = requests.post(url)
        print(f"\nStatus Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        
        if response.status_code == 200:
            print("\n✅ SUCCESS!")
            return True
        elif response.status_code == 404:
            print(f"\n⚠️  Subscription {subscription_id} not found")
            return False
        else:
            print(f"\n❌ FAILED: {response.text}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to {BASE_URL}")
        print("   Make sure your API server is running: python run_api.py")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def test_health():
    """Test health endpoint to verify API is running."""
    print("\n" + "="*60)
    print("Testing: GET /health")
    print("="*60)
    
    url = f"{BASE_URL}/health"
    print(f"URL: {url}")
    
    try:
        response = requests.get(url)
        print(f"\nStatus Code: {response.status_code}")
        if response.status_code == 200:
            print(f"Response: {json.dumps(response.json(), indent=2)}")
            print("\n✅ API is running!")
            return True
        else:
            print(f"\n⚠️  Unexpected status: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print(f"\n❌ ERROR: Could not connect to {BASE_URL}")
        print("   Make sure your API server is running: python run_api.py")
        return False
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        return False


def main():
    """Main test runner."""
    print("\n" + "="*60)
    print("Stripe Subscription Endpoints Test Suite")
    print("="*60)
    
    # Display current Stripe configuration
    print(f"\nStripe Configuration:")
    print(f"  Secret Key: {settings.STRIPE_SECRET_KEY[:20] + '...' if settings.STRIPE_SECRET_KEY else 'NOT SET'}")
    print(f"  Price ID Pro: {settings.STRIPE_PRICE_ID_PRO or 'NOT SET'}")
    print(f"  Webhook Secret: {'SET' if settings.STRIPE_WEBHOOK_SECRET else 'NOT SET'}")
    
    # Check if API is running
    if not test_health():
        print("\n⚠️  API server is not running. Start it with: python run_api.py")
        sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        endpoint = sys.argv[1].lower()
    else:
        endpoint = "all"
    
    results = {}
    
    if endpoint in ["checkout", "all"]:
        results["checkout"] = test_checkout()
    
    if endpoint in ["webhook", "all"]:
        results["webhook"] = test_webhook()
    
    if endpoint in ["subscription", "all"]:
        subscription_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        results["subscription"] = test_get_subscription(subscription_id)
    
    if endpoint in ["cancel", "all"]:
        subscription_id = int(sys.argv[2]) if len(sys.argv) > 2 else 1
        results["cancel"] = test_cancel_subscription(subscription_id)
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    for test_name, result in results.items():
        if result is None:
            status = "⚠️  SKIPPED (requires manual setup)"
        elif result:
            status = "✅ PASSED"
        else:
            status = "❌ FAILED"
        print(f"{test_name:20} {status}")
    
    print("\n" + "="*60)
    print("Testing Complete")
    print("="*60)


if __name__ == "__main__":
    main()

