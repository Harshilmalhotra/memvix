
FROM python:3.11-slim as builder

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1


RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --prefix=/install --no-cache-dir -r requirements.txt


FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PATH="/usr/local/bin:$PATH"


RUN useradd -m -u 1000 appuser


COPY --from=builder /install /usr/local


COPY . .


RUN chown -R appuser:appuser /app


USER appuser


CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
