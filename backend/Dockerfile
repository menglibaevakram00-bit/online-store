FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt \
    && useradd --create-home --uid 10001 appuser
COPY app/ ./app/
USER appuser

EXPOSE 5000
CMD ["sh", "-c", "flask --app app init-db && exec gunicorn --bind 0.0.0.0:5000 --workers 2 --access-logfile - 'app:create_app()'"]
