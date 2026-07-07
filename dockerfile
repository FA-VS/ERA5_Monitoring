# FROM DOCKER HUB, this needs to change?
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# TODO: Next line is redundant with previous one.
# Temporary approach. Should find more flexible solution eventually.
COPY data/reference /app/data/reference
ENTRYPOINT ["python", "monitor.py"]
