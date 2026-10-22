# backend/Dockerfile
FROM python:3.10-slim

# system deps needed for some ML libs (minimal)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential git curl libsndfile1 libgomp1 && rm -rf /var/lib/apt/lists/*

# create app dir
WORKDIR /app

# copy requirements first for caching
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# copy backend source (build context = backend/)
COPY . /app

# expose typical internal port (Fly sets PORT automatically)
EXPOSE 8080

ENV PYTHONUNBUFFERED=1

# run using Fly-provided $PORT
CMD exec gunicorn app.main:app \
    --workers 2 \
    --worker-class uvicorn.workers.UvicornWorker \
    --bind 0.0.0.0:${PORT}
