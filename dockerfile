# BASE IMAGE FROM DOCKER HUB, this would need to change for production
FROM python:3.11-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends git \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
RUN ls
ENTRYPOINT ["python", "-m", "scripts.monitor"]
