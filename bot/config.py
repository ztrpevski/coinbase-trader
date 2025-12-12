# --- coinbase-trader/bot/config.py
"""
Utility module that loads environment variables from a .env file
(and falls back to the process environment).

Usage:

    from bot.config import env

    # e.g.
    api_key = env["COINBASE_API_KEY"]
"""

import os
from pathlib import Path
from typing import Dict

# Load a .env file if present – this is completely optional
try:
    from dotenv import load_dotenv

    _ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
    if _ENV_PATH.exists():
        load_dotenv(dotenv_path=_ENV_PATH)
except Exception:
    # python‑dotenv is not a hard dependency; we silently ignore it
    pass


def _env(key: str, default: str | None = None) -> str:
    """Return an environment variable or a default (raises if missing)."""
    value = os.getenv(key, default)
    if value is None:
        raise RuntimeError(f"Required env variable '{key}' is not set.")
    return value


# Public, typed mapping of all the variables you’ll use in the repo
env: Dict[str, str] = {
    # Coinbase Pro auth
    "COINBASE_API_KEY": _env("COINBASE_API_KEY"),
    "COINBASE_API_SECRET": _env("COINBASE_API_SECRET"),
    "COINBASE_API_PASSPHRASE": _env("COINBASE_API_PASSPHRASE"),

    # Trading configuration
    "PRODUCT_ID": _env("PRODUCT_ID", default="BTC‑USD"),
    "GRANULARITY": _env("GRANULARITY", default="60"),      # seconds
    "HISTORIC_BARS": _env("HISTORIC_BARS", default="240"),  # 4 h of 1‑min data

    # Strategy parameters
    "ORDER_DOLLAR_AMOUNT": _env("ORDER_DOLLAR_AMOUNT", default="100"),
    "SMA_FAST": _env("SMA_FAST", default="20"),
    "SMA_SLOW": _env("SMA_SLOW", default="50"),
    "RSI_PERIOD": _env("RSI_PERIOD", default="14"),
    "RSI_OVERSOLD": _env("RSI_OVERSOLD", default="30"),
    "RSI_OVERBOUGHT": _env("RSI_OVERBOUGHT", default="70"),
    "BB_PERIOD": _env("BB_PERIOD", default="20"),
    "BB_STDDEV": _env("BB_STDDEV", default="2"),
}