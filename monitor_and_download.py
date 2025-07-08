import os
import time
import subprocess
import requests
import json
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Configuration
TWITCH_CLIENT_ID = os.getenv('TWITCH_CLIENT_ID', 'your_twitch_client_id')
TWITCH_CLIENT_SECRET = os.getenv('TWITCH_CLIENT_SECRET', 'your_twitch_client_secret')
TWITCH_CHANNELS = ['channel1', 'channel2']  # Replace with Twitch channel names
YOUTUBE_CHANNELS = ['@channel1', '@channel2']  # Replace with YouTube channel handles
CHECK_INTERVAL = 300  # Check every 5 minutes
OUTPUT_DIR = '/app/downloads'
QUALITY = 'best'
COOKIES_FILE = '/app/cookies.txt'

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Twitch API token storage
twitch_token = None
token_expiry = 0

def get_twitch_token():
    """Obtain or refresh Twitch API token."""
    global twitch_token, token_expiry
    current_time = time.time()
    
    if twitch_token and current_time < token_expiry:
        return twitch_token
    
    try:
        response = requests.post(
            'https://id.twitch.tv/oauth2/token',
            params={
                'client_id': TWITCH_CLIENT_ID,
                'client_secret': TWITCH_CLIENT_SECRET,
                'grant_type': 'client_credentials'
            }
        )
        response.raise_for_status()
        data = response.json()
        twitch_token = data['access_token']
        token_expiry = current_time + data['expires_in'] - 60  # Buffer of 1 minute
        logging.info("Obtained new Twitch API token.")
        return twitch_token
    except requests.RequestException as e:
        logging.error(f"Failed to get Twitch token: {e}")
        return None

def is_twitch_live(channel):
    """Check if a Twitch channel is live."""
    token = get_twitch_token()
    if not token:
        return False
    
    try:
        response = requests.get(
            f'https://api.twitch.tv/helix/streams?user_login={channel}',
            headers={
                'Client-ID': TWITCH_CLIENT_ID,
                'Authorization': f'Bearer {token}'
            }
        )
        response.raise_for_status()
        data = response.json()
        return len(data['data']) > 0
    except requests.RequestException as e:
        logging.error(f"Error checking Twitch channel {channel}: {e}")
        return False

def get_youtube_live_url(channel):
    """Check if a YouTube channel is live and get the live stream URL using yt-dlp with cookies."""
    try:
        # Use yt-dlp to extract the live stream URL with cookies
        result = subprocess.run(
            ['yt-dlp', '--cookies', COOKIES_FILE, '--get-url', f'https://www.youtube.com/{channel}/live'],
            capture_output=True, text=True
        )
        if result.returncode == 0 and result.stdout.strip():
            live_url = result.stdout.strip()
            logging.info(f"YouTube channel {channel} is live. Stream URL: {live_url}")
            return live_url
        return None
    except subprocess.CalledProcessError as e:
        logging.error(f"Error checking YouTube channel {channel}: {e}")
        return None

def download_twitch_stream(channel):
    """Download Twitch stream using Streamlink."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(OUTPUT_DIR, f'twitch_{channel}_{timestamp}.ts')
    
    try:
        logging.info(f"Starting download for Twitch channel {channel} to {output_file}")
        process = subprocess.Popen(
            ['streamlink', f'twitch.tv/{channel}', QUALITY, '-o', output_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            logging.info(f"Successfully downloaded Twitch stream for {channel}")
        else:
            logging.error(f"Failed to download Twitch stream for {channel}: {stderr}")
    except subprocess.SubprocessError as e:
        logging.error(f"Error downloading Twitch stream for {channel}: {e}")

def download_youtube_stream(channel, live_url):
    """Download YouTube stream using Streamlink with the extracted URL and cookies."""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = os.path.join(OUTPUT_DIR, f'youtube_{channel.replace('@', '')}_{timestamp}.ts')
    
    try:
        logging.info(f"Starting download for YouTube channel {channel} to {output_file}")
        process = subprocess.Popen(
            ['streamlink', '--http-cookies', f'cookies.txt=/app/cookies.txt', live_url, QUALITY, '-o', output_file],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True
        )
        stdout, stderr = process.communicate()
        if process.returncode == 0:
            logging.info(f"Successfully downloaded YouTube stream for {channel}")
        else:
            logging.error(f"Failed to download YouTube stream for {channel}: {stderr}")
    except subprocess.SubprocessError as e:
        logging.error(f"Error downloading YouTube stream for {channel}: {e}")

def main():
    """Monitor and download streams."""
    if not os.path.exists(COOKIES_FILE):
        logging.error(f"Cookies file {COOKIES_FILE} not found. Exiting.")
        return
    
    logging.info("Starting stream monitoring...")
    while True:
        # Check Twitch channels
        for channel in TWITCH_CHANNELS:
            if is_twitch_live(channel):
                download_twitch_stream(channel)
            else:
                logging.info(f"Twitch channel {channel} is not live.")
        
        # Check YouTube channels
        for channel in YOUTUBE_CHANNELS:
            live_url = get_youtube_live_url(channel)
            if live_url:
                download_youtube_stream(channel, live_url)
            else:
                logging.info(f"YouTube channel {channel} is not live.")
        
        # Wait before next check
        logging.info(f"Waiting {CHECK_INTERVAL} seconds before next check...")
        time.sleep(CHECK_INTERVAL)

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        logging.info("Monitoring stopped by user.")
