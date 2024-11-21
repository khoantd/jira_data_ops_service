FROM python:3.11-slim

WORKDIR /app

# Install system dependencies and cleanup in same layer
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install dependencies in order of stability
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt \
    && rm -rf /root/.cache/pip/*

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p data

EXPOSE 8080

CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8080"]