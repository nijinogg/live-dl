# Use Alpine Linux as the base image for minimal size
FROM alpine:3.20

# Install necessary packages: Python, pip, ffmpeg, curl, and dependencies for streamlink and yt-dlp
RUN apk add --no-cache \
    python3 \
    py3-pip \
    ffmpeg \
    curl \
    ca-certificates \
    libffi \
    openssl \
    musl-dev \
    libc-dev \
    gcc \
    && apk add --no-cache --virtual .build-deps \
    build-base \
    python3-dev \
    libffi-dev \
    openssl-dev \
    && pip3 install --no-cache-dir --break-system-packages --verbose \
    streamlink \
    yt-dlp \
    requests \
    && apk del .build-deps \
    && rm -rf /root/.cache

# Ensure /app directory exists and is writable
RUN mkdir -p /app && chmod 755 /app

# Install ytarchive binary from GitHub releases (version v0.5.0) with error handling
RUN curl -L --fail --output /app/ytarchive https://github.com/Kethsar/ytarchive/releases/download/v0.5.0/ytarchive_linux_amd64 \
    || { echo "Failed to download ytarchive from GitHub. Trying Mega mirror..."; \
         curl -L --fail --output /app/ytarchive https://mega.nz/file/JdwgVLKA#1vWcNPm1SziR60LFBe5WnxeYEza0gBOvem5J2FuxIak; } \
    && chmod +x /app/ytarchive

# Set the working directory
WORKDIR /app

# Copy the Python script into the container
COPY monitor_and_download.py /app/monitor_and_download.py

# Define the entrypoint to run the Python script
ENTRYPOINT ["python3", "/app/monitor_and_download.py"]