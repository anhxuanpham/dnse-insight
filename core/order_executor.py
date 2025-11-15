"""
Order Executor Module
Handles order placement via DNSE REST API
"""
from typing import Dict, List, Optional
from enum import Enum
from datetime import datetime
import time
import hmac
import hashlib
import json
import requests
from loguru import logger
from utils.config import settings


class OrderSide(Enum):
    """Order side"""

    BUY = "BUY"
    SELL = "SELL"


class OrderType(Enum):
    """Order type"""

    LIMIT = "LO"  # Limit Order
    MARKET = "MP"  # Market Price
    ATO = "ATO"  # At the Open
    ATC = "ATC"  # At the Close
    MTL = "MTL"  # Match or Cancel (MOK in Vietnam)


class OrderStatus(Enum):
    """Order status"""

    PENDING = "PENDING"
    FILLED = "FILLED"
    PARTIALLY_FILLED = "PARTIALLY_FILLED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"


class Order:
    """Order model"""

    def __init__(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        price: float = 0,
        order_type: OrderType = OrderType.LIMIT,
        order_id: str = None,
    ):
        self.symbol = symbol.upper()
        self.side = side
        self.quantity = quantity
        self.price = price
        self.order_type = order_type
        self.order_id = order_id
        self.status = OrderStatus.PENDING
        self.filled_quantity = 0
        self.avg_filled_price = 0.0
        self.created_at = datetime.now()
        self.updated_at = datetime.now()
        self.error_message = None

    def to_dict(self) -> Dict:
        return {
            "order_id": self.order_id,
            "symbol": self.symbol,
            "side": self.side.value,
            "quantity": self.quantity,
            "price": self.price,
            "order_type": self.order_type.value,
            "status": self.status.value,
            "filled_quantity": self.filled_quantity,
            "avg_filled_price": self.avg_filled_price,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "error_message": self.error_message,
        }

    def __repr__(self):
        return f"Order({self.symbol}, {self.side.value}, {self.quantity}@{self.price}, {self.status.value})"


