# FedSanitize Threat-Defense Platform — Production Container
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source
COPY . .

# Expose API port
EXPOSE 8000

# Start FastAPI application
CMD ["sh", "-c", "uvicorn backend_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
