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

# Attempt to pre-download MNIST during image build so runtime startup is instant
RUN python -c "from torchvision import datasets; datasets.MNIST('./data', train=True, download=True); datasets.MNIST('./data', train=False, download=True)" || true

# Copy application source
COPY . .

# Expose API port
EXPOSE 8000

# Start FastAPI application
CMD ["sh", "-c", "python -m uvicorn backend_api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
