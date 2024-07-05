import time
import requests
from requests.exceptions import RequestException
from typing import Optional
from datetime import datetime
import os

""" How this works? 
1. Make connetion to http://www.bmatraffic.com to get the sessionID.
2. Request for the specific video from http://www.bmatraffic.com/PlayVideo.aspx?ID={camera_id} with the camera ID and sessionID.
   This will tells the backend of bmatraffic.com that which camera we want to view
3. Get the streaming images from http://www.bmatraffic.com/show.aspx
   The backend of bmatraffic.com will know that which camera we want to watch based on the camera ID that we send before.
"""

BASE_URL = "http://www.bmatraffic.com"

def get_session_id(url: str) -> Optional[str]:
    try:
        response = requests.get(url)
        response.raise_for_status()
        cookie = response.headers.get('Set-Cookie', '')
        if cookie:
            session_id = cookie.split("=")[1].split(";")[0]
            return session_id
        return None
    except RequestException as e:
        print(f"Error getting session ID: {e}")
        return None


def get_image(camera_id: int, session_id: str, save_path: str) -> bool:
    url = f"{BASE_URL}/show.aspx"
    headers = {
        'Cookie': f'ASP.NET_SessionId={session_id};',
        'Priority': 'u=4'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        # Create filename with camera_id and current date and time
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"camera_{camera_id}_{current_time}.jpg"
        full_path = os.path.join(save_path, filename)
        with open(full_path, 'wb') as f:
            f.write(response.content)
        print(f"Image saved as {full_path}")
        return True
    except RequestException as e:
        print(f"Error getting image: {e}")
        return False


def play_video(camera_id: int, session_id: str, sleep: int, save_path: str) -> bool:
    url = f"{BASE_URL}/PlayVideo.aspx?ID={camera_id}"
    headers = {
        'Referer': f'{BASE_URL}/index.aspx',
        'Cookie': f'ASP.NET_SessionId={session_id};',
        'Priority': 'u=4'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        time.sleep(sleep)  # Give some time for the video to start streaming
        return get_image(camera_id, session_id, save_path)
    except RequestException as e:
        print(f"Error playing video: {e}")
        return False

def scrape(camera_id: int, loop: int, sleep_after_connect: int, sleep_between_download: int, save_path: str):
    session_id = get_session_id(BASE_URL)
    if not session_id:
        print("Failed to obtain session ID")
        return

    print(f"Session ID [{camera_id}] : {session_id}")
    time.sleep(sleep_after_connect)

    print(f"Playing video... [{camera_id}]")
    
    for i in range(loop):
        if play_video(camera_id, session_id, sleep_between_download, save_path):
            print(f"Image saved for camera {camera_id}")
        else:
            print(f"Failed to play video and get image for camera {camera_id}")


### Scrape many cameras in sequential using list
# def scrapes(camera_ids: list, loop: int, save_path: str, sleep_after_connect: int, sleep_between_download: int):
#     session_id = get_session_id(BASE_URL)
#     if not session_id:
#         print("Failed to obtain session ID")
#         return

#     print(f"Session ID: {session_id}")
#     time.sleep(sleep_after_connect)

#     print("Playing video...")
    
#     for camera_id in camera_ids:
#         for i in range(loop):
#             if play_video(camera_id, session_id, sleep_between_download, save_path):
#                 print(f"Image saved for camera {camera_id}")
#             else:
#                 print(f"Failed to play video and get image for camera {camera_id}")


# camera_ids = [7]  # Example list of camera IDs
# loops = 500 # How many images to scrape per camera
# save_path = "./Images/"  # Change this to your desired save path
# sleep_after_connect = 1 # Waiting time after got sessionID
# sleep_between_download = 1 # Waiting time between each image download

# scrapes(camera_ids, loops, save_path, sleep_after_connect, sleep_between_download)
