"""
AI Trading Assistant
Natural language interface for trading operations using LLM
"""
from typing import Dict, List, Optional, Callable
import json
from datetime import datetime
from loguru import logger

# LangChain imports (will be optional dependencies)
try:
    from langchain.chat_models import ChatOpenAI
    from langchain.agents import AgentExecutor, create_openai_functions_agent
    from langchain.tools import Tool
    from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    logger.warning("LangChain not installed. AI Assistant will have limited functionality.")

from core.price_stream import price_stream_manager
from core.risk_manager import risk_manager
from core.order_executor import order_executor, OrderSide, OrderType
from core.signal_engine import signal_engine


class TradingAssistant:
    """
    AI-Powered Trading Assistant

    Capabilities:
    - Natural language queries about prices, portfolio, signals
    - Voice commands for trading operations
    - Market analysis and recommendations
    - Trading execution via natural language
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.llm = None
        self.agent_executor = None
        self.conversation_history = []

        if LANGCHAIN_AVAILABLE and api_key:
            self._initialize_agent()

    def _initialize_agent(self):
        """Initialize LangChain agent with trading tools"""
        # Initialize LLM
        self.llm = ChatOpenAI(
            api_key=self.api_key,
            model="gpt-4",
            temperature=0,
        )

        # Define tools
        tools = [
            Tool(
                name="get_price",
                func=self._get_price,
                description="Get current price for a stock symbol. Input: symbol (e.g., 'VCB')",
            ),
            Tool(
                name="get_portfolio",
                func=self._get_portfolio,
                description="Get current portfolio summary including positions and P&L",
            ),
            Tool(
                name="get_signals",
                func=self._get_signals,
                description="Get trading signals for a symbol. Input: symbol (e.g., 'VCB')",
            ),
            Tool(
                name="place_order",
                func=self._place_order,
                description=(
                    "Place a trading order. Input: JSON string with keys "
                    "'symbol', 'side' (BUY/SELL), 'quantity', 'price' (optional)"
                ),
            ),
            Tool(
                name="analyze_symbol",
                func=self._analyze_symbol,
                description="Get comprehensive analysis of a symbol including technicals and signals",
            ),
        ]

        # Create prompt template
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert trading assistant for the Vietnamese stock market.
            You help users with:
            - Getting current prices and market data
            - Analyzing stocks using technical indicators
            - Managing portfolio and positions
            - Executing trades safely

            Always confirm with the user before executing trades.
            Provide clear, concise answers.
            Use technical analysis when discussing signals.
            """),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])

        # Create agent
        agent = create_openai_functions_agent(self.llm, tools, prompt)
        self.agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        logger.info("AI Trading Assistant initialized")

    def _get_price(self, symbol: str) -> str:
        """Get current price for symbol"""
        price_data = price_stream_manager.get_latest_price(symbol.upper())
        if not price_data:
            return f"No price data available for {symbol}"

        return json.dumps({
            "symbol": symbol,
            "price": price_data.price,
            "change": price_data.change,
            "change_percent": price_data.change_percent,
            "volume": price_data.volume,
            "timestamp": price_data.timestamp.isoformat(),
        })

    def _get_portfolio(self, _: str = "") -> str:
        """Get portfolio summary"""
        summary = risk_manager.get_portfolio_summary()
        return json.dumps(summary, indent=2)

    def _get_signals(self, symbol: str) -> str:
        """Get trading signals"""
        price_data = price_stream_manager.get_latest_price(symbol.upper())
        if not price_data:
            return f"No price data available for {symbol}"

        signal = signal_engine.generate_signal(symbol.upper(), price_data.price)
        if not signal:
            return "Insufficient data for signal generation"

        return json.dumps(signal.to_dict(), indent=2)

    def _place_order(self, order_json: str) -> str:
        """Place trading order"""
        try:
            order_data = json.loads(order_json)

            symbol = order_data["symbol"].upper()
            side = OrderSide[order_data["side"].upper()]
            quantity = int(order_data["quantity"])
            price = float(order_data.get("price", 0))
            order_type = OrderType.LIMIT if price > 0 else OrderType.MARKET

            order = order_executor.place_order(
                symbol=symbol,
                side=side,
                quantity=quantity,
                price=price,
                order_type=order_type,
            )

            if order:
                return f"Order placed successfully: {order.to_dict()}"
            else:
                return "Order placement failed"

        except Exception as e:
            return f"Error placing order: {str(e)}"

    def _analyze_symbol(self, symbol: str) -> str:
        """Comprehensive symbol analysis"""
        symbol = symbol.upper()

        # Get price data
        price_data = price_stream_manager.get_latest_price(symbol)
        if not price_data:
            return f"No data available for {symbol}"

        # Get signal
        signal = signal_engine.generate_signal(symbol, price_data.price)

        # Get technical indicators
        sma_20 = signal_engine.calculate_sma(symbol, 20)
        sma_50 = signal_engine.calculate_sma(symbol, 50)
        rsi = signal_engine.calculate_rsi(symbol, 14)
        support, resistance = signal_engine.detect_support_resistance(symbol, 50)

        analysis = {
            "symbol": symbol,
            "current_price": price_data.price,
            "change_percent": price_data.change_percent,
            "volume": price_data.volume,
            "technical_indicators": {
                "sma_20": sma_20,
                "sma_50": sma_50,
                "rsi": rsi,
                "support": support,
                "resistance": resistance,
            },
            "signal": signal.to_dict() if signal else None,
        }

        return json.dumps(analysis, indent=2)

    def chat(self, message: str) -> str:
        """
        Chat with the AI assistant

        Args:
            message: User message/query

        Returns:
            Assistant response
        """
        if not LANGCHAIN_AVAILABLE or not self.agent_executor:
            return self._basic_response(message)

        try:
            response = self.agent_executor.invoke({
                "input": message,
                "chat_history": self.conversation_history,
            })

            # Update conversation history
            self.conversation_history.append({
                "role": "user",
                "content": message,
                "timestamp": datetime.now().isoformat(),
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": response["output"],
                "timestamp": datetime.now().isoformat(),
            })

            return response["output"]

        except Exception as e:
            logger.error(f"Error in AI assistant: {e}")
            return f"Sorry, I encountered an error: {str(e)}"

    def _basic_response(self, message: str) -> str:
        """Basic responses without LLM (fallback)"""
        message_lower = message.lower()

        if "price" in message_lower or "giá" in message_lower:
            # Try to extract symbol
            words = message.upper().split()
            for word in words:
                if len(word) == 3 and word.isalpha():
                    return self._get_price(word)
            return "Please specify a symbol (e.g., 'price of VCB')"

        elif "portfolio" in message_lower or "danh mục" in message_lower:
            return self._get_portfolio()

        elif "signal" in message_lower or "tín hiệu" in message_lower:
            words = message.upper().split()
            for word in words:
                if len(word) == 3 and word.isalpha():
                    return self._get_signals(word)
            return "Please specify a symbol for signals"

        else:
            return (
                "I can help you with:\n"
                "- Get price: 'What is the price of VCB?'\n"
                "- Portfolio: 'Show my portfolio'\n"
                "- Signals: 'Get signals for VCB'\n"
                "- Analysis: 'Analyze VCB'\n"
                "\nNote: Install langchain for full AI capabilities"
            )


# Global instance (will need API key)
trading_assistant = TradingAssistant()
