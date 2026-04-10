FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Copy application code
COPY cybersoc/ ./cybersoc/
COPY openenv.yaml .

# Create non-root user for security
RUN useradd -m -u 1000 cybersoc && chown -R cybersoc:cybersoc /app
USER cybersoc

# Expose port for HF Space
EXPOSE 7860

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:7860/health || exit 1

# Start the OpenEnv server
CMD ["python", "-m", "uvicorn", "cybersoc.server:app", "--host", "0.0.0.0", "--port", "7860"]
