import os
import time
import requests
from datetime import datetime
from requests.exceptions import RequestException, Timeout
from typing import Optional

BASE_URL = "http://www.bmatraffic.com"
IMG_SIZE_THRESHOLD = 5120  # If the image size is below this, the session ID is expired

def get_session_id(url: str) -> Optional[str]:
    try:
        response = requests.get(url, timeout=60)  # Timeout set to 60 seconds
        response.raise_for_status()
        cookie = response.headers.get('Set-Cookie', '')
        if cookie:
            session_id = cookie.split("=")[1].split(";")[0]
            return session_id
        return None
    except Timeout:
        print("Error: Request timed out while getting session ID")
        return None
    except RequestException as e:
        print(f"Error getting session ID: {e}")
        return None

def save_image_to_file(camera_id: int, image_data: bytes, save_path: str) -> bool:
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"camera_{camera_id}_{current_time}.jpg"
    full_path = os.path.join(save_path, filename)
    try:
        with open(full_path, 'wb') as f:
            f.write(image_data)
        print(f"Image saved as {full_path}")
        return True
    except IOError as e:
        print(f"Error saving image: {e}")
        return False

def get_image(camera_id: int, session_id: str, save_path: str) -> bool:
    url = f"{BASE_URL}/show.aspx"
    headers = {
        'Cookie': f'ASP.NET_SessionId={session_id};',
        'Priority': 'u=4'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Check if the image size is less than the threshold
        if len(response.content) < IMG_SIZE_THRESHOLD:
            print(f"Session ID expired: image size is smaller than {IMG_SIZE_THRESHOLD} bytes")
            return False

        # Save the image to the file
        return save_image_to_file(camera_id, response.content, save_path)
    except RequestException as e:
        print(f"Error getting image: {e}")
        return False

def play_video(camera_id: int, session_id: str) -> bool:
    url = f"{BASE_URL}/PlayVideo.aspx?ID={camera_id}"
    headers = {
        'Referer': f'{BASE_URL}/index.aspx',
        'Cookie': f'ASP.NET_SessionId={session_id};',
        'Priority': 'u=4'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        time.sleep(5)  # Wait for 5 seconds before fetching the image
        return True
    except RequestException as e:
        print(f"Error playing video: {e}")
        return False

def test_session_id_duration(camera_id: int, save_path: str, check_interval: int = 60):
    # Get session ID only once
    session_id = get_session_id(BASE_URL)
    if not session_id:
        print("Failed to retrieve session ID")
        return
    
    print(f"Session ID retrieved: {session_id}")
    
    # Play video once
    if not play_video(camera_id, session_id):
        print("Failed to play video")
        return
    
    start_time = time.time()
    while True:
        # Periodically scrape the image and save it to the file
        if not get_image(camera_id, session_id, save_path):
            break
        elapsed_time = time.time() - start_time
        print(f"Session ID still valid. Elapsed time: {elapsed_time // 60:.0f} minutes")
        time.sleep(check_interval)

    elapsed_time = time.time() - start_time
    print(f"Session ID expired after {elapsed_time // 60:.0f} minutes")

# Example usage:
camera_id = 7  # Replace with the actual camera ID
save_path = "./images/"  # Replace with your desired save directory
test_session_id_duration(camera_id, save_path, check_interval=60)  # Check every 5 minutes


