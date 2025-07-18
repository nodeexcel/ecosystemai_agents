FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libpq-dev gcc curl build-essential \
    && apt-get clean

WORKDIR /app

COPY . /app/

RUN pip install --no-cache-dir -r requirements.txt

RUN alembic upgrade head

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]