# --- coinbase‑trader/Dockerfile
# Use an official Python runtime – the slim image is lightweight but still has pip
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Install build‑time utilities (for wheel building, if needed)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential && rm -rf /var/lib/apt/lists/*

# Copy the dependency list and install it
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY bot/ ./bot
COPY .env .  # <-- keep your .env next to this Dockerfile (if you use env‑files)

# Tell Docker what port the bot will listen on (only used if you expose a HTTP API)
# EXPOSE 8000  # uncomment if you add a Flask/Starlette UI

# Default command: run the bot
CMD ["python", "-m", "bot.run"]