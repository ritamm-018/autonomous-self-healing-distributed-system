FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY *.py ./
COPY rules.yaml ./

# Create directories for models
RUN mkdir -p /app/models /app/logs

# Run as non-root user
RUN useradd -m -u 1000 decision && chown -R decision:decision /app
USER decision

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

# Run decision engine
CMD ["python", "-u", "main.py"]