class OrderExecutor:
    """
    Handles order execution via DNSE REST API
    Supports:
    - Placing orders (market, limit, ATO, ATC)
    - Canceling orders
    - Querying order status
    - Querying positions
    - Paper trading mode
    """

    def __init__(self):
        self.base_url = settings.dnse_api_base_url
        self.api_key = settings.dnse_api_key
        self.api_secret = settings.dnse_api_secret
        self.account_id = settings.dnse_account_id
        self.session = requests.Session()
        self.orders: Dict[str, Order] = {}

        # Paper trading
        self.paper_mode = settings.trading_mode == "paper"
        self.paper_positions: Dict[str, int] = {}  # symbol -> quantity
        self.paper_cash = 1_000_000_000  # 1 billion VND for paper trading

    def _generate_signature(self, method: str, endpoint: str, body: str = "") -> str:
        """Generate HMAC signature for API authentication"""
        timestamp = str(int(time.time() * 1000))
        message = f"{timestamp}{method}{endpoint}{body}"
        signature = hmac.new(
            self.api_secret.encode(), message.encode(), hashlib.sha256
        ).hexdigest()
        return signature, timestamp

    def _make_request(
        self, method: str, endpoint: str, data: Dict = None
    ) -> Optional[Dict]:
        """Make authenticated request to DNSE API"""
        if self.paper_mode:
            logger.info(f"[PAPER MODE] {method} {endpoint} {data}")
            return {"success": True, "message": "Paper trading mode"}

        try:
            url = f"{self.base_url}{endpoint}"
            body = json.dumps(data) if data else ""
            signature, timestamp = self._generate_signature(method, endpoint, body)

            headers = {
                "X-API-KEY": self.api_key,
                "X-SIGNATURE": signature,
                "X-TIMESTAMP": timestamp,
                "Content-Type": "application/json",
            }

            if method == "GET":
                response = self.session.get(url, headers=headers)
            elif method == "POST":
                response = self.session.post(url, headers=headers, json=data)
            elif method == "DELETE":
                response = self.session.delete(url, headers=headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            return None

    def place_order(
        self,
        symbol: str,
        side: OrderSide,
        quantity: int,
        price: float = 0,
        order_type: OrderType = OrderType.LIMIT,
    ) -> Optional[Order]:
        """
        Place an order
        Returns Order object if successful, None otherwise
        """
        order = Order(
            symbol=symbol,
            side=side,
            quantity=quantity,
            price=price,
            order_type=order_type,
        )

        logger.info(f"Placing order: {order}")

        if self.paper_mode:
            # Paper trading simulation
            order.order_id = f"PAPER_{int(time.time()*1000)}"
            order.status = OrderStatus.FILLED
            order.filled_quantity = quantity
            order.avg_filled_price = price

            # Update paper positions
            if side == OrderSide.BUY:
                self.paper_cash -= quantity * price
                self.paper_positions[symbol] = (
                    self.paper_positions.get(symbol, 0) + quantity
                )
            else:  # SELL
                self.paper_cash += quantity * price
                self.paper_positions[symbol] = (
                    self.paper_positions.get(symbol, 0) - quantity
                )

            self.orders[order.order_id] = order
            logger.info(
                f"[PAPER MODE] Order placed: {order.order_id}, Cash: {self.paper_cash:,.0f}"
            )
            return order

        # Real trading
        data = {
            "accountId": self.account_id,
            "symbol": symbol.upper(),
            "side": side.value,
            "quantity": quantity,
            "orderType": order_type.value,
        }

        if order_type == OrderType.LIMIT:
            data["price"] = price

        response = self._make_request("POST", "/v1/orders", data)

        if response and response.get("success"):
            order.order_id = response.get("orderId")
            order.status = OrderStatus.PENDING
            self.orders[order.order_id] = order
            logger.info(f"Order placed successfully: {order.order_id}")
            return order
        else:
            order.status = OrderStatus.REJECTED
            order.error_message = response.get("message", "Unknown error")
            logger.error(f"Order placement failed: {order.error_message}")
            return None

    def cancel_order(self, order_id: str) -> bool:
        """
        Cancel an order
        Returns True if successful, False otherwise
        """
        logger.info(f"Canceling order: {order_id}")

        if self.paper_mode:
            if order_id in self.orders:
                self.orders[order_id].status = OrderStatus.CANCELLED
                logger.info(f"[PAPER MODE] Order cancelled: {order_id}")
                return True
            return False

        # Real trading
        response = self._make_request("DELETE", f"/v1/orders/{order_id}")

        if response and response.get("success"):
            if order_id in self.orders:
                self.orders[order_id].status = OrderStatus.CANCELLED
                self.orders[order_id].updated_at = datetime.now()
            logger.info(f"Order cancelled successfully: {order_id}")
            return True
        else:
            logger.error(f"Order cancellation failed: {response.get('message')}")
            return False

    def get_order_status(self, order_id: str) -> Optional[Order]:
        """
        Get order status from API and update local order
        """
        if self.paper_mode:
            return self.orders.get(order_id)

        response = self._make_request("GET", f"/v1/orders/{order_id}")

        if response and response.get("success"):
            order_data = response.get("data", {})
            if order_id in self.orders:
                order = self.orders[order_id]
                order.status = OrderStatus[order_data.get("status", "PENDING")]
                order.filled_quantity = order_data.get("filledQuantity", 0)
                order.avg_filled_price = order_data.get("avgFilledPrice", 0.0)
                order.updated_at = datetime.now()
                return order

        return None

    def get_positions(self) -> Dict[str, int]:
        """
        Get current positions
        Returns dict of symbol -> quantity
        """
        if self.paper_mode:
            logger.info(f"[PAPER MODE] Positions: {self.paper_positions}")
            return self.paper_positions.copy()

        response = self._make_request("GET", f"/v1/accounts/{self.account_id}/positions")

        if response and response.get("success"):
            positions = {}
            for position in response.get("data", []):
                symbol = position.get("symbol")
                quantity = position.get("quantity", 0)
                if quantity > 0:
                    positions[symbol] = quantity
            return positions

        return {}

    def get_account_balance(self) -> Dict[str, float]:
        """
        Get account balance information
        Returns dict with cash, buying_power, total_value, etc.
        """
        if self.paper_mode:
            return {
                "cash": self.paper_cash,
                "buying_power": self.paper_cash,
                "total_value": self.paper_cash,
                "positions_value": 0,
            }

        response = self._make_request("GET", f"/v1/accounts/{self.account_id}/balance")

        if response and response.get("success"):
            data = response.get("data", {})
            return {
                "cash": data.get("cash", 0),
                "buying_power": data.get("buyingPower", 0),
                "total_value": data.get("totalValue", 0),
                "positions_value": data.get("positionsValue", 0),
            }

        return {}

    def get_order_history(self, symbol: str = None, days: int = 7) -> List[Order]:
        """
        Get order history
        """
        if self.paper_mode:
            orders = list(self.orders.values())
            if symbol:
                orders = [o for o in orders if o.symbol == symbol.upper()]
            return orders

        params = {"days": days}
        if symbol:
            params["symbol"] = symbol.upper()

        response = self._make_request(
            "GET", f"/v1/accounts/{self.account_id}/orders", params
        )

        if response and response.get("success"):
            orders = []
            for order_data in response.get("data", []):
                order = Order(
                    symbol=order_data.get("symbol"),
                    side=OrderSide[order_data.get("side")],
                    quantity=order_data.get("quantity"),
                    price=order_data.get("price", 0),
                    order_type=OrderType[order_data.get("orderType")],
                    order_id=order_data.get("orderId"),
                )
                order.status = OrderStatus[order_data.get("status")]
                order.filled_quantity = order_data.get("filledQuantity", 0)
                order.avg_filled_price = order_data.get("avgFilledPrice", 0.0)
                orders.append(order)
            return orders

        return []


# Global instance
order_executor = OrderExecutor()
