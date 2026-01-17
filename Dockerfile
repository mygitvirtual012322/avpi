# Use official Playwright image (includes Python, Browsers, and Deps)
# This fixes the "Build Timeout" by avoiding heavy installations
FROM mcr.microsoft.com/playwright/python:v1.40.0-jammy

# Install Chromium Driver for Selenium support (Platform fallback)
RUN apt-get update && apt-get install -y \
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

# Create directory for local data persistence and correct permissions
RUN mkdir -p admin_data && chmod 777 admin_data

# Environment variables
ENV PORT=8080
ENV PYTHONUNBUFFERED=1
# Selenium will use the system chromium-driver from apt
ENV CHROME_BIN=/usr/bin/chromium
ENV CHROMEDRIVER_PATH=/usr/bin/chromedriver

# Expose port
EXPOSE 8080

# Start command
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "120", "--log-level", "debug"]
