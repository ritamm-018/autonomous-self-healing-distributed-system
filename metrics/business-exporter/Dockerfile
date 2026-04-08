FROM python:3.9-slim

WORKDIR /app

RUN pip install prometheus-client requests

COPY exporter.py .

CMD ["python", "-u", "exporter.py"]
