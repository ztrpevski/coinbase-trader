"""
Multi‑indicator strategy: SMA crossover + RSI + MACD + Bollinger Bands.

Author: YourName
Date:   2025‑12‑12

The strategy executes only when *all* bullish or *all* bearish conditions
are satisfied. Adjust the logic if you want a different trade frequency.
"""

import os
import logging
import math
from datetime import datetime, timedelta
import coinbasepro
from coinbasepro.auth import Auth

# --------------------------------------------------------------------------- #
# Logging – the main application already configures a logger named
# "coinbase-trader.strategy".  If you run this file standalone, add a basic
# handler for demonstration purposes.
# --------------------------------------------------------------------------- #
logger = logging.getLogger("coinbase-trader.strategy")
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] %(levelname)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

# --------------------------------------------------------------------------- #
# Configuration – read from the environment
# --------------------------------------------------------------------------- #
HISTORIC_BARS           = int(os.getenv("HISTORIC_BARS", 300))
SMA_FAST                = int(os.getenv("SMA_FAST", 20))
SMA_SLOW                = int(os.getenv("SMA_SLOW", 50))
RSI_PERIOD              = int(os.getenv("RSI_PERIOD", 14))
RSI_OVERSOLD            = float(os.getenv("RSI_OVERSOLD", 30))
RSI_OVERBOUGHT          = float(os.getenv("RSI_OVERBOUGHT", 70))
MACD_FAST               = int(os.getenv("MACD_FAST", 12))
MACD_SLOW               = int(os.getenv("MACD_SLOW", 26))
MACD_SIGNAL             = int(os.getenv("MACD_SIGNAL", 9))
BB_PERIOD               = int(os.getenv("BB_PERIOD", 20))
BB_STDDEV               = float(os.getenv("BB_STDDEV", 2))
ORDER_DOLLAR_AMOUNT     = float(os.getenv("ORDER_DOLLAR_AMOUNT", 20.0))
FAST_TRADE_ENABLED      = os.getenv("FAST_TRADE_ENABLED", "true").lower() in ("true", "1", "yes")
SLOW_TRADE_ENABLED      = os.getenv("SLOW_TRADE_ENABLED", "true").lower() in ("true", "1", "yes")

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #

def simple_moving_average(data, period):
    """Return SMA for the last 'period' elements of 'data'."""
    if len(data) < period:
        return None
    return sum(data[-period:]) / period

def exponential_moving_average(data, period):
    """Return EMA for the entire list; last element is the current EMA."""
    if len(data) < period:
        return None
    k = 2 / (period + 1)
    ema = data[0]  # seed EMA with the first price
    for price in data[1:]:
        ema = price * k + ema * (1 - k)
    return ema

def calculate_rsi(close_prices, period=RSI_PERIOD):
    """Return RSI of the most recent price."""
    if len(close_prices) < period + 1:
        return None
    deltas = [close_prices[i] - close_prices[i - 1] for i in range(1, len(close_prices))]
    gains = [d for d in deltas if d > 0]
    losses = [-d for d in deltas if d < 0]
    avg_gain = sum(gains[-period:]) / period if gains else 0
    avg_loss = sum(losses[-period:]) / period if losses else 0
    if avg_loss == 0:
        return 100.0
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs))

def calculate_macd(close_prices):
    """Return (macd, signal, histogram) for the latest price."""
    if len(close_prices) < MACD_SLOW:
        return None, None, None
    ema_fast = exponential_moving_average(close_prices, MACD_FAST)
    ema_slow = exponential_moving_average(close_prices, MACD_SLOW)
    macd_line = ema_fast - ema_slow

    # To compute the signal line we need to keep a running list of MACD values.
    # For simplicity, compute it from scratch each time.
    macd_hist = []
    for i in range(MACD_SLOW, len(close_prices)):
        ema_fast_i = exponential_moving_average(close_prices[:i+1], MACD_FAST)
        ema_slow_i = exponential_moving_average(close_prices[:i+1], MACD_SLOW)
        macd_hist.append(ema_fast_i - ema_slow_i)

    signal_line = simple_moving_average(macd_hist, MACD_SIGNAL)
    histogram = macd_line - signal_line if signal_line is not None else None
    return macd_line, signal_line, histogram

def bollinger_bands(close_prices, period=BB_PERIOD, stddev=BB_STDDEV):
    """Return (middle, upper, lower) Bollinger Bands for the latest price."""
    if len(close_prices) < period:
        return None, None, None
    recent = close_prices[-period:]
    mean = sum(recent) / period
    variance = sum((p - mean) ** 2 for p in recent) / period
    std = math.sqrt(variance)
    upper = mean + stddev * std
    lower = mean - stddev * std
    return mean, upper, lower

