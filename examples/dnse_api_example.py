#!/usr/bin/env python3
"""
DNSE API Integration Example
Demonstrates all DNSE API features
"""
import asyncio
from loguru import logger
from core.dnse_api_client import dnse_client
from core.price_stream import price_stream_manager, PriceData
from core.order_executor import order_executor, OrderSide, OrderType


def demo_market_data():
    """Demonstrate market data APIs"""
    print("\n" + "="*60)
    print("1. MARKET DATA APIs")
    print("="*60)

    # Get stock price
    print("\n📊 Get Stock Price (VCB):")
    price_data = dnse_client.get_stock_price("VCB")
    print(f"   Response: {price_data}")

    # Get orderbook
    print("\n📖 Get Orderbook (VCB):")
    orderbook = dnse_client.get_orderbook("VCB")
    print(f"   Response: {orderbook}")

    # Get stock info
    print("\n📋 Get Stock Info (VCB):")
    info = dnse_client.get_stock_info("VCB")
    print(f"   Response: {info}")

    # Get market status
    print("\n⏰ Get Market Status:")
    status = dnse_client.get_market_status()
    print(f"   Response: {status}")

    # Get market index
    print("\n📈 Get Market Index (VNINDEX):")
    vnindex = dnse_client.get_market_index("VNINDEX")
    print(f"   Response: {vnindex}")

    print("\n📈 Get VN30 Index:")
    vn30 = dnse_client.get_market_index("VN30")
    print(f"   Response: {vn30}")


def demo_account_apis():
    """Demonstrate account APIs"""
    print("\n" + "="*60)
    print("2. ACCOUNT APIs")
    print("="*60)

    # Get account balance
    print("\n💰 Get Account Balance:")
    balance = dnse_client.get_account_balance()
    print(f"   Response: {balance}")

    # Get portfolio
    print("\n📊 Get Portfolio:")
    portfolio = dnse_client.get_portfolio()
    print(f"   Response: {portfolio}")

    # Get asset information
    print("\n💼 Get Asset Information:")
    assets = dnse_client.get_asset_information()
    print(f"   Response: {assets}")


def demo_trading_apis():
    """Demonstrate trading APIs"""
    print("\n" + "="*60)
    print("3. TRADING APIs (Using Order Executor)")
    print("="*60)

    # Place limit order
    print("\n📝 Place Limit Order (BUY 100 VCB @ 95,000):")
    order = order_executor.place_order(
        symbol="VCB",
        side=OrderSide.BUY,
        quantity=100,
        price=95000,
        order_type=OrderType.LIMIT
    )
    if order:
        print(f"   ✅ Order placed: {order}")
        print(f"   Order ID: {order.order_id}")
        print(f"   Status: {order.status.value}")

        # Get order status
        print(f"\n🔍 Get Order Status ({order.order_id}):")
        updated_order = order_executor.get_order_status(order.order_id)
        if updated_order:
            print(f"   Status: {updated_order.status.value}")
            print(f"   Filled: {updated_order.filled_quantity}/{updated_order.quantity}")
    else:
        print("   ❌ Order placement failed")

    # Get positions
    print("\n📦 Get Current Positions:")
    positions = order_executor.get_positions()
    print(f"   Positions: {positions}")

    # Get account balance
    print("\n💵 Get Account Balance:")
    balance = order_executor.get_account_balance()
    for key, value in balance.items():
        print(f"   {key}: {value:,.0f} VND")

    # Get order history
    print("\n📜 Get Order History:")
    history = order_executor.get_order_history(days=7)
    print(f"   Total orders (last 7 days): {len(history)}")
    for order in history[:5]:  # Show first 5
        print(f"   - {order}")


