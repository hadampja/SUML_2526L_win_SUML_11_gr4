FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install backend dependencies first to maximise Docker layer caching.
COPY app/requirements.txt /app/app/requirements.txt
RUN pip install -r /app/app/requirements.txt

# Copy application code and the precomputed data artefacts the API serves.
COPY app /app/app
COPY data/reporting /app/data/reporting

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request,sys; \
  urllib.request.urlopen('http://localhost:8000/').read(); sys.exit(0)" \
  || exit 1

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
