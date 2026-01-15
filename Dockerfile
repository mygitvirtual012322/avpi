FROM python:3.11-slim

# Install system dependencies and Chromium + Driver
# Chromium from Debian repos is more stable for this environment
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    wget \
    unzip \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create directory for local data persistence
RUN mkdir -p admin_data

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Expose port
EXPOSE 8080

# Start command
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080", "--workers", "2", "--timeout", "120"]
