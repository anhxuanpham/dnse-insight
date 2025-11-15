# DNSE Insight - Vietnam Trading Bot System

🚀 **Real-time automated trading bot for Vietnamese stock market using DNSE API**

Hệ thống trading bot tự động cho thị trường chứng khoán Việt Nam với các tính năng:
- ✅ Real-time price streaming qua MQTT
- ✅ Tự động phân tích kỹ thuật và tạo tín hiệu
- ✅ Auto-buy khi giá phá kháng cự
- ✅ Auto-sell khi xuyên hỗ trợ
- ✅ Auto-cutloss khi biến động mạnh
- ✅ Virtual STOP LOSS (Vì VN không có stop loss chuẩn)
- ✅ DCA Bot (Dollar Cost Averaging)
- ✅ Risk management tự động
- ✅ Telegram notifications
- ✅ Paper trading mode để test

## 📋 Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Trading Strategies](#trading-strategies)
- [API Documentation](#api-documentation)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

## ✨ Features

### 1. Trading Bot Realtime (Core)

**Price Streaming:**
- MQTT real-time price streaming from DNSE
- Multi-symbol subscription
- Automatic reconnection
- Price history management

**Signal Generation:**
- Breakout strategy (resistance/support)
- Moving average crossover (SMA, EMA)
- RSI overbought/oversold
- Volume surge detection
- Bollinger Bands
- Multi-timeframe analysis

**Order Execution:**
- REST API integration with DNSE
- Market orders, Limit orders
- ATO (At The Open), ATC (At The Close)
- Paper trading mode
- Order status tracking

**Risk Management:**
- Position sizing based on risk per trade
- Virtual stop-loss monitoring
- Trailing stop-loss
- Maximum drawdown protection
- Portfolio-level risk management

**DCA Bot:**
- Periodic buying (Dollar Cost Averaging)
- Configurable intervals
- Auto position sizing
- Support for multiple symbols

### 2. Notifications

- Telegram integration
- Real-time trade alerts
- Portfolio updates
- Error notifications

## 🏗️ Architecture

```
dnse-insight/
├── core/                      # Core trading components
│   ├── price_stream.py       # MQTT price streaming
│   ├── signal_engine.py      # Technical analysis & signals
│   ├── order_executor.py     # Order execution via REST
│   ├── risk_manager.py       # Risk & position management
│   └── trading_bot.py        # Main orchestrator
├── utils/                     # Utilities
│   ├── config.py             # Configuration management
│   ├── logger.py             # Logging setup
│   └── notifications.py      # Telegram notifications
├── strategies/                # Custom trading strategies
├── tests/                     # Unit tests
├── data/                      # Data storage
├── logs/                      # Log files
├── main.py                    # Main entry point
├── requirements.txt           # Python dependencies
└── .env.example              # Environment variables example
```

## 📦 Installation

### Prerequisites

- Python 3.9+
- DNSE trading account
- DNSE API credentials
- Redis (optional, for advanced features)

### Steps

1. **Clone the repository:**
```bash
git clone https://github.com/yourusername/dnse-insight.git
cd dnse-insight
```

2. **Create virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Install TA-Lib (required for technical indicators):**

**Ubuntu/Debian:**
```bash
wget http://prdownloads.sourceforge.net/ta-lib/ta-lib-0.4.0-src.tar.gz
tar -xzf ta-lib-0.4.0-src.tar.gz
cd ta-lib/
./configure --prefix=/usr
make
sudo make install
```

**macOS:**
```bash
brew install ta-lib
```

**Windows:**
Download and install from: http://www.lfd.uci.edu/~gohlke/pythonlibs/#ta-lib

5. **Configure environment:**
```bash
cp .env.example .env
nano .env  # Edit with your DNSE credentials
```

6. **Run tests:**
```bash
pytest tests/
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# DNSE API Configuration
DNSE_API_BASE_URL=https://api.dnse.com.vn
DNSE_API_KEY=your_api_key_here
DNSE_API_SECRET=your_api_secret_here
DNSE_ACCOUNT_ID=your_account_id_here

# MQTT Configuration
MQTT_BROKER=mqtt.dnse.com.vn
MQTT_PORT=1883
MQTT_USERNAME=your_mqtt_username
MQTT_PASSWORD=your_mqtt_password

# Trading Configuration
TRADING_MODE=paper  # paper or live
MAX_POSITION_SIZE=100000000  # 100M VND
MAX_POSITIONS=10
RISK_PER_TRADE=0.02  # 2%
DEFAULT_STOP_LOSS_PCT=0.03  # 3%

# DCA Bot Configuration
DCA_ENABLED=false
DCA_INTERVAL_HOURS=24
DCA_AMOUNT_PER_ORDER=10000000  # 10M VND
DCA_SYMBOLS=VCB,VHM,VIC

# Telegram Notifications
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
TELEGRAM_ENABLED=true
```

### Getting DNSE API Credentials

1. Login to DNSE account
2. Go to Settings > API Management
3. Create new API key
4. Copy API Key, Secret, and Account ID
5. Enable MQTT access

### Setting up Telegram Bot

1. Create a bot via [@BotFather](https://t.me/botfather)
2. Get bot token
3. Get your chat ID via [@userinfobot](https://t.me/userinfobot)
4. Add to `.env` file

## 🚀 Usage

### Basic Usage

**Run with specific symbols:**
```bash
python main.py --symbols VCB VHM VIC FPT
```

**Run with VN30 stocks:**
```bash
python main.py --vn30
```

**Run in live trading mode:**
```bash
python main.py --symbols VCB VHM --mode live
```

**Enable DCA bot:**
```bash
python main.py --symbols VCB VHM --dca --dca-symbols VCB VIC
```

### Advanced Usage

**Custom DCA settings:**
```bash
python main.py --symbols VCB VHM \
  --dca \
  --dca-symbols VCB VIC \
  --dca-interval 12 \
  --dca-amount 20000000
```

### Running as a Service (Linux)

Create systemd service file:

```bash
sudo nano /etc/systemd/system/dnse-bot.service
```

```ini
[Unit]
Description=DNSE Trading Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/path/to/dnse-insight
Environment=PATH=/path/to/dnse-insight/venv/bin
ExecStart=/path/to/dnse-insight/venv/bin/python main.py --vn30
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable dnse-bot
sudo systemctl start dnse-bot
sudo systemctl status dnse-bot
```

## 📊 Trading Strategies

### 1. Breakout Strategy

Tự động mua khi giá phá vỡ kháng cự:
- Detect resistance levels using recent highs
- Buy when price breaks above resistance
- Set stop-loss below breakout level

### 2. Support/Resistance Strategy

- Buy when price bounces off support
- Sell when price breaks below support
- Use recent lows/highs for levels

### 3. Moving Average Crossover

- Golden Cross: Buy when SMA20 crosses above SMA50
- Death Cross: Sell when SMA20 crosses below SMA50

### 4. RSI Strategy

- Buy when RSI < 30 (oversold)
- Sell when RSI > 70 (overbought)

### 5. Volume Surge Strategy

- Buy when volume surges 2x+ with price increase
- Indicates strong buying pressure

### 6. Volatility Cutloss

- Auto cutloss when volatility exceeds threshold
- Protects against sudden market crashes

## 📈 Risk Management

### Position Sizing

Position size is calculated based on:
- Risk per trade (default 2%)
- Distance to stop-loss
- Account capital

Formula:
```
Position Size = (Account Capital × Risk%) / (Entry Price - Stop Loss Price)
```

### Stop Loss Types

1. **Fixed Percentage Stop Loss**: Default 3% below entry
2. **Trailing Stop Loss**: Moves up with price, never down
3. **Volatility-based Stop Loss**: Based on ATR

### Portfolio Limits

- Max positions: 10 (configurable)
- Max position size: 100M VND (configurable)
- Max drawdown: 10% (configurable)

## 🗺️ Roadmap

### Completed (Feature #1)
- ✅ MQTT real-time price streaming
- ✅ REST API order execution
- ✅ Technical analysis signals
- ✅ Virtual stop-loss
- ✅ DCA bot
- ✅ Risk management

### In Progress

**Feature #2: Dashboard Web Realtime (TradingView style)**
- [ ] FastAPI backend
- [ ] WebSocket price streaming
- [ ] React frontend
- [ ] Real-time charts
- [ ] Market heatmap
- [ ] Watchlist auto-scanner

**Feature #3: P2P Lending + Securities**
- [ ] Collateral management
- [ ] Real-time asset valuation
- [ ] Auto liquidation
- [ ] Smart contract integration

**Feature #4: Market Screener Realtime**
- [ ] Multi-criteria scanner
- [ ] Volume surge detection
- [ ] Price momentum detection
- [ ] Custom filters

**Feature #5: Auto Portfolio Rebalancing**
- [ ] Target allocation tracking
- [ ] Rebalancing suggestions
- [ ] Auto execution

**Feature #6: Alert System**
- [ ] Custom alert rules
- [ ] Multi-channel notifications
- [ ] Discord integration

**Feature #7: Backtest Engine**
- [ ] Historical tick data storage
- [ ] Strategy backtesting
- [ ] Performance metrics
- [ ] Market replay

**Feature #8: AI Trading Assistant**
- [ ] Natural language queries
- [ ] Voice commands
- [ ] Auto trading suggestions

**Feature #9: Advanced Risk Management**
- [ ] Portfolio hedging
- [ ] Margin management
- [ ] Multi-account support

**Feature #10: Machine Learning Signals**
- [ ] LSTM price prediction
- [ ] Breakout prediction
- [ ] Volatility forecasting

## 🧪 Testing

Run tests:
```bash
pytest tests/ -v
```

Run with coverage:
```bash
pytest tests/ --cov=core --cov=utils
```

## 📝 Logging

Logs are stored in `logs/` directory:
- `trading_bot.log`: Main application log
- `error.log`: Error logs only
- `trading.log`: Trade execution audit trail (kept for 365 days)

## ⚠️ Disclaimer

**IMPORTANT:**

This software is for educational and research purposes only.

- Trading stocks involves risk and you can lose money
- Past performance does not guarantee future results
- Always test in paper trading mode first
- Use at your own risk
- Not financial advice

The authors are not responsible for any financial losses incurred from using this software.

## 🤝 Contributing

Contributions are welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- DNSE for providing the API
- Vietnamese trading community
- All contributors

## 📞 Support

For issues and questions:
- GitHub Issues: [Create an issue](https://github.com/yourusername/dnse-insight/issues)
- Email: your.email@example.com

---

**Made with ❤️ for Vietnamese traders**
