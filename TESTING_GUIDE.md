# 🧪 Hướng dẫn Test & Chạy thử hệ thống

## Mục lục
- [Setup môi trường](#setup-môi-trường)
- [Test từng component](#test-từng-component)
- [Chạy toàn bộ hệ thống](#chạy-toàn-bộ-hệ-thống)
- [Troubleshooting](#troubleshooting)

---

## 📋 Setup môi trường

### Bước 1: Cài đặt dependencies

```bash
# Tạo virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
# hoặc: venv\Scripts\activate  # Windows

# Cài đặt packages
pip install -r requirements.txt
```

### Bước 2: Cấu hình môi trường

```bash
# Copy file config
cp .env.example .env

# Chỉnh sửa .env với editor
nano .env
```

**Cấu hình tối thiểu cho TEST (Paper Trading):**

```bash
# ========================================
# QUAN TRỌNG: Cấu hình này cho PAPER TRADING
# ========================================

# DNSE API - Điền thông tin thật để test API
DNSE_API_BASE_URL=https://api.dnse.com.vn
DNSE_API_KEY=your_api_key_here          # Lấy từ DNSE
DNSE_API_SECRET=your_api_secret_here    # Lấy từ DNSE
DNSE_ACCOUNT_ID=your_account_id_here    # Mã tài khoản

# MQTT - Điền thông tin thật để test streaming
MQTT_BROKER=mqtt.dnse.com.vn
MQTT_PORT=1883
MQTT_USERNAME=your_mqtt_username
MQTT_PASSWORD=your_mqtt_password
MQTT_CLIENT_ID=dnse_test_bot

# TRADING MODE - BẮT BUỘC PHẢI ĐỂ PAPER ĐỂ TEST
TRADING_MODE=paper  # ⚠️ KHÔNG ĐỔI SANG LIVE KHI TEST!

# Redis (dùng localhost cho test)
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=0

# Database (SQLite cho test local)
DATABASE_URL=sqlite:///./dnse_trading_test.db

# Telegram (optional - có thể bỏ qua khi test)
TELEGRAM_BOT_TOKEN=
TELEGRAM_CHAT_ID=
TELEGRAM_ENABLED=false

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/trading_bot_test.log
```

### Bước 3: Khởi động Redis (cần cho cache)

**Option 1: Dùng Docker (khuyến nghị)**
```bash
docker run -d --name redis-test -p 6379:6379 redis:7-alpine
```

**Option 2: Cài đặt Redis local**
```bash
# Ubuntu/Debian
sudo apt-get install redis-server
sudo systemctl start redis

# macOS
brew install redis
brew services start redis

# Windows
# Download từ https://github.com/microsoftarchive/redis/releases
```

**Kiểm tra Redis:**
```bash
redis-cli ping
# Phải trả về: PONG
```

---

## 🧪 Test từng component

### Test 1: Kiểm tra DNSE API Connection

```bash
python examples/dnse_api_example.py
```

**Kết quả mong đợi:**
```
✅ Connected to DNSE API
✅ Market Data APIs working
✅ Account APIs working
✅ Trading APIs working (Paper Mode)
```

**Nếu lỗi:**
- Kiểm tra API credentials trong `.env`
- Kiểm tra network/firewall
- Kiểm tra API key còn hạn sử dụng

### Test 2: Test MQTT Streaming

```bash
python -c "
from core.price_stream import price_stream_manager

# Connect
if price_stream_manager.start():
    print('✅ MQTT connected')

    # Subscribe
    price_stream_manager.subscribe(['VCB', 'VHM'])
    print('✅ Subscribed to symbols')

    # Wait for data
    import time
    time.sleep(5)

    # Check latest price
    vcb = price_stream_manager.get_latest_price('VCB')
    if vcb:
        print(f'✅ Received VCB price: {vcb.price:,.0f}')
    else:
        print('⚠️ No price data received')

    price_stream_manager.stop()
else:
    print('❌ MQTT connection failed')
"
```

### Test 3: Test Order Execution (Paper Mode)

```bash
python -c "
from core.order_executor import order_executor, OrderSide, OrderType

# Kiểm tra paper mode
if order_executor.paper_mode:
    print('✅ Paper trading mode enabled')

    # Test đặt lệnh
    order = order_executor.place_order(
        symbol='VCB',
        side=OrderSide.BUY,
        quantity=100,
        price=95000,
        order_type=OrderType.LIMIT
    )

    if order:
        print(f'✅ Order placed: {order.order_id}')
        print(f'   Status: {order.status.value}')
        print(f'   Symbol: {order.symbol}')
    else:
        print('❌ Order placement failed')

    # Kiểm tra positions
    positions = order_executor.get_positions()
    print(f'✅ Positions: {positions}')

    # Kiểm tra balance
    balance = order_executor.get_account_balance()
    print(f'✅ Cash: {balance[\"cash\"]:,.0f} VND')
else:
    print('❌ Not in paper mode! Dangerous!')
"
```

### Test 4: Test Trading Bot

```bash
python -c "
from core.trading_bot import TradingBot

bot = TradingBot()

# Test khởi động
if bot.start():
    print('✅ Trading bot started')

    # Chạy 1 iteration
    import time
    time.sleep(3)

    # Dừng bot
    bot.stop()
    print('✅ Trading bot stopped')
else:
    print('❌ Failed to start bot')
"
```

### Test 5: Test Watchlist Manager

```bash
python examples/watchlist_example.py
```

**Kết quả mong đợi:**
```
✅ Created watchlist: My Portfolio
✅ Added symbols: VCB, VHM, FPT
✅ Exported to CSV
✅ Imported from JSON
```

### Test 6: Test Market Screener

```bash
python examples/screener_example.py
```

### Test 7: Test Dashboard API

```bash
# Start backend
python dashboard/backend/main.py &

# Wait for startup
sleep 3

# Test API endpoint
curl http://localhost:8000/health

# Nên trả về: {"status":"healthy"}

# Test watchlist API
curl http://localhost:8000/api/v1/watchlists/

# Stop backend
pkill -f "dashboard/backend/main.py"
```

---

## 🚀 Chạy toàn bộ hệ thống

### Option 1: Chạy từng service riêng (Debugging)

**Terminal 1: Start Redis**
```bash
docker run -d --name redis-test -p 6379:6379 redis:7-alpine
```

**Terminal 2: Start Backend API**
```bash
# Activate venv nếu chưa
source venv/bin/activate

# Start backend
python dashboard/backend/main.py

# Log sẽ hiển thị:
# INFO: Started server process
# INFO: Uvicorn running on http://0.0.0.0:8000
```

**Terminal 3: Start Trading Bot**
```bash
source venv/bin/activate
python main.py

# Hoặc chạy tất cả features:
python run_all_features.py
```

**Terminal 4: Start Frontend (nếu có)**
```bash
cd dashboard/frontend
npm install
npm run dev

# Frontend sẽ chạy ở: http://localhost:3000
```

**Terminal 5: Test API**
```bash
# Health check
curl http://localhost:8000/health

# Get watchlists
curl http://localhost:8000/api/v1/watchlists/

# Get stock price
curl http://localhost:8000/api/v1/market/price/VCB
```

### Option 2: Chạy với Docker Compose (Production-like)

**Bước 1: Build images**
```bash
# Build tất cả services
docker-compose build

# Hoặc build từng service
docker-compose build backend
docker-compose build frontend
```

**Bước 2: Start services**
```bash
# Start tất cả (background mode)
docker-compose up -d

# Xem logs
docker-compose logs -f

# Xem logs của 1 service
docker-compose logs -f backend
docker-compose logs -f redis
```

**Bước 3: Kiểm tra services**
```bash
# Check status
docker-compose ps

# Expected output:
# NAME                 SERVICE    STATUS    PORTS
# redis                redis      running   0.0.0.0:6379->6379/tcp
# postgres             postgres   running   0.0.0.0:5432->5432/tcp
# backend              backend    running   0.0.0.0:8000->8000/tcp
# frontend             frontend   running   0.0.0.0:3000->3000/tcp
# grafana              grafana    running   0.0.0.0:3001->3000/tcp
# prometheus           prometheus running   0.0.0.0:9090->9090/tcp

# Test endpoints
curl http://localhost:8000/health      # Backend
curl http://localhost:3000             # Frontend
curl http://localhost:3001             # Grafana
curl http://localhost:9090             # Prometheus
```

**Bước 4: Stop services**
```bash
# Stop tất cả
docker-compose down

# Stop và xóa volumes (reset data)
docker-compose down -v
```

### Option 3: Quick Start Script (Khuyến nghị cho beginners)

```bash
# Chạy script tự động
bash setup.sh

# Script sẽ:
# 1. Kiểm tra dependencies
# 2. Cài đặt packages
# 3. Setup .env nếu chưa có
# 4. Start Redis
# 5. Start backend
# 6. Chạy tests
```

---

## 🎯 Test scenarios thực tế

### Scenario 1: Test Auto Trading Bot

```bash
# 1. Start bot với config test
python -c "
from core.trading_bot import TradingBot
from loguru import logger

bot = TradingBot()
bot.config['symbols'] = ['VCB', 'VHM']  # Test với 2 mã
bot.config['max_positions'] = 2
bot.config['check_interval'] = 5  # Check mỗi 5 giây

logger.info('Starting test trading bot...')
bot.start()

# Chạy 30 giây
import time
time.sleep(30)

bot.stop()
logger.info('Test completed')
"
```

### Scenario 2: Test DCA Bot

```bash
python -c "
from core.trading_bot import TradingBot

# Setup DCA
import os
os.environ['DCA_ENABLED'] = 'true'
os.environ['DCA_SYMBOLS'] = 'VCB,VHM'
os.environ['DCA_AMOUNT_PER_ORDER'] = '10000000'
os.environ['DCA_INTERVAL_HOURS'] = '0.1'  # 6 minutes for testing

bot = TradingBot()
bot.start()

# Chạy 10 phút
import time
time.sleep(600)

bot.stop()
"
```

### Scenario 3: Test Market Screener

```bash
python -c "
from screener.core.scanner_engine import ScannerEngine
from screener.filters.breakout import BreakoutFilter

scanner = ScannerEngine()
scanner.add_filter(BreakoutFilter())

# Scan VN30
symbols = ['VCB', 'VHM', 'VIC', 'FPT', 'HPG', 'VNM', 'GAS', 'MSN', 'TCB', 'VPB']
results = scanner.scan(symbols)

print(f'Found {len(results)} opportunities:')
for r in results:
    print(f'  {r[\"symbol\"]}: {r[\"reason\"]}')
"
```

### Scenario 4: Test Backtest Engine

```bash
python examples/backtest_example.py
```

### Scenario 5: Test Alert System

```bash
python -c "
from alerts.alert_system import AlertSystem

alert_system = AlertSystem()

# Tạo alert
alert = alert_system.create_price_alert(
    symbol='VCB',
    target_price=95000,
    condition='above'
)

print(f'Alert created: {alert.id}')

# Start monitoring
alert_system.start()

import time
time.sleep(10)

alert_system.stop()
"
```

---

## 📊 Dashboard Testing

### Test với Web Browser

1. **Start backend + frontend:**
```bash
# Terminal 1: Backend
python dashboard/backend/main.py

# Terminal 2: Frontend
cd dashboard/frontend && npm run dev
```

2. **Mở browser:**
```
http://localhost:3000
```

3. **Test các tính năng:**
- ✅ Dashboard hiển thị đúng
- ✅ Watchlist CRUD operations
- ✅ Real-time price updates
- ✅ Trading chart
- ✅ Market heatmap
- ✅ Portfolio view

### Test API với Postman/Insomnia

**Import collection này:**

```json
{
  "name": "DNSE Trading Bot API",
  "requests": [
    {
      "name": "Health Check",
      "method": "GET",
      "url": "http://localhost:8000/health"
    },
    {
      "name": "Get Watchlists",
      "method": "GET",
      "url": "http://localhost:8000/api/v1/watchlists/"
    },
    {
      "name": "Create Watchlist",
      "method": "POST",
      "url": "http://localhost:8000/api/v1/watchlists/",
      "body": {
        "name": "Test Portfolio",
        "description": "Test watchlist",
        "symbols": ["VCB", "VHM"],
        "color": "#3b82f6"
      }
    },
    {
      "name": "Get Stock Price",
      "method": "GET",
      "url": "http://localhost:8000/api/v1/market/price/VCB"
    },
    {
      "name": "Place Order",
      "method": "POST",
      "url": "http://localhost:8000/api/v1/orders",
      "body": {
        "symbol": "VCB",
        "side": "BUY",
        "quantity": 100,
        "price": 95000,
        "order_type": "LO"
      }
    }
  ]
}
```

---

## 🔍 Monitoring & Debugging

### Xem logs

```bash
# Logs của trading bot
tail -f logs/trading_bot.log

# Logs của backend
tail -f logs/backend.log

# Docker logs
docker-compose logs -f backend
docker-compose logs -f trading-bot
```

### Kiểm tra Redis cache

```bash
# Connect to Redis CLI
redis-cli

# Xem tất cả keys
KEYS *

# Xem 1 key cụ thể
GET dnse:stock_price:VCB

# Xóa cache (nếu cần test lại)
FLUSHDB
```

### Monitoring với Prometheus/Grafana

```bash
# Start monitoring stack
docker-compose up -d prometheus grafana

# Access Grafana
open http://localhost:3001
# Login: admin/admin

# Access Prometheus
open http://localhost:9090
```

### Performance Testing

```bash
# Test API performance
ab -n 1000 -c 10 http://localhost:8000/health

# Test concurrent orders (paper mode)
python -c "
import concurrent.futures
from core.order_executor import order_executor, OrderSide, OrderType

def place_test_order(i):
    return order_executor.place_order('VCB', OrderSide.BUY, 100, 95000)

with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
    results = list(executor.map(place_test_order, range(100)))

print(f'Placed {len([r for r in results if r])} orders successfully')
"
```

---

## ⚠️ Troubleshooting

### Lỗi: Redis connection refused

```bash
# Check Redis running
docker ps | grep redis

# Nếu không chạy
docker run -d --name redis-test -p 6379:6379 redis:7-alpine

# Test connection
redis-cli ping
```

### Lỗi: DNSE API authentication failed

```bash
# Kiểm tra credentials
cat .env | grep DNSE

# Test API key
python -c "
from core.dnse_api_client import dnse_client
print('API Key:', dnse_client.api_key[:10] + '...')
print('Account ID:', dnse_client.account_id)

# Test connection
result = dnse_client.get_market_status()
print('Connection:', 'OK' if result.get('success') else 'FAILED')
"
```

### Lỗi: MQTT connection timeout

```bash
# Test MQTT broker
python -c "
import paho.mqtt.client as mqtt

def on_connect(client, userdata, flags, rc):
    print(f'Connected with code: {rc}')
    if rc == 0:
        print('✅ MQTT connection OK')
    else:
        print('❌ MQTT connection failed')

client = mqtt.Client()
client.on_connect = on_connect
client.connect('mqtt.dnse.com.vn', 1883, 60)
client.loop_start()

import time
time.sleep(3)
client.loop_stop()
"
```

### Lỗi: Port already in use

```bash
# Tìm process đang dùng port 8000
lsof -i :8000
# hoặc: netstat -ano | findstr :8000  (Windows)

# Kill process
kill -9 <PID>

# Hoặc đổi port trong .env
echo "BACKEND_PORT=8001" >> .env
```

### Lỗi: Module not found

```bash
# Reinstall dependencies
pip install -r requirements.txt --force-reinstall

# Hoặc cài từng package lỗi
pip install <package-name>
```

### Lỗi: Database locked (SQLite)

```bash
# Xóa database cũ
rm dnse_trading_test.db

# Hoặc chuyển sang PostgreSQL
docker run -d -p 5432:5432 -e POSTGRES_PASSWORD=postgres postgres:15

# Update .env
DATABASE_URL=postgresql://postgres:postgres@localhost/dnse_trading
```

---

## ✅ Checklist trước khi Deploy

- [ ] Tất cả tests pass
- [ ] Redis hoạt động bình thường
- [ ] DNSE API credentials hợp lệ
- [ ] MQTT streaming hoạt động
- [ ] Paper trading mode hoạt động tốt
- [ ] Dashboard accessible
- [ ] Logs không có critical errors
- [ ] Monitoring setup (Prometheus/Grafana)
- [ ] Backup strategy prepared
- [ ] .env có đầy đủ config production
- [ ] Security: API keys, passwords secure
- [ ] Resource limits configured (Docker)

---

## 🚀 Next Steps: Deploy lên Server

Sau khi test xong local, xem file **DEPLOYMENT.md** để deploy lên server:

```bash
# Preview deployment guide
cat DEPLOYMENT.md

# Hoặc deploy ngay với Docker
docker-compose -f docker-compose.production.yml up -d
```

---

## 📚 Tài liệu liên quan

- `DNSE_API_INTEGRATION.md` - Chi tiết API integration
- `DEPLOYMENT.md` - Hướng dẫn deploy production
- `WATCHLIST_GUIDE.md` - Watchlist management
- `README.md` - Tổng quan hệ thống
- `CONTRIBUTING.md` - Development guide

---

## 💡 Tips

1. **Luôn test với Paper Mode trước** - An toàn nhất
2. **Check logs thường xuyên** - Phát hiện lỗi sớm
3. **Monitor Redis cache** - Đảm bảo performance tốt
4. **Test từng component riêng** - Dễ debug hơn
5. **Dùng Docker Compose** - Gần với production nhất
6. **Setup monitoring** - Biết được system health
7. **Backup data trước khi test** - Phòng trường hợp xóa nhầm

---

**Happy Testing! 🎉**
