# Backend-only Dockerfile for Render free tier
FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Install system deps for Playwright
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    libnss3 libnspr4 libatk1.0-0 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxkbcommon0 libxcomposite1 \
    libxdamage1 libxfixes3 libxrandr2 libgbm1 \
    libasound2 libpango-1.0-0 libcairo2 libatspi2.0-0 libgtk-3-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install Playwright chromium
RUN playwright install chromium && playwright install-deps chromium

# Copy app source
COPY app ./app
COPY pyproject.toml .
COPY start.sh .
RUN chmod +x start.sh && sed -i 's/\r$//' start.sh

# Create data directory
RUN mkdir -p /app/data

EXPOSE 10000

HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-10000}/api/v1/health || exit 1

# Use shell script so $PORT env var is evaluated at runtime
CMD ["/bin/sh", "/app/start.sh"]
