FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY wsgi.py run.py ./
COPY app ./app
COPY config ./config
COPY migrations ./migrations
COPY docker/entrypoint.sh ./docker/entrypoint.sh
RUN chmod +x docker/entrypoint.sh \
    && mkdir -p app/static/images app/static/uploads/logos app/static/uploads/resumes app/static/uploads/jobs

ENV FLASK_APP=run.py \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production \
    PORT=5060

EXPOSE 5060

ENTRYPOINT ["sh", "docker/entrypoint.sh"]
