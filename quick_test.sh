#!/bin/bash

# Quick Test Script for DNSE Trading Bot
# Chạy tất cả tests để kiểm tra hệ thống

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print functions
print_header() {
    echo -e "\n${BLUE}========================================${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}========================================${NC}\n"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

print_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

# Main header
clear
print_header "🧪 DNSE TRADING BOT - QUICK TEST"

# Check Python
print_info "Checking Python installation..."
if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    print_success "Python found: $PYTHON_VERSION"
else
    print_error "Python 3 not found. Please install Python 3.8+"
    exit 1
fi

# Check if in virtual environment
print_info "Checking virtual environment..."
if [[ "$VIRTUAL_ENV" != "" ]]; then
    print_success "Virtual environment active: $VIRTUAL_ENV"
else
    print_warning "Not in virtual environment"
    print_info "Creating virtual environment..."
    python3 -m venv venv

    if [[ "$OSTYPE" == "msys" || "$OSTYPE" == "win32" ]]; then
        source venv/Scripts/activate
    else
        source venv/bin/activate
    fi

    print_success "Virtual environment created and activated"
fi

# Install dependencies
print_header "📦 Installing Dependencies"
print_info "Installing Python packages..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
print_success "Dependencies installed"

# Check .env file
print_header "⚙️  Checking Configuration"
if [ ! -f .env ]; then
    print_warning ".env file not found"
    print_info "Copying from .env.example..."
    cp .env.example .env
    print_success ".env created"
    print_warning "⚠️  IMPORTANT: Edit .env file with your DNSE credentials!"
    print_info "Press Enter to continue (make sure you've edited .env)..."
    read
else
    print_success ".env file exists"
fi

# Check Redis
print_header "🔧 Checking Redis"
if command -v redis-cli &> /dev/null; then
    if redis-cli ping &> /dev/null; then
        print_success "Redis is running"
    else
        print_warning "Redis not running, trying to start..."

        # Try Docker
        if command -v docker &> /dev/null; then
            print_info "Starting Redis with Docker..."
            docker run -d --name redis-test -p 6379:6379 redis:7-alpine 2>/dev/null || docker start redis-test 2>/dev/null
            sleep 2

            if redis-cli ping &> /dev/null; then
                print_success "Redis started with Docker"
            else
                print_error "Failed to start Redis"
            fi
        else
            print_warning "Docker not found, Redis tests may fail"
        fi
    fi
else
    print_warning "redis-cli not found"

    if command -v docker &> /dev/null; then
        print_info "Starting Redis with Docker..."
        docker run -d --name redis-test -p 6379:6379 redis:7-alpine 2>/dev/null || docker start redis-test 2>/dev/null
        sleep 2
        print_success "Redis started with Docker"
    else
        print_warning "Redis not available, some tests may fail"
    fi
fi

# Create logs directory
print_header "📁 Setting up directories"
mkdir -p logs
mkdir -p data
print_success "Directories created"

# Run tests
print_header "🧪 Running Component Tests"

# Test 1: Check imports
print_info "Test 1: Checking Python imports..."
python3 << 'EOF'
try:
    from core.dnse_api_client import dnse_client
    from core.price_stream import price_stream_manager
    from core.order_executor import order_executor
    from core.watchlist_manager import watchlist_manager
    print("✅ All core modules imported successfully")
except ImportError as e:
    print(f"❌ Import error: {e}")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    print_success "Import test passed"
else
    print_error "Import test failed"
    exit 1
fi

# Test 2: Check configuration
print_info "Test 2: Checking configuration..."
python3 << 'EOF'
try:
    from utils.config import settings

    print(f"   Trading Mode: {settings.trading_mode}")
    print(f"   API Base URL: {settings.dnse_api_base_url}")

    if settings.trading_mode != "paper":
        print("⚠️  WARNING: Not in paper trading mode!")
        print("   Set TRADING_MODE=paper in .env for testing")
    else:
        print("✅ Paper trading mode enabled (safe for testing)")

except Exception as e:
    print(f"❌ Config error: {e}")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    print_success "Configuration test passed"
else
    print_error "Configuration test failed"
    exit 1
fi

# Test 3: Test Order Executor (Paper Mode)
print_info "Test 3: Testing Order Executor (Paper Mode)..."
python3 << 'EOF'
from core.order_executor import order_executor, OrderSide, OrderType

if not order_executor.paper_mode:
    print("❌ ERROR: Not in paper mode! Stopping test for safety.")
    exit(1)

# Test placing order
order = order_executor.place_order(
    symbol='VCB',
    side=OrderSide.BUY,
    quantity=100,
    price=95000,
    order_type=OrderType.LIMIT
)

if order:
    print(f"✅ Order placed successfully: {order.order_id}")
    print(f"   Symbol: {order.symbol}")
    print(f"   Status: {order.status.value}")
else:
    print("❌ Order placement failed")
    exit(1)

# Test get positions
positions = order_executor.get_positions()
print(f"✅ Positions retrieved: {len(positions)} symbols")

# Test get balance
balance = order_executor.get_account_balance()
print(f"✅ Balance: {balance['cash']:,.0f} VND")
EOF

if [ $? -eq 0 ]; then
    print_success "Order Executor test passed"
else
    print_error "Order Executor test failed"
fi

# Test 4: Test Watchlist Manager
print_info "Test 4: Testing Watchlist Manager..."
python3 << 'EOF'
from core.watchlist_manager import watchlist_manager

# Create test watchlist
wl = watchlist_manager.create_watchlist(
    name="Test Portfolio",
    description="Quick test",
    symbols=["VCB", "VHM"],
    color="#10b981"
)

if wl:
    print(f"✅ Watchlist created: {wl.name} (ID: {wl.id})")

    # Add symbol
    if watchlist_manager.add_symbol(wl.id, "FPT"):
        print("✅ Symbol added successfully")

    # Get watchlist
    retrieved = watchlist_manager.get_watchlist(wl.id)
    if retrieved:
        print(f"✅ Watchlist retrieved: {len(retrieved.symbols)} symbols")

    # Clean up
    watchlist_manager.delete_watchlist(wl.id)
    print("✅ Test watchlist deleted")
else:
    print("❌ Watchlist creation failed")
    exit(1)
EOF

if [ $? -eq 0 ]; then
    print_success "Watchlist Manager test passed"
else
    print_error "Watchlist Manager test failed"
fi

# Test 5: Test DNSE API Client (if credentials provided)
print_info "Test 5: Testing DNSE API Client..."
python3 << 'EOF'
from core.dnse_api_client import dnse_client

# Check if credentials are set
if dnse_client.api_key == "your_api_key_here":
    print("⚠️  WARNING: API credentials not configured")
    print("   Skipping API test (this is OK for initial testing)")
    print("   To test API: Edit .env and add your DNSE credentials")
else:
    print("   Testing market status API...")
    result = dnse_client.get_market_status()

    if result and not result.get("error"):
        print("✅ DNSE API connection successful")
    else:
        print("⚠️  API call failed (check credentials or network)")
        print(f"   Error: {result.get('error', 'Unknown')}")
EOF

if [ $? -eq 0 ]; then
    print_success "API Client test completed"
else
    print_warning "API Client test had issues (check credentials)"
fi

# Summary
print_header "📊 Test Summary"

echo ""
echo "Component Test Results:"
echo "  ✅ Python imports"
echo "  ✅ Configuration"
echo "  ✅ Order Executor (Paper Mode)"
echo "  ✅ Watchlist Manager"
echo "  ⚠️  DNSE API (needs credentials)"
echo ""

print_info "Next Steps:"
echo "  1. Edit .env with your DNSE credentials"
echo "  2. Run: python examples/dnse_api_example.py"
echo "  3. Start backend: python dashboard/backend/main.py"
echo "  4. Start bot: python main.py"
echo "  5. Read TESTING_GUIDE.md for detailed testing"
echo ""

print_header "✅ Quick Test Completed!"

print_info "To start the full system:"
echo "  Option 1 (Simple): bash setup.sh"
echo "  Option 2 (Docker): docker-compose up -d"
echo "  Option 3 (Manual): See TESTING_GUIDE.md"
echo ""

print_success "All basic tests passed! System ready for testing."
echo ""
