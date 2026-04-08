FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY predictive-scaler.py .

# Run as non-root user
RUN useradd -m -u 1000 scaler && chown -R scaler:scaler /app
USER scaler

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import sys; sys.exit(0)"

CMD ["python", "-u", "predictive-scaler.py"]
