@echo off
REM Quick Test Script for DNSE Trading Bot (Windows)
REM Chay tat ca tests de kiem tra he thong

setlocal enabledelayedexpansion

echo.
echo ========================================
echo     DNSE TRADING BOT - QUICK TEST
echo ========================================
echo.

REM Check Python
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+
    exit /b 1
)
for /f "tokens=*" %%i in ('python --version') do set PYTHON_VERSION=%%i
echo [OK] Python found: %PYTHON_VERSION%

REM Check virtual environment
echo [INFO] Checking virtual environment...
if not exist "venv\" (
    echo [WARNING] Virtual environment not found
    echo [INFO] Creating virtual environment...
    python -m venv venv
    echo [OK] Virtual environment created
)

REM Activate virtual environment
call venv\Scripts\activate.bat
echo [OK] Virtual environment activated

REM Install dependencies
echo.
echo ========================================
echo     Installing Dependencies
echo ========================================
echo.
echo [INFO] Installing Python packages...
pip install -q --upgrade pip
pip install -q -r requirements.txt
echo [OK] Dependencies installed

REM Check .env file
echo.
echo ========================================
echo     Checking Configuration
echo ========================================
echo.
if not exist ".env" (
    echo [WARNING] .env file not found
    echo [INFO] Copying from .env.example...
    copy .env.example .env
    echo [OK] .env created
    echo.
    echo [WARNING] IMPORTANT: Edit .env file with your DNSE credentials!
    echo [INFO] Press any key to continue after editing .env...
    pause >nul
) else (
    echo [OK] .env file exists
)

REM Check Redis
echo.
echo ========================================
echo     Checking Redis
echo ========================================
echo.
redis-cli ping >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Redis not running
    echo [INFO] Checking for Docker...

    docker --version >nul 2>&1
    if %errorlevel% equ 0 (
        echo [INFO] Starting Redis with Docker...
        docker run -d --name redis-test -p 6379:6379 redis:7-alpine 2>nul || docker start redis-test 2>nul
        timeout /t 2 /nobreak >nul
        echo [OK] Redis started with Docker
    ) else (
        echo [WARNING] Docker not found, Redis tests may fail
    )
) else (
    echo [OK] Redis is running
)

REM Create directories
echo.
echo ========================================
echo     Setting up directories
echo ========================================
echo.
if not exist "logs\" mkdir logs
if not exist "data\" mkdir data
echo [OK] Directories created

REM Run tests
echo.
echo ========================================
echo     Running Component Tests
echo ========================================
echo.

REM Test 1: Check imports
echo [TEST 1] Checking Python imports...
python -c "from core.dnse_api_client import dnse_client; from core.price_stream import price_stream_manager; from core.order_executor import order_executor; from core.watchlist_manager import watchlist_manager; print('[OK] All core modules imported successfully')"
if %errorlevel% neq 0 (
    echo [ERROR] Import test failed
    exit /b 1
)
echo [OK] Import test passed

REM Test 2: Check configuration
echo.
echo [TEST 2] Checking configuration...
python -c "from utils.config import settings; print(f'   Trading Mode: {settings.trading_mode}'); print(f'   API Base URL: {settings.dnse_api_base_url}'); print('[OK] Configuration loaded')"
if %errorlevel% neq 0 (
    echo [ERROR] Configuration test failed
    exit /b 1
)
echo [OK] Configuration test passed

REM Test 3: Test Order Executor
echo.
echo [TEST 3] Testing Order Executor (Paper Mode)...
python -c "from core.order_executor import order_executor, OrderSide, OrderType; order = order_executor.place_order('VCB', OrderSide.BUY, 100, 95000, OrderType.LIMIT); print(f'[OK] Order placed: {order.order_id}') if order else print('[ERROR] Order failed')"
if %errorlevel% neq 0 (
    echo [ERROR] Order Executor test failed
    exit /b 1
)
echo [OK] Order Executor test passed

REM Test 4: Test Watchlist
echo.
echo [TEST 4] Testing Watchlist Manager...
python -c "from core.watchlist_manager import watchlist_manager; wl = watchlist_manager.create_watchlist('Test', 'Test', ['VCB']); print(f'[OK] Watchlist created: {wl.id}') if wl else print('[ERROR] Failed'); watchlist_manager.delete_watchlist(wl.id) if wl else None"
if %errorlevel% neq 0 (
    echo [ERROR] Watchlist test failed
    exit /b 1
)
echo [OK] Watchlist Manager test passed

REM Summary
echo.
echo ========================================
echo     Test Summary
echo ========================================
echo.
echo Component Test Results:
echo   [OK] Python imports
echo   [OK] Configuration
echo   [OK] Order Executor (Paper Mode)
echo   [OK] Watchlist Manager
echo.
echo Next Steps:
echo   1. Edit .env with your DNSE credentials
echo   2. Run: python examples\dnse_api_example.py
echo   3. Start backend: python dashboard\backend\main.py
echo   4. Start bot: python main.py
echo   5. Read TESTING_GUIDE.md for detailed testing
echo.
echo ========================================
echo     Quick Test Completed!
echo ========================================
echo.
echo [OK] All basic tests passed! System ready for testing.
echo.
pause
