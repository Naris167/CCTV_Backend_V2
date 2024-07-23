import time
import requests
from requests.exceptions import RequestException, Timeout
from typing import Optional
from datetime import datetime
import os
import re
import ast
from Database import *

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

def save_image_to_db(camera_id: int, image_data: bytes) -> bool:
    add_image(camera_id, image_data, datetime.now())
    return True

def get_image(camera_id: int, session_id: str, save_path: str, save_to_db: bool, img_size: int) -> bool:
    url = f"{BASE_URL}/show.aspx"
    headers = {
        'Cookie': f'ASP.NET_SessionId={session_id};',
        'Priority': 'u=4'
    }
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()

        # Check if the image size is less than a certain size
        if len(response.content) < img_size:
            print(f"Ignoring image from camera {camera_id} as it is smaller than {img_size} bytes")
            return False

        if save_to_db:
            return save_image_to_db(camera_id, response.content)
        else:
            return save_image_to_file(camera_id, response.content, save_path)
    except RequestException as e:
        print(f"Error getting image: {e}")
        return False

def play_video(camera_id: int, session_id: str, sleep: int, save_path: str, save_to_db: bool, img_size: int) -> bool:
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
        return get_image(camera_id, session_id, save_path, save_to_db, img_size)
    except RequestException as e:
        print(f"Error playing video: {e}")
        return False

def scrape(camera_id: int, loop: int, sleep_after_connect: int, sleep_between_download: int, save_path: str, save_to_db: bool, img_size: int):
    print(f"Getting sessionID for [{camera_id}]")
    session_id = get_session_id(BASE_URL)
    if not session_id:
        print(f"Failed to obtain session ID [{camera_id}]")
        return

    print(f"Session ID [{camera_id}]: {session_id}")
    time.sleep(sleep_after_connect)

    print(f"Playing video for [{camera_id}] ...")
    
    for i in range(loop):
        if play_video(camera_id, session_id, sleep_between_download, save_path, save_to_db, img_size):
            print(f"Image saved [{camera_id}] [{i+1}/{loop}]")
        else:
            print(f"Failed to play video and get image for camera {camera_id} [{i}/{loop}]")

def scrape_sequential(camera_ids, loop, sleep_after_connect, sleep_between_download, save_path, save_to_db, img_size, refresh_interval, progress_gui):
    print(f"Getting sessionID for [{camera_ids}]")
    session_id = get_session_id(BASE_URL)
    if not session_id:
        print("Failed to obtain initial session ID")
        return

    for index, camera_id in enumerate(camera_ids):
        if index > 0 and index % refresh_interval == 0:
            session_id = get_session_id(BASE_URL)
            if not session_id:
                print(f"Failed to refresh session ID after {index} images")
                return

        print(f"Session ID [{camera_id}]: {session_id}")
        time.sleep(sleep_after_connect)

        for i in range(loop):
            if play_video(camera_id, session_id, sleep_between_download, save_path, save_to_db, img_size):
                print(f"Image saved [{camera_id}] [{i+1}/{loop}]")
            else:
                print(f"Failed to play video and get image for camera {camera_id} [{i}/{loop}]")
        progress_gui.increment_progress()


def get_cam_ids_from_bma(url = BASE_URL):
    print(f"\n[SCRAPER] Getting camera ID from {url}")
    response = requests.get(url)
    response.raise_for_status()  # Check if the request was successful

    # Find the var locations = [...] data
    data_pattern = re.compile(r"var locations = (\[.*?\]);", re.DOTALL)
    match = data_pattern.search(response.text)

    if match:
        data_string = match.group(1)
        
        # Convert the JavaScript array to a Python list using ast.literal_eval
        json_data = ast.literal_eval(data_string)

        # Process data to use the specified column names
        processed_data = []
        for item in json_data:
            code_match = re.match(r'^[A-Z0-9\-]+', item[1])
            code = code_match.group(0) if code_match else ''
            cam_name = item[1][len(code):].strip() if code else item[1]
            
            processed_item = (
                item[0],       # ID
                code or None,          # Code
                cam_name or None,      # Cam_Name
                item[2] or None,       # Cam_Name_e
                item[3] or None,       # Cam_Location
                item[4] or None,       # Cam_Direction
                item[5] or None,       # Latitude
                item[6] or None,       # Longitude
                item[7] or None,       # IP
                item[8] or None        # Icon
            )
            processed_data.append(processed_item)
        
        print("[SCRAPER] Successfully getting camera ID.\n")
        return processed_data
    else:
        print("[SCRAPER] Error getting camera ID. Defaulting to CCTV List database.\n")
        processed_data = get_cam_ids_from_db()
        return processed_data




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
