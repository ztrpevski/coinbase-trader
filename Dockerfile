# --- coinbase‑trader/Dockerfile
FROM python:3.10-slim

WORKDIR /app

# Build‑time deps for compiling optional C extensions
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev \
 && rm -rf /var/lib/apt/lists/*

# Copy deps list
COPY requirements.txt .

# Upgrade pip (optional but keeps us on the latest wheel cache)
RUN pip install --upgrade pip

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Clean up build tools (optional)
RUN apt-get purge -y --auto-remove \
    build-essential \
    python3-dev \
    libffi-dev \
    libssl-dev

# Copy the application
COPY bot/ ./bot

CMD ["python", "-m", "bot.run"]