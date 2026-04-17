FROM python:3.11-slim

WORKDIR /app

# Install system deps for browser automation
RUN apt-get update && apt-get install -y --no-install-recommends \
    wget gnupg curl \
    chromium chromium-driver \
    fonts-liberation libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdrm2 libgbm1 libgtk-3-0 \
    libnspr4 libnss3 libx11-xcb1 libxcomposite1 \
    libxdamage1 libxfixes3 libxkbcommon0 libxrandr2 \
    xdg-utils \
    && rm -rf /var/lib/apt/lists/*

# Install Python deps
RUN pip install --no-cache-dir \
    flask flask-cors \
    browser-use \
    langchain langchain-ollama \
    playwright \
    Pillow requests \
    playwright install-deps chromium

ENV PYTHONUNBUFFERED=1
ENV CLOUDBROWSER_PORT=9876
ENV CLOUDBROWSER_DATA=/data

# CloudBrowser API server
COPY server.py /app/server.py
RUN chmod +x /app/server.py

EXPOSE 9876

CMD ["python3", "/app/server.py"]
