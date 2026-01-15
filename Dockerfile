FROM python:3.11-slim

# Install system dependencies and Chrome
RUN apt-get update && apt-get install -y \
    wget \
    gnupg \
    unzip \
    && wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add - \
    && sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list' \
    && apt-get update && apt-get install -y \
    google-chrome-stable \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for local data persistence (if needed, though ephemeral on Render free)
RUN mkdir -p admin_data

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/bin/google-chrome

# Expose port
EXPOSE 8080

# Start command
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120"]
