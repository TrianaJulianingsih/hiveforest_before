FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN apt-get update \
    && apt-get install -y gcc libpq-dev curl postgresql-client \
    && pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && mkdir -p /var/log/hiveforest

COPY . .

EXPOSE 8000

CMD ["gunicorn", "cfg.wsgi:application", "--bind", "0.0.0.0:8000"]