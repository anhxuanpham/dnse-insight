"""
DNSE Lightspeed API Client
Official integration with DNSE trading API
"""
import time
import hmac
import hashlib
import requests
import json
import base64
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from loguru import logger
from utils.config import settings
from utils.cache import cache_manager, CacheKeys, cached


class DNSEAPIClient:
    """
    DNSE Lightspeed API Client

    Features:
    - Token-based authentication (login API)
    - HMAC-SHA256 authentication (API key/secret)
    - Market data (prices, orderbook, trades)
    - Order management (place, cancel, query)
    - Account information
    - Realtime MQTT support
    - Auto token refresh (8 hour expiry)
    """

    def __init__(self):
        self.base_url = settings.dnse_api_base_url
        self.auth_url = getattr(settings, 'dnse_auth_url', 'https://api.dnse.com.vn/auth-service')
        self.api_key = settings.dnse_api_key
        self.api_secret = settings.dnse_api_secret
        self.account_id = settings.dnse_account_id

        # Token-based auth (new)
        self.username = getattr(settings, 'dnse_username', None)
        self.password = getattr(settings, 'dnse_password', None)
        self.token = None
        self.token_expires_at = None
        self.user_info = {}

        self.session = requests.Session()

        # Auto login if username/password provided
        if self.username and self.password:
            self._ensure_token()

    def login(self, username: str = None, password: str = None) -> Dict:
        """
        Login to DNSE and get JWT token

        Args:
            username: DNSE username (custody code, e.g., "064CYIDYCG")
            password: DNSE password

        Returns:
            Response with token and user info

        Example response:
            {
                "token": "eyJ0eXAiOiJKV1QiLCJhbGci...",
                "roles": ["investor"],
                "isNeedReset": false
            }
        """
        username = username or self.username
        password = password or self.password

        if not username or not password:
            logger.error("Username and password required for login")
            return {"success": False, "error": "Missing credentials"}

        url = f"{self.auth_url}/login"
        data = {
            "username": username,
            "password": password
        }

        try:
            logger.info(f"Logging in to DNSE as {username}...")
            response = self.session.post(url, json=data)
            response.raise_for_status()

            result = response.json()

            if "token" in result:
                self.token = result["token"]
                self.user_info = {
                    "roles": result.get("roles", []),
                    "isNeedReset": result.get("isNeedReset", False)
                }

                # Decode JWT to get expiry time
                self._parse_token_expiry()

                # Cache token
                cache_manager.set(
                    "dnse:auth_token",
                    self.token,
                    ttl=28000  # 7h 45min (slightly less than 8h for safety)
                )

                logger.info(f"✅ Login successful! Token expires at {self.token_expires_at}")
                logger.info(f"User: {self._get_token_field('fullName')}")
                logger.info(f"Customer ID: {self._get_token_field('customerId')}")
                logger.info(f"Roles: {self.user_info['roles']}")

                return {"success": True, **result}
            else:
                logger.error(f"Login failed: {result}")
                return {"success": False, "error": "No token in response", **result}

        except requests.exceptions.RequestException as e:
            logger.error(f"Login request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            return {"success": False, "error": str(e)}

    def _parse_token_expiry(self):
        """Parse JWT token to get expiry time"""
        if not self.token:
            return

        try:
            # JWT format: header.payload.signature
            parts = self.token.split('.')
            if len(parts) != 3:
                return

            # Decode payload (add padding if needed)
            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding

            payload = json.loads(base64.b64decode(payload_b64))

            # Get expiry timestamp
            exp = payload.get('exp')
            if exp:
                self.token_expires_at = datetime.fromtimestamp(exp)
                logger.debug(f"Token expires at: {self.token_expires_at}")

            # Store useful info from token
            self.account_id = payload.get('customerId', self.account_id)

        except Exception as e:
            logger.warning(f"Failed to parse token expiry: {e}")

    def _get_token_field(self, field: str) -> Optional[str]:
        """Get a field from JWT token payload"""
        if not self.token:
            return None

        try:
            parts = self.token.split('.')
            if len(parts) != 3:
                return None

            payload_b64 = parts[1]
            padding = 4 - len(payload_b64) % 4
            if padding != 4:
                payload_b64 += '=' * padding

            payload = json.loads(base64.b64decode(payload_b64))
            return payload.get(field)

        except Exception:
            return None

    def _is_token_valid(self) -> bool:
        """Check if current token is still valid"""
        if not self.token:
            return False

        if not self.token_expires_at:
            self._parse_token_expiry()

        if not self.token_expires_at:
            return True  # Can't determine expiry, assume valid

        # Check if token expires within 5 minutes
        return datetime.now() < self.token_expires_at - timedelta(minutes=5)

    def _ensure_token(self) -> bool:
        """Ensure we have a valid token, refresh if needed"""
        # Try to get cached token first
        cached_token = cache_manager.get("dnse:auth_token")
        if cached_token and not self.token:
            self.token = cached_token
            self._parse_token_expiry()
            logger.info("Using cached token")

        # Check if token is valid
        if self._is_token_valid():
            return True

        # Token expired or missing, login again
        logger.info("Token expired or missing, logging in...")
        result = self.login()
        return result.get("success", False)

    def _generate_signature(self, method: str, path: str, timestamp: str, body: str = "") -> str:
        """Generate HMAC-SHA256 signature for authentication"""
        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, use_token: bool = True) -> Dict:
        """
        Make authenticated request to DNSE API

        Args:
            method: HTTP method (GET, POST, DELETE)
            endpoint: API endpoint path
            data: Request data
            use_token: Use token auth (True) or HMAC auth (False)
        """
        url = f"{self.base_url}{endpoint}"

        headers = {
            "Content-Type": "application/json",
        }

        # Choose authentication method
        if use_token and (self.token or (self.username and self.password)):
            # Token-based authentication (preferred)
            self._ensure_token()

            if self.token:
                headers["Authorization"] = f"Bearer {self.token}"
            else:
                logger.warning("Token auth requested but no token available, falling back to HMAC")
                use_token = False

        if not use_token:
            # HMAC-based authentication (fallback)
            timestamp = str(int(time.time() * 1000))

            body = ""
            if data and method in ["POST", "PUT"]:
                body = json.dumps(data)

            signature = self._generate_signature(method, endpoint, timestamp, body)

            headers.update({
                "X-API-KEY": self.api_key,
                "X-SIGNATURE": signature,
                "X-TIMESTAMP": timestamp,
            })

        try:
            if method == "GET":
                response = self.session.get(url, headers=headers, params=data)
            elif method == "POST":
                response = self.session.post(url, headers=headers, json=data)
            elif method == "PUT":
                response = self.session.put(url, headers=headers, json=data)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"DNSE API request failed: {method} {endpoint}")
            logger.error(f"Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"Status code: {e.response.status_code}")
                logger.error(f"Response: {e.response.text}")
            return {"success": False, "error": str(e)}

    # Market Data APIs
    @cached(ttl=5, key_prefix="dnse")
    def get_stock_price(self, symbol: str) -> Dict:
        """Get current stock price"""
        return self._request("GET", f"/v1/market/stock/{symbol}")

    @cached(ttl=10, key_prefix="dnse")
    def get_orderbook(self, symbol: str) -> Dict:
        """Get orderbook (bid/ask)"""
        return self._request("GET", f"/v1/market/orderbook/{symbol}")

    @cached(ttl=60, key_prefix="dnse")
    def get_stock_info(self, symbol: str) -> Dict:
        """Get stock information"""
        return self._request("GET", f"/v1/market/info/{symbol}")

    def get_market_status(self) -> Dict:
        """Get market trading status"""
        return self._request("GET", "/v1/market/status")

    @cached(ttl=30, key_prefix="dnse")
    def get_market_index(self, index: str = "VNINDEX") -> Dict:
        """Get market index (VNINDEX, VN30, HNX)"""
        return self._request("GET", f"/v1/market/index/{index}")

    # Trading APIs
    def place_order(
        self,
        symbol: str,
        side: str,  # BUY or SELL
        quantity: int,
        price: float,
        order_type: str = "LO"  # LO, MP, ATO, ATC, MTL
    ) -> Dict:
        """
        Place order

        Args:
            symbol: Stock symbol (e.g., "VCB")
            side: "BUY" or "SELL"
            quantity: Number of shares
            price: Limit price (0 for market orders)
            order_type: Order type (LO, MP, ATO, ATC, MTL)

        Returns:
            Response with order ID
        """
        data = {
            "accountId": self.account_id,
            "symbol": symbol.upper(),
            "side": side.upper(),
            "quantity": quantity,
            "price": price,
            "orderType": order_type,
        }

        response = self._request("POST", "/v1/orders", data)

        # Invalidate cache
        cache_manager.delete(CacheKeys.ORDER_HISTORY.format(symbol=symbol, days=7))

        return response

    def cancel_order(self, order_id: str) -> Dict:
        """Cancel order"""
        return self._request("DELETE", f"/v1/orders/{order_id}")

    def modify_order(self, order_id: str, quantity: int = None, price: float = None) -> Dict:
        """Modify existing order"""
        data = {}
        if quantity:
            data["quantity"] = quantity
        if price:
            data["price"] = price

        return self._request("POST", f"/v1/orders/{order_id}/modify", data)

    def get_order_status(self, order_id: str) -> Dict:
        """Get order status"""
        return self._request("GET", f"/v1/orders/{order_id}")

    def get_order_history(self, symbol: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> Dict:
        """Get order history"""
        params = {"accountId": self.account_id}
        if symbol:
            params["symbol"] = symbol.upper()
        if from_date:
            params["fromDate"] = from_date
        if to_date:
            params["toDate"] = to_date

        return self._request("GET", "/v1/orders/history", params)

    # Account APIs
    @cached(ttl=10, key_prefix="dnse")
    def get_account_balance(self) -> Dict:
        """Get account balance"""
        return self._request("GET", f"/v1/accounts/{self.account_id}/balance")

    @cached(ttl=30, key_prefix="dnse")
    def get_portfolio(self) -> Dict:
        """Get current portfolio positions"""
        return self._request("GET", f"/v1/accounts/{self.account_id}/portfolio")

    def get_cash_statement(self, from_date: str, to_date: str) -> Dict:
        """Get cash in/out statement"""
        params = {
            "accountId": self.account_id,
            "fromDate": from_date,
            "toDate": to_date,
        }
        return self._request("GET", "/v1/accounts/cash-statement", params)

    def get_asset_information(self) -> Dict:
        """Get total asset information"""
        return self._request("GET", f"/v1/accounts/{self.account_id}/assets")

    # Advanced APIs
    def get_right_exercise(self) -> Dict:
        """Get stock rights information"""
        return self._request("GET", f"/v1/accounts/{self.account_id}/rights")

    def get_advance_payment(self) -> Dict:
        """Get advance payment info"""
        return self._request("GET", f"/v1/accounts/{self.account_id}/advance")

    def transfer_cash(self, amount: float, bank_code: str, bank_account: str) -> Dict:
        """Transfer cash to bank"""
        data = {
            "accountId": self.account_id,
            "amount": amount,
            "bankCode": bank_code,
            "bankAccount": bank_account,
        }
        return self._request("POST", "/v1/accounts/transfer", data)


# Global instance
dnse_client = DNSEAPIClient()
