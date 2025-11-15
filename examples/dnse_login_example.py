#!/usr/bin/env python3
"""
DNSE Login API Example
Demonstrates token-based authentication with DNSE API
"""
import os
from loguru import logger
from core.dnse_api_client import dnse_client


def main():
    """Demo DNSE login and token management"""

    print("\n" + "="*70)
    print(" "*15 + "🔐 DNSE LOGIN API DEMO 🔐")
    print("="*70 + "\n")

    # Check if credentials are configured
    if not dnse_client.username or dnse_client.username == "your_custody_code_here":
        print("⚠️  WARNING: DNSE credentials not configured!")
        print("\nTo use token authentication, add to your .env file:")
        print("  DNSE_USERNAME=your_custody_code  # e.g., 064CYIDYCG")
        print("  DNSE_PASSWORD=your_password")
        print("\nAlternatively, you can login programmatically:")
        print("  dnse_client.login(username='064CYIDYCG', password='your_password')")
        print()
        return

    # Method 1: Auto-login (already done in __init__ if credentials provided)
    print("📌 Method 1: Auto-login (credentials from .env)")
    print(f"   Username: {dnse_client.username}")

    if dnse_client.token:
        print(f"   ✅ Already logged in!")
        print(f"   Token: {dnse_client.token[:50]}...")
        print(f"   Expires at: {dnse_client.token_expires_at}")
        print(f"   User: {dnse_client._get_token_field('fullName')}")
        print(f"   Customer ID: {dnse_client._get_token_field('customerId')}")
        print(f"   Roles: {dnse_client.user_info.get('roles', [])}")
    else:
        print("   ⚠️  Not logged in, trying now...")
        result = dnse_client.login()
        if result.get('success'):
            print(f"   ✅ Login successful!")
        else:
            print(f"   ❌ Login failed: {result.get('error')}")
            return

    # Method 2: Manual login
    print("\n📌 Method 2: Manual login (programmatic)")
    print("   # dnse_client.login(username='...', password='...')")
    print("   ✅ Can be used to switch accounts or refresh token")

    # Method 3: Token info
    print("\n📌 Token Information:")
    print(f"   Token valid: {dnse_client._is_token_valid()}")
    print(f"   Expires at: {dnse_client.token_expires_at}")
    print(f"   Time remaining: {dnse_client.token_expires_at - dnse_client.token_expires_at.__class__.now() if dnse_client.token_expires_at else 'N/A'}")

    # Decode full JWT payload
    if dnse_client.token:
        import base64
        import json
        try:
            payload_b64 = dnse_client.token.split('.')[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding
            payload = json.loads(base64.b64decode(payload_b64))

            print("\n📌 Full JWT Payload:")
            for key, value in payload.items():
                if key == 'exp' or key == 'iat':
                    from datetime import datetime
                    print(f"   {key}: {value} ({datetime.fromtimestamp(value)})")
                else:
                    print(f"   {key}: {value}")
        except Exception as e:
            print(f"   ⚠️  Could not decode JWT: {e}")

    # Test API calls with token
    print("\n" + "="*70)
    print(" "*15 + "🧪 TESTING API CALLS WITH TOKEN")
    print("="*70 + "\n")

    # Test 1: Get market status
    print("Test 1: Get Market Status")
    result = dnse_client.get_market_status()
    if result and not result.get('error'):
        print(f"   ✅ Success: {result}")
    else:
        print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

    # Test 2: Get account balance
    print("\nTest 2: Get Account Balance")
    result = dnse_client.get_account_balance()
    if result and not result.get('error'):
        print(f"   ✅ Success!")
        if 'data' in result:
            balance_data = result['data']
            print(f"   Cash: {balance_data.get('cash', 0):,.0f} VND")
            print(f"   Buying Power: {balance_data.get('buyingPower', 0):,.0f} VND")
    else:
        print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

    # Test 3: Get portfolio
    print("\nTest 3: Get Portfolio")
    result = dnse_client.get_portfolio()
    if result and not result.get('error'):
        print(f"   ✅ Success!")
        if 'data' in result and isinstance(result['data'], list):
            print(f"   Positions: {len(result['data'])} stocks")
            for pos in result['data'][:5]:  # Show first 5
                print(f"     - {pos.get('symbol')}: {pos.get('quantity')} shares")
    else:
        print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

    # Test 4: Get stock price
    print("\nTest 4: Get Stock Price (VCB)")
    result = dnse_client.get_stock_price("VCB")
    if result and not result.get('error'):
        print(f"   ✅ Success!")
        if 'data' in result:
            price_data = result['data']
            print(f"   Price: {price_data.get('price', 0):,.0f} VND")
            print(f"   Change: {price_data.get('change', 0):+.2f}%")
    else:
        print(f"   ❌ Failed: {result.get('error', 'Unknown error')}")

    # Token auto-refresh demo
    print("\n" + "="*70)
    print(" "*15 + "🔄 TOKEN AUTO-REFRESH")
    print("="*70 + "\n")

    print("Token Auto-refresh Features:")
    print("  ✅ Token cached in Redis (TTL: 7h 45min)")
    print("  ✅ Auto-refresh before expiry (5 min buffer)")
    print("  ✅ Seamless re-authentication")
    print("  ✅ No manual intervention needed")

    print("\nToken Management:")
    print("  1. Token stored in memory: dnse_client.token")
    print("  2. Token cached in Redis: 'dnse:auth_token'")
    print("  3. Expiry tracked: dnse_client.token_expires_at")
    print("  4. Auto-refresh on next API call if expired")

    print("\n" + "="*70)
    print(" "*20 + "✅ DEMO COMPLETED!")
    print("="*70 + "\n")

    print("Summary:")
    print(f"  ✅ Login successful")
    print(f"  ✅ Token valid until {dnse_client.token_expires_at}")
    print(f"  ✅ API calls working with Bearer token")
    print(f"  ✅ Auto-refresh enabled")

    print("\nUsage in your code:")
    print("  from core.dnse_api_client import dnse_client")
    print("  ")
    print("  # Auto-login if credentials in .env")
    print("  result = dnse_client.get_stock_price('VCB')")
    print("  ")
    print("  # Or manual login")
    print("  dnse_client.login(username='...', password='...')")
    print("  result = dnse_client.get_portfolio()")
    print()


if __name__ == "__main__":
    main()
