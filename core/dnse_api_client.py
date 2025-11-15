"""
DNSE Lightspeed API Client
Official integration with DNSE trading API
"""
import time
import hmac
import hashlib
import requests
from typing import Dict, List, Optional
from datetime import datetime
from loguru import logger
from utils.config import settings
from utils.cache import cache_manager, CacheKeys, cached


class DNSEAPIClient:
    """
    DNSE Lightspeed API Client

    Features:
    - Authentication with API key/secret
    - Market data (prices, orderbook, trades)
    - Order management (place, cancel, query)
    - Account information
    - Realtime MQTT support
    """

    def __init__(self):
        self.base_url = settings.dnse_api_base_url
        self.api_key = settings.dnse_api_key
        self.api_secret = settings.dnse_api_secret
        self.account_id = settings.dnse_account_id
        self.session = requests.Session()

    def _generate_signature(self, method: str, path: str, timestamp: str, body: str = "") -> str:
        """Generate HMAC-SHA256 signature for authentication"""
        message = f"{timestamp}{method}{path}{body}"
        signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature

    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make authenticated request to DNSE API"""
        url = f"{self.base_url}{endpoint}"
        timestamp = str(int(time.time() * 1000))

        body = ""
        if data:
            import json
            body = json.dumps(data)

        signature = self._generate_signature(method, endpoint, timestamp, body)

        headers = {
            "X-API-KEY": self.api_key,
            "X-SIGNATURE": signature,
            "X-TIMESTAMP": timestamp,
            "Content-Type": "application/json",
        }

        try:
            if method == "GET":
                response = self.session.get(url, headers=headers, params=data)
            elif method == "POST":
                response = self.session.post(url, headers=headers, json=data)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"DNSE API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
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
