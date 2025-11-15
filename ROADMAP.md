# DNSE Insight - Development Roadmap

This document outlines the 10 major features planned for the DNSE Insight trading system.

## Overview

DNSE Insight is a comprehensive trading system for the Vietnamese stock market, designed to provide:
- Real-time trading automation
- Advanced analytics and visualization
- Risk management
- Portfolio optimization
- Machine learning-powered predictions

## Feature Status

- ✅ Completed
- 🚧 In Progress
- 📋 Planned
- 💡 Future Consideration

---

## ✅ Feature #1: Trading Bot Realtime (VIETNAM - DNSE)

**Status:** ✅ COMPLETED

### Description
Real-time automated trading bot using MQTT for price streaming and REST API for order execution.

### Components
- ✅ **price_stream.py**: MQTT price streaming with auto-reconnect
- ✅ **signal_engine.py**: Technical analysis and signal generation
- ✅ **order_executor.py**: REST API order execution
- ✅ **risk_manager.py**: Risk management with virtual stop-loss

### Features Implemented
- Auto-buy when price breaks resistance
- Auto-sell when price breaks support
- Auto-cutloss on high volatility
- DCA (Dollar Cost Averaging) bot
- Virtual STOP LOSS (Vietnam doesn't have standard stop loss)
- Multiple trading strategies:
  - Breakout strategy
  - Support/Resistance
  - Moving Average crossover
  - RSI overbought/oversold
  - Volume surge detection
  - Bollinger Bands

### Tech Stack
- Python 3.9+
- paho-mqtt for MQTT
- requests/httpx for REST API
- pandas/numpy for data processing
- ta-lib for technical indicators

---

## 📋 Feature #2: Dashboard Web Realtime - TradingView Style

**Status:** 📋 PLANNED

### Description
Real-time web dashboard with TradingView-style charts and market analysis.

### Planned Components

#### Backend (FastAPI)
```
/dashboard
  backend/
    main.py                 # FastAPI application
    websocket_server.py     # WebSocket for real-time updates
    market_data_api.py      # Market data endpoints
    user_api.py             # User management
```

#### Frontend (React)
```
  frontend/
    src/
      components/
        Chart.tsx           # TradingView-style chart
        Heatmap.tsx         # Market heatmap
        Watchlist.tsx       # Personal watchlist
        PriceBoard.tsx      # Personalized price board
      pages/
        Dashboard.tsx
        Portfolio.tsx
        Signals.tsx
```

### Features
- Real-time charts with candlesticks, indicators
- Market heatmap (sectors, market cap, performance)
- Personalized watchlist with auto-scanning
- Custom price boards
- Telegram notifications on breakouts
- Voice commands integration
- Multi-timeframe analysis
- Drawing tools (trend lines, fibonacci, etc.)

### Tech Stack
- **Backend:** FastAPI, WebSocket, Redis
- **Frontend:** React, TypeScript, Chart.js/Lightweight Charts
- **Real-time:** MQTT → WebSocket bridge

### Timeline
- Q1 2024: Backend API development
- Q2 2024: Frontend development
- Q3 2024: Integration and testing

---

## 📋 Feature #3: P2P Lending + Securities (Blockchain MVP)

**Status:** 📋 PLANNED

### Description
P2P lending platform with stock collateral, leveraging blockchain for transparency.

### Architecture
```
/lending
  smart_contracts/
    Vault.sol              # Asset locking
    LendingPool.sol        # Lending logic
    Collateral.sol         # Collateral management
  backend/
    lending_engine.py      # Lending logic
    collateral_manager.py  # Collateral tracking
    liquidation_engine.py  # Auto liquidation
```

### Features
- Loan creation with stock collateral
- Real-time collateral valuation via DNSE API
- Auto liquidation when stock price drops below margin
- Smart contract integration for asset locking
- Interest rate calculation
- Loan-to-Value (LTV) ratio management
- Credit scoring
- Multi-collateral support (stocks + cash)

### Integration with DNSE
- Read portfolio in real-time
- Get asset values live
- Auto liquidation triggers
- Position monitoring

### Tech Stack
- Smart Contracts: Solidity, Hardhat
- Blockchain: Ethereum/Polygon/BSC
- Backend: Python, Web3.py
- Database: PostgreSQL

### Timeline
- Q2 2024: Smart contract development
- Q3 2024: Backend integration
- Q4 2024: Testing and launch

---

## 📋 Feature #4: Custom Market Screener Realtime

**Status:** 📋 PLANNED

### Description
Real-time market scanner to detect trading opportunities across all Vietnamese stocks.

### Architecture
```
/screener
  core/
    scanner_engine.py      # Main scanning logic
    filters.py             # Custom filters
    alerting.py            # Alert system
  filters/
    volume_surge.py        # Volume detection
    price_momentum.py      # Momentum detection
    breakout.py            # Breakout detection
    unusual_activity.py    # Unusual patterns
```

### Filters
1. **Volume Surge**: Detect abnormal volume spikes
2. **Price Momentum**: High % changes
3. **Breakout Detection**: Price breaking resistance/support
4. **Supply-Demand Imbalance**: Large bid/ask gaps
5. **Money Flow**: F0 flow indicator (FAKE-FLOW)
6. **Gap Detection**: Opening gaps
7. **New Highs/Lows**: 52-week highs/lows
8. **Moving Average Crosses**: Various MA combinations

### Output Formats
- Excel export
- Web UI dashboard
- Telegram bot notifications
- Email alerts
- Discord webhooks

### Tech Stack
- Python for screening engine
- Redis for real-time data caching
- Celery for distributed scanning
- React for UI

### Timeline
- Q3 2024: Core engine development
- Q4 2024: UI and integrations

---

## 📋 Feature #5: Auto Portfolio Rebalancing

**Status:** 📋 PLANNED

### Description
Automatic portfolio rebalancing to maintain target asset allocation.

### Features
- Fetch current portfolio via REST API
- Get real-time prices via MQTT
- Calculate current allocation vs target
- Generate rebalancing recommendations
- Auto-execute rebalancing trades
- Alerts on allocation drift (5%, 10%, etc.)
- Tax-loss harvesting
- Threshold-based rebalancing

### Example Flow
```python
# Target allocation
target = {
    "VCB": 0.30,  # 30%
    "VHM": 0.25,  # 25%
    "VIC": 0.20,  # 20%
    "FPT": 0.15,  # 15%
    "Cash": 0.10  # 10%
}

# Current portfolio
current = get_portfolio()

# Calculate drift
drift = calculate_drift(current, target)

# Suggest rebalancing
if drift > 0.05:
    suggestions = generate_rebalancing_orders(current, target)
    execute_orders(suggestions)
```

### Timeline
- Q4 2024: Development and testing

---

## 📋 Feature #6: Real-time Alert System

**Status:** 📋 PLANNED

### Description
Comprehensive alerting system for various market events.

### Alert Types
1. **Price Alerts**
   - Price crosses threshold
   - Price crosses moving average
   - Price reaches support/resistance

2. **Technical Indicators**
   - RSI overbought/oversold
   - MACD crossover
   - Bollinger Band breach

3. **Volume Alerts**
   - Volume surge (2x, 3x, 5x average)
   - Volume drying up

4. **Order Alerts**
   - Order filled
   - Order cancelled
   - Order rejected

5. **Portfolio Alerts**
   - Daily P&L threshold
   - Position limit reached
   - Margin call

### Delivery Channels
- Telegram
- Discord
- Email
- SMS (via Twilio)
- Push notifications
- Webhook

### Timeline
- Q1 2025: Core development

---

## 📋 Feature #7: Backtest Engine with Self-recorded Data

**Status:** 📋 PLANNED

### Description
Professional backtesting engine using self-recorded tick data.

### Architecture
```
/backtest
  data/
    tick_recorder.py       # Record tick data from MQTT
    data_storage.py        # Store in database
  engine/
    backtest_engine.py     # Main backtesting logic
    strategy_base.py       # Strategy interface
    performance.py         # Performance metrics
  strategies/
    breakout_strategy.py
    mean_reversion.py
    ml_strategy.py
```

### Features
- Record tick-by-tick data from MQTT
- Replay market conditions
- Test trading strategies
- Performance metrics:
  - Sharpe ratio
  - Max drawdown
  - Win rate
  - Profit factor
  - Risk/Reward ratio
- Strategy optimization
- Parameter tuning
- Walk-forward analysis
- Monte Carlo simulation

### Tech Stack
- TimescaleDB for time-series data
- Pandas for data manipulation
- Backtrader/Zipline for backtesting framework

### Timeline
- Q2 2025: Data collection infrastructure
- Q3 2025: Backtesting engine

---

## 📋 Feature #8: Personal AI Trading Assistant

**Status:** 📋 PLANNED

### Description
AI-powered trading assistant with natural language interface and voice commands.

### Capabilities
- **Natural Language Queries:**
  - "What's the current price of VCB?"
  - "Show me my portfolio performance today"
  - "Which stocks broke out today?"

- **Trading Commands:**
  - "Buy 100 VCB at market price"
  - "Sell 30% of my VHM position"
  - "Set stop loss for VIC at 45.5"

- **Analysis:**
  - "Analyze VCB for me"
  - "What's the sentiment on banking stocks?"
  - "Find stocks with RSI < 30"

- **Voice Integration:**
  - Voice commands for placing orders
  - Voice authentication (using existing voice auth for bank)
  - Text-to-speech for alerts

### Tech Stack
- OpenAI GPT-4 / Claude for NLP
- Whisper for speech-to-text
- ElevenLabs for text-to-speech
- LangChain for agent framework

### Timeline
- Q3 2025: Development
- Q4 2025: Testing and refinement

---

## 📋 Feature #9: Advanced Risk Management System (Binance-style)

**Status:** 📋 PLANNED

### Description
Professional-grade risk management similar to Binance's margin system.

### Features
1. **Margin Management**
   - Real-time margin calculation
   - Maintenance margin monitoring
   - Auto margin calls

2. **Position Management**
   - Auto position closure on high risk
   - Cross-margin vs isolated margin
   - Leverage control

3. **Portfolio Risk**
   - Value at Risk (VaR)
   - Portfolio beta
   - Correlation analysis
   - Stress testing

4. **Hedging**
   - Auto hedge suggestions
   - Derivative hedging (if available)
   - Cross-market hedging

5. **Risk Limits**
   - Daily loss limits
   - Position size limits
   - Sector exposure limits

### Dashboard
- Real-time risk metrics
- Risk heatmap
- Margin utilization gauge
- Liquidation price calculator

### Timeline
- Q4 2025: Development

---

## 📋 Feature #10: Machine Learning Signal Engine

**Status:** 📋 PLANNED

### Description
ML-powered prediction models for price movements, volatility, and breakouts.

### Models

#### 1. LSTM Price Prediction
```python
# Predict next 5 candles
model = LSTM_Price_Predictor(
    sequence_length=60,
    features=['close', 'volume', 'rsi', 'macd']
)
prediction = model.predict(symbol='VCB', horizon=5)
```

#### 2. GRU Volatility Prediction
```python
# Predict volatility
volatility_model = GRU_Volatility_Predictor()
vol_forecast = volatility_model.predict(symbol='VCB')
```

#### 3. Random Forest Breakout Detection
```python
# Detect breakout probability
breakout_model = RandomForestBreakout()
probability = breakout_model.predict_breakout('VCB')
```

#### 4. XGBoost Direction Classifier
```python
# Classify: UP, DOWN, SIDEWAYS
direction_model = XGBoostDirectionClassifier()
direction = direction_model.predict('VCB')  # Returns: UP/DOWN/SIDEWAYS
```

### Features
- Real-time data collection
- Feature engineering
- Model training pipeline
- Backtesting ML strategies
- Model performance tracking
- A/B testing of models
- Ensemble methods

### Data Requirements
- Minimum 2 years of tick data
- Real-time feature calculation
- Data quality monitoring

### Tech Stack
- TensorFlow/PyTorch for deep learning
- Scikit-learn for classical ML
- XGBoost/LightGBM for gradient boosting
- MLflow for model tracking
- Airflow for pipeline orchestration

### Timeline
- Q1 2026: Data collection
- Q2 2026: Model development
- Q3 2026: Integration with trading bot
- Q4 2026: Live testing

---

## Infrastructure Requirements

### For All Features

#### Data Infrastructure
- TimescaleDB for time-series data
- PostgreSQL for relational data
- Redis for caching
- InfluxDB for metrics

#### Message Queue
- RabbitMQ or Kafka for event streaming
- Celery for task queue

#### Monitoring
- Prometheus for metrics
- Grafana for visualization
- ELK stack for logging

#### Deployment
- Docker for containerization
- Kubernetes for orchestration
- CI/CD with GitHub Actions

---

## Milestones

### 2024 Q1
- ✅ Feature #1 complete
- Start Feature #2 (Dashboard)

### 2024 Q2
- Complete Feature #2
- Start Feature #3 (P2P Lending)

### 2024 Q3
- Complete Feature #3
- Start Feature #4 (Market Screener)

### 2024 Q4
- Complete Feature #4
- Start Feature #5 (Portfolio Rebalancing)

### 2025
- Features #5-#9

### 2026
- Feature #10 (ML Engine)
- System optimization
- Production hardening

---

## Success Metrics

### Technical
- System uptime: 99.9%
- MQTT latency: < 100ms
- Order execution: < 500ms
- API response time: < 200ms

### Trading
- Win rate: > 55%
- Sharpe ratio: > 1.5
- Max drawdown: < 15%
- Profit factor: > 2.0

### User
- User satisfaction: > 4.5/5
- Daily active users: 1000+
- Trading volume: 1B+ VND/day

---

## Contributing

We welcome contributions to any of these features! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## Questions?

Open an issue or discussion on GitHub.
