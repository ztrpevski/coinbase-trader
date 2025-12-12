# --- coinbase‑trader/Dockerfile
# Base image – lightweight but includes a Python runtime
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# ---------------------------------------------------------------
# 1️⃣  Install build‑time system packages that the Coinbase‑Pro
#     client requires for compiling optional C extensions.
# ---------------------------------------------------------------
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
 && rm -rf /var/lib/apt/lists/*

# ---------------------------------------------------------------
# 2️⃣  Copy the dependency list and install it with pip
# ---------------------------------------------------------------
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---------------------------------------------------------------
# 3️⃣  Clean up build tools (optional but keeps the image small)
# ---------------------------------------------------------------
RUN apt-get purge -y --auto-remove \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev

# ---------------------------------------------------------------
# 4️⃣  Copy the application code
# ---------------------------------------------------------------
COPY bot/ ./bot

# ---------------------------------------------------------------
# 5️⃣  Default command – start the bot
# ---------------------------------------------------------------
CMD ["python", "-m", "bot.run"]