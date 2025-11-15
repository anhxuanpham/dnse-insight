-- Initialize TimescaleDB for time-series data
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Tick data table
CREATE TABLE IF NOT EXISTS tick_data (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    volume BIGINT NOT NULL,
    bid_price DOUBLE PRECISION,
    ask_price DOUBLE PRECISION,
    bid_volume BIGINT,
    ask_volume BIGINT,
    high DOUBLE PRECISION,
    low DOUBLE PRECISION,
    open DOUBLE PRECISION,
    close DOUBLE PRECISION,
    change DOUBLE PRECISION,
    change_percent DOUBLE PRECISION
);

-- Convert to hypertable
SELECT create_hypertable('tick_data', 'time', if_not_exists => TRUE);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_tick_symbol_time ON tick_data (symbol, time DESC);
CREATE INDEX IF NOT EXISTS idx_tick_time ON tick_data (time DESC);

-- Trades table
CREATE TABLE IF NOT EXISTS trades (
    id SERIAL PRIMARY KEY,
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    side TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    price DOUBLE PRECISION NOT NULL,
    order_type TEXT NOT NULL,
    status TEXT NOT NULL,
    pnl DOUBLE PRECISION DEFAULT 0,
    pnl_percent DOUBLE PRECISION DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_trades_time ON trades (time DESC);
CREATE INDEX IF NOT EXISTS idx_trades_symbol ON trades (symbol);

-- Portfolio snapshots
CREATE TABLE IF NOT EXISTS portfolio_snapshots (
    time TIMESTAMPTZ NOT NULL,
    total_value DOUBLE PRECISION NOT NULL,
    cash DOUBLE PRECISION NOT NULL,
    positions_value DOUBLE PRECISION NOT NULL,
    total_pnl DOUBLE PRECISION NOT NULL,
    total_return DOUBLE PRECISION NOT NULL,
    num_positions INTEGER NOT NULL
);

SELECT create_hypertable('portfolio_snapshots', 'time', if_not_exists => TRUE);

-- Scan results table
CREATE TABLE IF NOT EXISTS scan_results (
    time TIMESTAMPTZ NOT NULL,
    symbol TEXT NOT NULL,
    filter_name TEXT NOT NULL,
    priority TEXT NOT NULL,
    message TEXT NOT NULL,
    price DOUBLE PRECISION,
    change_percent DOUBLE PRECISION,
    metadata JSONB
);

SELECT create_hypertable('scan_results', 'time', if_not_exists => TRUE);
CREATE INDEX IF NOT EXISTS idx_scan_symbol ON scan_results (symbol, time DESC);

-- Continuous aggregates for OHLCV
CREATE MATERIALIZED VIEW IF NOT EXISTS ohlcv_1min
WITH (timescaledb.continuous) AS
SELECT
    time_bucket('1 minute', time) AS bucket,
    symbol,
    first(open, time) as open,
    max(high) as high,
    min(low) as low,
    last(close, time) as close,
    sum(volume) as volume
FROM tick_data
GROUP BY bucket, symbol;

-- Refresh policy
SELECT add_continuous_aggregate_policy('ohlcv_1min',
    start_offset => INTERVAL '1 hour',
    end_offset => INTERVAL '1 minute',
    schedule_interval => INTERVAL '1 minute',
    if_not_exists => TRUE
);

-- Data retention (keep 1 year of tick data)
SELECT add_retention_policy('tick_data', INTERVAL '365 days', if_not_exists => TRUE);
