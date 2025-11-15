"""
Prometheus Metrics for Monitoring
"""
from prometheus_client import Counter, Histogram, Gauge, generate_latest, REGISTRY
from prometheus_client.core import CollectorRegistry
from fastapi import Response
from loguru import logger

# Create metrics
ORDERS_TOTAL = Counter('trading_orders_total', 'Total number of orders', ['side', 'status'])
ORDERS_PNL = Histogram('trading_orders_pnl', 'Order P&L distribution', buckets=[-100000, -50000, -10000, 0, 10000, 50000, 100000])
PORTFOLIO_VALUE = Gauge('portfolio_total_value', 'Total portfolio value')
PORTFOLIO_PNL = Gauge('portfolio_pnl', 'Portfolio P&L')
ACTIVE_POSITIONS = Gauge('active_positions_count', 'Number of active positions')

PRICE_UPDATES = Counter('price_updates_total', 'Total price updates received', ['symbol'])
SIGNAL_GENERATED = Counter('signals_generated_total', 'Trading signals generated', ['symbol', 'signal_type'])
SCAN_HITS = Counter('scan_hits_total', 'Market scanner hits', ['filter'])

API_REQUESTS = Counter('api_requests_total', 'Total API requests', ['endpoint', 'method'])
API_LATENCY = Histogram('api_request_duration_seconds', 'API request latency', ['endpoint'])

CACHE_HITS = Counter('cache_hits_total', 'Cache hits')
CACHE_MISSES = Counter('cache_misses_total', 'Cache misses')


def get_metrics():
    """Get Prometheus metrics"""
    return Response(content=generate_latest(REGISTRY), media_type="text/plain")
