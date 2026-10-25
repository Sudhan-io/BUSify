FROM python:3.12-slim

# Set working directory
WORKDIR /app

# Install system dependencies for OSRM client and scientific libraries
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy and install pinned Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY backend/ ./backend/
COPY busify.db ./data/busify.db

# Expose backend port
EXPOSE 8000

# Run via Gunicorn with Uvicorn workers for production concurrency
# 2 workers × (2 × CPU cores + 1) is the Gunicorn formula for I/O-bound apps
CMD ["gunicorn", "backend.app.main:app", \
     "--worker-class", "uvicorn.workers.UvicornWorker", \
     "--workers", "4", \
     "--bind", "0.0.0.0:8000", \
     "--timeout", "120", \
     "--log-level", "info", \
     "--access-logfile", "-", \
     "--error-logfile", "-"]
