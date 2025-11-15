"""
MQTT Price Streaming Module
Handles real-time price data streaming from DNSE via MQTT
"""
import json
import time
from typing import Callable, Dict, List, Optional, Set
from datetime import datetime
from threading import Thread, Lock
import paho.mqtt.client as mqtt
from loguru import logger
from utils.config import settings


class PriceData:
    """Price data model"""

    def __init__(self, data: Dict):
        self.symbol: str = data.get("symbol", "")
        self.price: float = data.get("price", 0.0)
        self.volume: int = data.get("volume", 0)
        self.bid_price: float = data.get("bid_price", 0.0)
        self.ask_price: float = data.get("ask_price", 0.0)
        self.bid_volume: int = data.get("bid_volume", 0)
        self.ask_volume: int = data.get("ask_volume", 0)
        self.high: float = data.get("high", 0.0)
        self.low: float = data.get("low", 0.0)
        self.open: float = data.get("open", 0.0)
        self.close: float = data.get("close", 0.0)
        self.change: float = data.get("change", 0.0)
        self.change_percent: float = data.get("change_percent", 0.0)
        self.timestamp: datetime = datetime.fromisoformat(
            data.get("timestamp", datetime.now().isoformat())
        )

    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "symbol": self.symbol,
            "price": self.price,
            "volume": self.volume,
            "bid_price": self.bid_price,
            "ask_price": self.ask_price,
            "bid_volume": self.bid_volume,
            "ask_volume": self.ask_volume,
            "high": self.high,
            "low": self.low,
            "open": self.open,
            "close": self.close,
            "change": self.change,
            "change_percent": self.change_percent,
            "timestamp": self.timestamp.isoformat(),
        }


class PriceStreamManager:
    """
    Manages MQTT connection and price streaming from DNSE
    Supports multiple symbol subscriptions and callback handlers
    """

    def __init__(self):
        self.client: Optional[mqtt.Client] = None
        self.subscribed_symbols: Set[str] = set()
        self.callbacks: List[Callable[[PriceData], None]] = []
        self.latest_prices: Dict[str, PriceData] = {}
        self.lock = Lock()
        self.is_connected = False
        self.reconnect_delay = 5
        self.max_reconnect_delay = 60

    def add_callback(self, callback: Callable[[PriceData], None]):
        """Add a callback function to be called when price data is received"""
        with self.lock:
            self.callbacks.append(callback)
        logger.info(f"Added price callback: {callback.__name__}")

    def remove_callback(self, callback: Callable[[PriceData], None]):
        """Remove a callback function"""
        with self.lock:
            if callback in self.callbacks:
                self.callbacks.remove(callback)
        logger.info(f"Removed price callback: {callback.__name__}")

    def subscribe(self, symbols: List[str]):
        """Subscribe to price updates for given symbols"""
        for symbol in symbols:
            symbol = symbol.upper()
            if symbol not in self.subscribed_symbols:
                self.subscribed_symbols.add(symbol)
                if self.client and self.is_connected:
                    topic = f"market/price/{symbol}"
                    self.client.subscribe(topic)
                    logger.info(f"Subscribed to {topic}")

    def unsubscribe(self, symbols: List[str]):
        """Unsubscribe from price updates"""
        for symbol in symbols:
            symbol = symbol.upper()
            if symbol in self.subscribed_symbols:
                self.subscribed_symbols.remove(symbol)
                if self.client and self.is_connected:
                    topic = f"market/price/{symbol}"
                    self.client.unsubscribe(topic)
                    logger.info(f"Unsubscribed from {topic}")

    def get_latest_price(self, symbol: str) -> Optional[PriceData]:
        """Get the latest price data for a symbol"""
        with self.lock:
            return self.latest_prices.get(symbol.upper())

    def _on_connect(self, client, userdata, flags, rc):
        """Callback when connected to MQTT broker"""
        if rc == 0:
            self.is_connected = True
            self.reconnect_delay = 5  # Reset reconnect delay
            logger.info("Connected to MQTT broker successfully")

            # Resubscribe to all symbols
            for symbol in self.subscribed_symbols:
                topic = f"market/price/{symbol}"
                client.subscribe(topic)
                logger.info(f"Resubscribed to {topic}")
        else:
            self.is_connected = False
            logger.error(f"Failed to connect to MQTT broker. Return code: {rc}")

    def _on_disconnect(self, client, userdata, rc):
        """Callback when disconnected from MQTT broker"""
        self.is_connected = False
        if rc != 0:
            logger.warning(f"Unexpected disconnect from MQTT broker. Code: {rc}")
            logger.info(f"Will attempt to reconnect in {self.reconnect_delay}s")

    def _on_message(self, client, userdata, msg):
        """Callback when a message is received"""
        try:
            # Parse the message
            payload = json.loads(msg.payload.decode("utf-8"))
            price_data = PriceData(payload)

            # Update latest prices
            with self.lock:
                self.latest_prices[price_data.symbol] = price_data

            # Call all registered callbacks
            with self.lock:
                callbacks = self.callbacks.copy()

            for callback in callbacks:
                try:
                    callback(price_data)
                except Exception as e:
                    logger.error(f"Error in price callback {callback.__name__}: {e}")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to decode MQTT message: {e}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    def connect(self):
        """Connect to MQTT broker"""
        try:
            # Create MQTT client
            self.client = mqtt.Client(client_id=settings.mqtt_client_id)

            # Set username and password if provided
            if settings.mqtt_username and settings.mqtt_password:
                self.client.username_pw_set(
                    settings.mqtt_username, settings.mqtt_password
                )

            # Set callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message

            # Enable auto-reconnect
            self.client.reconnect_delay_set(
                min_delay=1, max_delay=self.max_reconnect_delay
            )

            # Connect to broker
            logger.info(
                f"Connecting to MQTT broker at {settings.mqtt_broker}:{settings.mqtt_port}"
            )
            self.client.connect(settings.mqtt_broker, settings.mqtt_port, keepalive=60)

            # Start the loop in a separate thread
            self.client.loop_start()

            # Wait for connection
            timeout = 10
            start_time = time.time()
            while not self.is_connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)

            if self.is_connected:
                logger.info("MQTT connection established successfully")
                return True
            else:
                logger.error("Failed to establish MQTT connection within timeout")
                return False

        except Exception as e:
            logger.error(f"Error connecting to MQTT broker: {e}")
            return False

    def disconnect(self):
        """Disconnect from MQTT broker"""
        if self.client:
            logger.info("Disconnecting from MQTT broker")
            self.client.loop_stop()
            self.client.disconnect()
            self.is_connected = False

    def start(self):
        """Start the price stream manager"""
        logger.info("Starting Price Stream Manager")
        if not self.connect():
            logger.error("Failed to start Price Stream Manager")
            return False

        logger.info("Price Stream Manager started successfully")
        return True

    def stop(self):
        """Stop the price stream manager"""
        logger.info("Stopping Price Stream Manager")
        self.disconnect()
        logger.info("Price Stream Manager stopped")


# Global instance
price_stream_manager = PriceStreamManager()
