FROM python:3.13-slim

WORKDIR /app

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Install production dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code, fixtures, and configuration
COPY src/ ./src/
COPY fixtures/ ./fixtures/

# Create and switch to non-root user for Cloud Run container security
RUN useradd -u 1000 -m nonroot && \
    chown -R nonroot:nonroot /app
USER nonroot

EXPOSE 8080

# Start FastAPI application dynamically binding to Cloud Run $PORT (default 8080)
CMD exec uvicorn src.main:app --host 0.0.0.0 --port ${PORT:-8080}
