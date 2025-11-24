# Using Python 3.11 for better performance
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies
# We don't need ffmpeg here because the audio is already converted to MP3!
# We just need basic tools.
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Run the service
CMD ["python", "main.py"]