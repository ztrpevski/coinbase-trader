# Coinbase Pro Trading Bot

A tiny, Docker‑friendly trading bot that connects to the Coinbase Pro API and runs a **multi‑indicator strategy** (SMA, RSI, MACD, Bollinger Bands).

> ⚠️ **IMPORTANT** – This bot is *fully open‑source* and **not audited** for production use.  
> Use it in the sandbox, back‑test thoroughly, and keep your API keys safe.

---

## 1. Quick start (Docker)

```bash
# 1. Clone / copy the repo structure above
# 2. Build the Docker image
docker build -t coinbase-trader .

# 3. Run the bot (replace the .env variables first!)
docker run --rm -it -v "$(pwd)/.env:/app/.env:ro" coinbase-trader