# --------------------------------------------------------------------------- #
# Core trading routine
# --------------------------------------------------------------------------- #

def run_strategy(client: coinbasepro.client.Client, product_id: str, interval: int = 60):
    """
    Execute the multi‑indicator logic every 'interval' seconds.
    """
    # 1️⃣ Pull historic candles
    now = datetime.utcnow()
    start_time = now - timedelta(seconds=HISTORIC_BARS * interval)
    params = {
        "product_id": product_id,
        "granularity": interval,
        "start": start_time.isoformat(),
        "end": now.isoformat()
    }

    try:
        candles = client.get_product_historic_rates(**params)
    except Exception as exc:
        logger.error(f"Failed to fetch historic rates: {exc}")
        return

    if not candles:
        logger.warning("No candles returned – skipping this tick.")
        return

    # 2️⃣ Extract price & volume arrays
    close_prices = [c[4] for c in candles]   # closing price
    high_prices  = [c[2] for c in candles]   # high
    low_prices   = [c[1] for c in candles]   # low

    # 3️⃣ Compute all indicators
    sma_fast = simple_moving_average(close_prices, SMA_FAST)
    sma_slow = simple_moving_average(close_prices, SMA_SLOW)

    rsi = calculate_rsi(close_prices, RSI_PERIOD)

    macd_line, signal_line, _ = calculate_macd(close_prices)

    bb_mean, bb_upper, bb_lower = bollinger_bands(close_prices, BB_PERIOD, BB_STDDEV)

    # 4️⃣ Current market price (from the last candle)
    latest_candle = candles[-1]
    price = latest_candle[4]  # close

    # 5️⃣ Compile signal flags
    bullish = (
        sma_fast is not None and sma_slow is not None and sma_fast > sma_slow and
        rsi is not None and rsi < RSI_OVERSOLD and
        macd_line is not None and signal_line is not None and macd_line > signal_line and
        bb_lower is not None and price < bb_lower
    )

    bearish = (
        sma_fast is not None and sma_slow is not None and sma_fast < sma_slow and
        rsi is not None and rsi > RSI_OVERBOUGHT and
        macd_line is not None and signal_line is not None and macd_line < signal_line and
        bb_upper is not None and price > bb_upper
    )

    # 6️⃣ Decision & execution
    if bullish and FAST_TRADE_ENABLED:
        side = "buy"
        logger.info(f"ALL bullish signals active – initiating BUY (price={price})")
        _place_limit_order(client, product_id, side, price)
    elif bearish and SLOW_TRADE_ENABLED:
        side = "sell"
        logger.info(f"ALL bearish signals active – initiating SELL (price={price})")
        _place_limit_order(client, product_id, side, price)
    else:
        logger.info("No consensus signal – no trade placed this cycle.")

# --------------------------------------------------------------------------- #
# Order handling helpers
# --------------------------------------------------------------------------- #

def _cancel_stale_orders(client, product_id):
    """Cancel any open GTC orders before placing a new one."""
    try:
        open_orders = client.get_open_orders(product_id)
        for o in open_orders:
            if o.get("time_in_force") == "GTC":
                client.cancel_order(o["id"])
                logger.info(f"Cancelled stale order {o['id']} on {product_id}")
    except Exception as exc:
        logger.error(f"Failed to cancel stale orders: {exc}")

def _place_limit_order(client, product_id, side, price):
    """Create and submit a limit order of size ORDER_DOLLAR_AMOUNT."""
    # 1️⃣  Compute size in coins that equals ORDER_DOLLAR_AMOUNT at current price
    order_size = ORDER_DOLLAR_AMOUNT / float(price)
    order_size = round(order_size, _coin_precision(product_id))  # round to the tick size

    order_payload = {
        "product_id": product_id,
        "side": side,
        "type": "limit",
        "size": str(order_size),
        "price": str(price),          # market‑price limit; tweak for spread if desired
        "time_in_force": "GTC",
    }

    try:
        resp = client.place_order(order_payload)
        logger.info(f"Placed {side.upper()} limit order {resp['id']} "
                    f"(size={order_size} @ {price} USD)")
    except Exception as exc:
        logger.error(f"Order failed: {exc}")

def _coin_precision(product_id):
    """Return the smallest tick size (number of decimal places) for a given product."""
    try:
        details = client.get_product(product_id)
        tick_size = float(details["base_min_size"])
        # Coinbase Pro uses a decimal string like "0.000001" – count trailing zeros
        decimals = len(str(tick_size).split('.')[1])
        return decimals
    except Exception:
        return 6  # fallback

# --------------------------------------------------------------------------- #
# The entry point for the main application
# --------------------------------------------------------------------------- #
# In your `run.py` you can simply do:
#   from strategy import run_strategy
#   run_strategy(client, product_id)
# --------------------------------------------------------------------------- #
