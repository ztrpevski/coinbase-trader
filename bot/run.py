# --- coinbase-trader/bot/run.py
"""
Entry point for the bot.  It simply wires everything together:
  * reads env vars via `bot.config.env`
  * constructs a Coinbase Pro client
  * calls the strategy loop
"""

import time
import sys
import logging
from pathlib import Path

# Import the helper that builds a client from our env vars
from bot import config
from bot import strategy

# Import the official client library
import coinbasepro.client

# Optional – if you want a nicer logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# ------------------------------------------------------------------
# 1️⃣  Build a client with the supplied API credentials
# ------------------------------------------------------------------
client = coinbasepro.client.Client(
    api_key=config.env["COINBASE_API_KEY"],
    api_secret=config.env["COINBASE_API_SECRET"],
    passphrase=config.env["COINBASE_API_PASSPHRASE"],
)

# ------------------------------------------------------------------
# 2️⃣  Run the strategy in a tight loop
# ------------------------------------------------------------------
def _main():
    product_id = config.env["PRODUCT_ID"]
    granularity = int(config.env["GRANULARITY"])

    # Run once immediately, then every `granularity` seconds
    strategy.run_strategy(client, product_id, interval=granularity)

    while True:
        time.sleep(granularity)
        strategy.run_strategy(client, product_id, interval=granularity)


if __name__ == "__main__":
    _main()