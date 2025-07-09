FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libpq-dev gcc curl build-essential \
    && apt-get clean

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

CMD ["celery", "-A", "app.services.celery_app", "worker", "-Q", "app2_queue", "--loglevel=info"]