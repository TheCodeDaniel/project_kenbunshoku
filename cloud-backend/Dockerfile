FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV QWEN_API_KEY=""
ENV PUSH_ENDPOINT=""

EXPOSE 8000
CMD ["uvicorn", "ingestion_api:app", "--host", "0.0.0.0", "--port", "8000"]
