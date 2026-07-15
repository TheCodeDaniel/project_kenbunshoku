FROM python:3.11-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV STREAM_URL=""
ENV CAMERA_ID="test-cam-1"
ENV CLOUD_INGEST_URL="http://cloud-backend:8000/ingest"

CMD ["python", "detector.py"]
