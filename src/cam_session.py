import requests
import time
from typing import Literal

from log_config import logger
from utils import BASE_URL

# Function to get a session ID for a specific camera
def get_cctv_session_id(camera_id: str, max_retries=3, delay=5) -> str | Literal[False]:
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(BASE_URL, timeout=120)
            response.raise_for_status()
            cookie = response.headers.get('Set-Cookie', '')

            # Check if cookie is present
            if cookie:
                session_id = cookie.split("=")[1].split(";")[0]
                logger.info(f"[{camera_id}] Obtained session ID: {session_id}")
                return session_id
            else:
                logger.warning(f"[{camera_id}] No session cookie found. Retry {retries + 1}/{max_retries}...")
        except requests.RequestException as e:
            logger.error(f"[{camera_id}] Error getting session ID: {e}. Retry {retries + 1}/{max_retries}...")
        
        retries += 1
        time.sleep(delay)

    logger.error(f"[{camera_id}] Failed to obtain session ID after {max_retries} retries.")
    return False

# Function to play video for a camera session
def play_video(camera_id: str, session_id: str, max_retries=3, delay=5) -> bool:
    url = f"{BASE_URL}/PlayVideo.aspx?ID={camera_id}"
    headers = {
        'Referer': f'{BASE_URL}/index.aspx',
        'Cookie': f'ASP.NET_SessionId={session_id};',
        'Priority': 'u=4'
    }
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, headers=headers, timeout=120)  # Added timeout
            response.raise_for_status()
            logger.info(f"[{camera_id}] Playing video for session ID: {session_id}")
            return True  # Exit function if successful
        except requests.RequestException as e:
            retries += 1
            logger.warning(f"[{camera_id}] Error playing video: {e}. Retry {retries}/{max_retries}...")
            time.sleep(delay)
    logger.error(f"[{camera_id}] Failed to play video after {max_retries} retries.")
    return False

# Get image stream from BMA Traffic
# This function will only be use for refreshing the session ID
def get_image(camera_id: int, session_id: str, max_retries=3, delay=5) -> bytes | Literal[False]:
    url = f"{BASE_URL}/show.aspx"
    headers = {
        'Cookie': f'ASP.NET_SessionId={session_id};',
        'Priority': 'u=4'
    }
    retries = 0
    while retries < max_retries:
        try:
            response = requests.get(url, headers=headers, timeout=120)
            response.raise_for_status()
            logger.info(f"[{camera_id}] Image retrieved for session ID: {session_id}")
            return response.content
        except requests.RequestException as e:
            logger.error(f"[{camera_id}] Error getting image: {e}. Retry {retries}/{max_retries}...")
            time.sleep(delay)
    logger.error(f"[{camera_id}] Failed to get image after {max_retries} retries.")  
    return False



