"""
Dashboard Backend - FastAPI Application
Real-time dashboard with WebSocket support for price streaming
"""
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import asyncio
import json
from loguru import logger

from core.price_stream import price_stream_manager, PriceData
from core.risk_manager import risk_manager
from core.signal_engine import signal_engine
from core.order_executor import order_executor
from utils.config import settings


# FastAPI app
app = FastAPI(
    title="DNSE Insight Dashboard API",
    description="Real-time trading dashboard for Vietnamese stock market",
    version="1.0.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# WebSocket connection manager
class ConnectionManager:
    """Manages WebSocket connections for real-time updates"""

    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.subscriptions: Dict[WebSocket, List[str]] = {}

    async def connect(self, websocket: WebSocket):
        """Accept new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.subscriptions[websocket] = []
        logger.info(f"WebSocket connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        self.active_connections.remove(websocket)
        if websocket in self.subscriptions:
            del self.subscriptions[websocket]
        logger.info(f"WebSocket disconnected. Total connections: {len(self.active_connections)}")

    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        await websocket.send_json(message)

    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to client: {e}")

    async def send_to_subscribers(self, symbol: str, message: dict):
        """Send message to clients subscribed to specific symbol"""
        for connection, symbols in self.subscriptions.items():
            if symbol in symbols:
                try:
                    await connection.send_json(message)
                except Exception as e:
                    logger.error(f"Error sending to subscriber: {e}")


manager = ConnectionManager()


# Pydantic models
class SymbolSubscribe(BaseModel):
    symbols: List[str]


class OrderRequest(BaseModel):
    symbol: str
    side: str
    quantity: int
    price: Optional[float] = None
    order_type: str = "LIMIT"


class PositionResponse(BaseModel):
    symbol: str
    quantity: int
    avg_entry_price: float
    current_price: float
    pnl: float
    pnl_percent: float


class PortfolioSummary(BaseModel):
    total_value: float
    cash: float
    positions_value: float
    total_pnl: float
    total_return: float
    num_positions: int


# REST API Endpoints

@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "DNSE Insight Dashboard API",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "mqtt_connected": price_stream_manager.is_connected,
        "timestamp": datetime.now().isoformat(),
    }


@app.get("/api/v1/portfolio/summary")
async def get_portfolio_summary() -> PortfolioSummary:
    """Get portfolio summary"""
    summary = risk_manager.get_portfolio_summary()
    return PortfolioSummary(**summary)


@app.get("/api/v1/portfolio/positions")
async def get_positions() -> List[PositionResponse]:
    """Get all current positions"""
    positions = []
    for symbol, position in risk_manager.positions.items():
        positions.append(
            PositionResponse(
                symbol=position.symbol,
                quantity=position.quantity,
                avg_entry_price=position.avg_entry_price,
                current_price=position.current_price,
                pnl=position.pnl,
                pnl_percent=position.pnl_percent,
            )
        )
    return positions


@app.get("/api/v1/market/price/{symbol}")
async def get_price(symbol: str):
    """Get latest price for a symbol"""
    price_data = price_stream_manager.get_latest_price(symbol.upper())
    if not price_data:
        raise HTTPException(status_code=404, detail=f"Price data not found for {symbol}")
    return price_data.to_dict()


@app.get("/api/v1/market/signals/{symbol}")
async def get_signals(symbol: str):
    """Get latest trading signals for a symbol"""
    latest_price = price_stream_manager.get_latest_price(symbol.upper())
    if not latest_price:
        raise HTTPException(status_code=404, detail=f"Price data not found for {symbol}")

    signal = signal_engine.generate_signal(symbol.upper(), latest_price.price)
    if not signal:
        return {"message": "Insufficient data for signal generation"}

    return signal.to_dict()


@app.post("/api/v1/orders/place")
async def place_order(order: OrderRequest):
    """Place a new order"""
    from core.order_executor import OrderSide, OrderType

    try:
        side = OrderSide[order.side.upper()]
        order_type = OrderType[order.order_type.upper()]

        result = order_executor.place_order(
            symbol=order.symbol.upper(),
            side=side,
            quantity=order.quantity,
            price=order.price or 0,
            order_type=order_type,
        )

        if result:
            return {"status": "success", "order": result.to_dict()}
        else:
            raise HTTPException(status_code=400, detail="Order placement failed")

    except KeyError as e:
        raise HTTPException(status_code=400, detail=f"Invalid parameter: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/orders/history")
async def get_order_history(symbol: Optional[str] = None, days: int = 7):
    """Get order history"""
    orders = order_executor.get_order_history(symbol=symbol, days=days)
    return [order.to_dict() for order in orders]


@app.get("/api/v1/market/heatmap")
async def get_market_heatmap():
    """Get market heatmap data"""
    # Get all VN30 symbols
    vn30_symbols = [
        "VCB", "VHM", "VIC", "VNM", "FPT", "GAS", "MSN", "MWG", "VPB", "HPG",
        "TCB", "BID", "CTG", "SAB", "SSI", "VRE", "PLX", "POW", "MBB", "ACB",
        "GVR", "HDB", "TPB", "VJC", "PDR", "STB", "NVL", "BCM", "KDH", "VCG",
    ]

    heatmap_data = []
    for symbol in vn30_symbols:
        price_data = price_stream_manager.get_latest_price(symbol)
        if price_data:
            heatmap_data.append({
                "symbol": symbol,
                "price": price_data.price,
                "change": price_data.change,
                "change_percent": price_data.change_percent,
                "volume": price_data.volume,
            })

    return heatmap_data


@app.get("/api/v1/market/watchlist")
async def get_watchlist():
    """Get watchlist with auto-scanned signals"""
    # Example watchlist symbols
    watchlist_symbols = ["VCB", "VHM", "VIC", "FPT", "HPG"]

    watchlist = []
    for symbol in watchlist_symbols:
        price_data = price_stream_manager.get_latest_price(symbol)
        if price_data:
            signal = signal_engine.generate_signal(symbol, price_data.price)
            watchlist.append({
                "symbol": symbol,
                "price": price_data.price,
                "change_percent": price_data.change_percent,
                "volume": price_data.volume,
                "signal": signal.to_dict() if signal else None,
            })

    return watchlist


# WebSocket endpoint
@app.websocket("/ws/market")
async def websocket_market_data(websocket: WebSocket):
    """
    WebSocket endpoint for real-time market data
    Clients can subscribe to specific symbols
    """
    await manager.connect(websocket)

    try:
        # Send initial connection message
        await manager.send_personal_message(
            {"type": "connected", "message": "Connected to market data stream"},
            websocket,
        )

        # Listen for messages from client
        async def receive_messages():
            while True:
                try:
                    data = await websocket.receive_json()
                    message_type = data.get("type")

                    if message_type == "subscribe":
                        symbols = data.get("symbols", [])
                        manager.subscriptions[websocket] = [s.upper() for s in symbols]
                        await manager.send_personal_message(
                            {"type": "subscribed", "symbols": symbols},
                            websocket,
                        )
                        logger.info(f"Client subscribed to: {symbols}")

                    elif message_type == "unsubscribe":
                        symbols = data.get("symbols", [])
                        current_subs = manager.subscriptions.get(websocket, [])
                        for symbol in symbols:
                            if symbol.upper() in current_subs:
                                current_subs.remove(symbol.upper())
                        await manager.send_personal_message(
                            {"type": "unsubscribed", "symbols": symbols},
                            websocket,
                        )

                except WebSocketDisconnect:
                    break
                except Exception as e:
                    logger.error(f"Error receiving message: {e}")
                    break

        # Send market data updates
        async def send_market_updates():
            while websocket in manager.active_connections:
                try:
                    # Send updates for subscribed symbols
                    subscribed_symbols = manager.subscriptions.get(websocket, [])
                    for symbol in subscribed_symbols:
                        price_data = price_stream_manager.get_latest_price(symbol)
                        if price_data:
                            await manager.send_personal_message(
                                {
                                    "type": "price_update",
                                    "data": price_data.to_dict(),
                                },
                                websocket,
                            )

                    # Send portfolio update
                    if risk_manager.positions:
                        summary = risk_manager.get_portfolio_summary()
                        await manager.send_personal_message(
                            {"type": "portfolio_update", "data": summary},
                            websocket,
                        )

                    await asyncio.sleep(1)  # Update every second

                except Exception as e:
                    logger.error(f"Error sending updates: {e}")
                    break

        # Run both tasks concurrently
        await asyncio.gather(
            receive_messages(),
            send_market_updates(),
        )

    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        manager.disconnect(websocket)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    logger.info("Starting Dashboard API...")
    # Price stream will be started by the main trading bot
    # This is just the API layer


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down Dashboard API...")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
