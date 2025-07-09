# Use Alpine Linux as the base image for minimal size
FROM alpine:3.20

# Install necessary packages: Python, pip, ffmpeg, curl, and dependencies for Streamlink and yt-dlp
RUN apk add --no-cache \
    python3 \
    py3-pip \
    ffmpeg \
    curl \
    ca-certificates \
    && apk add --no-cache --virtual .build-deps \
    build-base \
    python3-dev \
    && pip3 install --no-cache-dir --break-system-packages \
    streamlink \
    yt-dlp \
    requests \
    && apk del .build-deps \
    && rm -rf /root/.cache

# Install ytarchive binary from GitHub releases (version v0.5.0)
RUN curl -L https://github.com/Kethsar/ytarchive/releases/download/v0.5.0/ytarchive_linux_amd64 -o /app/ytarchive \
    && chmod +x /app/ytarchive

# Set the working directory
WORKDIR /app

# Copy the Python script into the container
COPY monitor_and_download.py /app/monitor_and_download.py

# Define the entrypoint to run the Python script
ENTRYPOINT ["python3", "/app/monitor_and_download.py"]