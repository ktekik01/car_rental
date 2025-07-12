# syntax=docker/dockerfile:1
FROM python:3.10-slim

# set workdir
WORKDIR /app

# install system deps (e.g. for psycopg2) and Python deps
RUN apt-get update \
    && apt-get install -y --no-install-recommends gcc libpq-dev postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# copy & install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# copy app sources
COPY . .

# expose Flask port
EXPOSE 5000

# set env vars for Flask and to suppress .pyc files
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# entrypoint: wait for the `db` service to be ready, then migrate & serve
CMD ["sh","-c", "\
  echo Waiting for postgres... && \
  until pg_isready -h db -p 5432; do \
    sleep 1; \
  done && \
  flask db upgrade && \
  flask run --host=0.0.0.0 \
"]  