def demo_realtime_streaming():
    """Demonstrate real-time MQTT streaming"""
    print("\n" + "="*60)
    print("4. REAL-TIME PRICE STREAMING (MQTT)")
    print("="*60)

    # Define callback
    def on_price_update(price_data: PriceData):
        print(f"   🔥 {price_data.symbol}: {price_data.price:,.0f} VND "
              f"({price_data.change_percent:+.2f}%) "
              f"Vol: {price_data.volume:,}")

    # Add callback
    price_stream_manager.add_callback(on_price_update)

    # Subscribe to symbols
    symbols = ["VCB", "VHM", "VIC", "FPT", "HPG"]
    print(f"\n📡 Subscribing to: {', '.join(symbols)}")
    price_stream_manager.subscribe(symbols)

    # Connect and start streaming
    print("\n🔌 Connecting to MQTT broker...")
    if price_stream_manager.start():
        print("   ✅ Connected! Streaming prices for 10 seconds...\n")

        import time
        time.sleep(10)

        # Get latest prices
        print("\n📊 Latest Prices:")
        for symbol in symbols:
            latest = price_stream_manager.get_latest_price(symbol)
            if latest:
                print(f"   {symbol}: {latest.price:,.0f} VND ({latest.change_percent:+.2f}%)")

        # Stop streaming
        price_stream_manager.stop()
        print("\n🛑 Stopped streaming")
    else:
        print("   ❌ Failed to connect to MQTT broker")


def demo_dnse_api_client():
    """Demonstrate DNSE API client directly"""
    print("\n" + "="*60)
    print("5. DNSE API CLIENT - TRADING OPERATIONS")
    print("="*60)

    # Place order via API client
    print("\n📝 Place Order (API Client):")
    response = dnse_client.place_order(
        symbol="VCB",
        side="BUY",
        quantity=100,
        price=95000,
        order_type="LO"
    )
    print(f"   Response: {response}")

    if response.get("success"):
        order_id = response.get("orderId")

        # Get order status
        print(f"\n🔍 Get Order Status ({order_id}):")
        status = dnse_client.get_order_status(order_id)
        print(f"   Response: {status}")

        # Cancel order
        print(f"\n❌ Cancel Order ({order_id}):")
        cancel_response = dnse_client.cancel_order(order_id)
        print(f"   Response: {cancel_response}")

    # Get order history
    print("\n📜 Get Order History:")
    history = dnse_client.get_order_history(symbol="VCB")
    print(f"   Response: {history}")


def demo_advanced_apis():
    """Demonstrate advanced APIs"""
    print("\n" + "="*60)
    print("6. ADVANCED APIs")
    print("="*60)

    # Get rights information
    print("\n🎁 Get Stock Rights:")
    rights = dnse_client.get_right_exercise()
    print(f"   Response: {rights}")

    # Get advance payment info
    print("\n💳 Get Advance Payment:")
    advance = dnse_client.get_advance_payment()
    print(f"   Response: {advance}")

    # Get cash statement
    print("\n💵 Get Cash Statement (Last 30 days):")
    from datetime import datetime, timedelta
    to_date = datetime.now().strftime("%Y-%m-%d")
    from_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    statement = dnse_client.get_cash_statement(from_date, to_date)
    print(f"   Response: {statement}")


def main():
    """Main demo function"""
    print("\n" + "="*80)
    print(" "*20 + "🚀 DNSE API INTEGRATION DEMO 🚀")
    print("="*80)

    print("\n📌 Current Configuration:")
    print(f"   Base URL: {dnse_client.base_url}")
    print(f"   Account ID: {dnse_client.account_id}")
    print(f"   Trading Mode: {'PAPER' if order_executor.paper_mode else 'LIVE'}")

    # Run demos
    try:
        demo_market_data()
        demo_account_apis()
        demo_trading_apis()
        demo_dnse_api_client()
        demo_advanced_apis()
        demo_realtime_streaming()

    except KeyboardInterrupt:
        print("\n\n⏸️  Demo interrupted by user")
    except Exception as e:
        logger.error(f"Demo error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "="*80)
    print(" "*25 + "✅ DEMO COMPLETED!")
    print("="*80)

    print("\n📚 API Integration Summary:")
    print("   ✅ Market Data APIs - get_stock_price, get_orderbook, get_market_index")
    print("   ✅ Trading APIs - place_order, cancel_order, modify_order")
    print("   ✅ Account APIs - get_account_balance, get_portfolio")
    print("   ✅ Real-time Streaming - MQTT price updates")
    print("   ✅ Advanced APIs - rights, advance payment, cash statement")
    print("\n💡 Next Steps:")
    print("   1. Set up your API credentials in .env file")
    print("   2. Test with paper trading mode first (TRADING_MODE=paper)")
    print("   3. Switch to live mode when ready (TRADING_MODE=live)")
    print("   4. Check DNSE API documentation: https://hdsd.dnse.com.vn/")
    print()


if __name__ == "__main__":
    main()
