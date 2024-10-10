import requests
import time
from typing import Literal, Union

from utils.log_config import logger
from utils.utils import BASE_URL
import functools

def retry_request(func):
    @functools.wraps(func)
    def wrapper(*args, max_retries=3, delay=5, **kwargs):
        for retry in range(max_retries):
            try:
                return func(*args, **kwargs)
            except requests.RequestException as e:
                # Extract camera_id from args if it exists
                camera_id = args[0] if args else kwargs.get('camera_id', 'Unknown')
                
                logger.warning(f"Error in {func.__name__} (Camera ID: {camera_id}): {e}. Retry {retry + 1}/{max_retries}...")
                if retry == max_retries - 1:
                    logger.error(f"Failed {func.__name__} (Camera ID: {camera_id}) after {max_retries} retries.")
                    return False
                time.sleep(delay)
    return wrapper

def get_base_session():
    response = requests.get(BASE_URL, timeout=120)
    response.raise_for_status()
    cookie = response.headers.get('Set-Cookie', '')
    return cookie.split("=")[1].split(";")[0] if cookie else None

@retry_request
def get_cctv_session_id(camera_id: str) -> Union[str, Literal[False]]:
    session_id = get_base_session()
    if session_id:
        logger.info(f"[{camera_id}] Obtained session ID: {session_id}")
        return session_id
    logger.warning(f"[{camera_id}] No session cookie found.")
    return False

@retry_request
def play_video(camera_id: str, session_id: str) -> bool:
    url = f"{BASE_URL}/PlayVideo.aspx?ID={camera_id}"
    headers = {
        'Referer': f'{BASE_URL}/index.aspx',
        'Cookie': f'ASP.NET_SessionId={session_id};',
        'Priority': 'u=4'
    }
    response = requests.get(url, headers=headers, timeout=120)
    response.raise_for_status()
    logger.info(f"[{camera_id}] Playing video for session ID: {session_id}")
    return True

@retry_request
def get_image(camera_id: int, session_id: str) -> Union[bytes, Literal[False]]:
    url = f"{BASE_URL}/show.aspx"
    headers = {
        'Cookie': f'ASP.NET_SessionId={session_id};',
        'Priority': 'u=4'
    }
    response = requests.get(url, headers=headers, timeout=120)
    response.raise_for_status()
    logger.info(f"[{camera_id}] Image retrieved for session ID: {session_id}")
    return response.content