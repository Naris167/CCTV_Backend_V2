import os
import time
import requests
import logging
from datetime import datetime
from requests.exceptions import RequestException, Timeout
from typing import Optional

BASE_URL = "http://www.bmatraffic.com"
IMG_SIZE_THRESHOLD = 5120  # If the image size is below this, session ID is expired
MAX_ATTEMPTS = 5  # Number of attempts for each iteration to check the image size

# Set up logging
log_directory = "./logs"
os.makedirs(log_directory, exist_ok=True)  # Ensure the directory exists
timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
log_filename = f"{log_directory}/testSessionID_{timestamp}.log"

logging.basicConfig(
    filename=log_filename,
    filemode='w',  # Overwrite the log file each time the script runs
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Also log to the console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
console_handler.setFormatter(console_formatter)
logging.getLogger().addHandler(console_handler)


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
        logging.error("Error: Request timed out while getting session ID")
        return None
    except RequestException as e:
        logging.error(f"Error getting session ID: {e}")
        return None

def save_image_to_file(camera_id: int, image_data: bytes, save_path: str) -> bool:
    current_time = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"camera_{camera_id}_{current_time}.jpg"
    full_path = os.path.join(save_path, filename)
    try:
        with open(full_path, 'wb') as f:
            f.write(image_data)
        logging.info(f"Image saved as {full_path}")
        return True
    except IOError as e:
        logging.error(f"Error saving image: {e}")
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

        # Save the image to the file
        save_image_to_file(camera_id, response.content, save_path)

        # Check if the image size is less than the threshold
        if len(response.content) < IMG_SIZE_THRESHOLD:
            logging.info(f"Image size is smaller than {IMG_SIZE_THRESHOLD} bytes (session might be expired)")
            return False

        logging.info(f"Successfully retrieved image from camera {camera_id}")
        return True
    except RequestException as e:
        logging.error(f"Error getting image: {e}")
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
        logging.error(f"Error playing video: {e}")
        return False

# def test_session_id_duration(camera_id: int, save_path: str, initial_interval: int = 60):
#     # Get session ID only once
#     session_id = get_session_id(BASE_URL)
#     if not session_id:
#         logging.error("Failed to retrieve session ID")
#         return
    
#     logging.info(f"Session ID retrieved: {session_id}")
    
#     # Play video once
#     if not play_video(camera_id, session_id):
#         logging.error("Failed to play video")
#         return
    
#     interval = 1140

#     while True:
#         # Wait for the current interval before fetching images
#         start_time = time.time()
        
#         time.sleep(interval)
        
#         # Calculate elapsed time
#         elapsed_time = time.time() - start_time
#         logging.info(f"Start fetching image after waiting for {int(elapsed_time // 60)} minutes {int(elapsed_time % 60)} seconds.")

#         successful_attempts = 0

#         # Fetch images 5 times
#         for attempt in range(MAX_ATTEMPTS):
#             logging.info(f"Fetching image attempt {attempt + 1}...")
#             if get_image(camera_id, session_id, save_path):
#                 successful_attempts += 1
#                 logging.info("Session ID still working.\n\n")
#                 break

#             time.sleep(2)  # Short pause between attempts to avoid spamming the server

#         # If all 5 attempts failed, consider the session expired
#         if successful_attempts == 0:
#             logging.info("Session ID expired.")
#             break

#         # After fetching images, increment the interval for the next cycle
#         interval += 60  # Increase wait time by 1 minute for the next cycle


def test_session_id_duration(camera_id: int, save_path: str, test_interval: int = 60, play_video_interval: int = 18 * 60, test_duration: int = 24 * 60 * 60):
    # Get session ID only once
    session_id = get_session_id(BASE_URL)
    if not session_id:
        logging.error("Failed to retrieve session ID")
        return
    
    logging.info(f"Session ID retrieved: {session_id}")
    
    start_time = time.time()
    end_time = start_time + test_duration  # Set the test duration to 24 hours

    # Play video every 18 minutes
    while time.time() < end_time:
        # Play video every 18 minutes
        if not play_video(camera_id, session_id):
            logging.error("Failed to play video")
            break
        
        logging.info("Played video to keep session alive.")
        
        # Wait for 18 minutes before playing video again
        time.sleep(play_video_interval)
    
    # Calculate elapsed time in hours, minutes, and seconds
    elapsed_time = time.time() - start_time
    elapsed_hours = int(elapsed_time // 3600)
    elapsed_minutes = int((elapsed_time % 3600) // 60)
    elapsed_seconds = int(elapsed_time % 60)

    # Log the more specific elapsed time
    logging.info(f"{elapsed_hours} hours, {elapsed_minutes} minutes, and {elapsed_seconds} seconds of playing video every 18 minutes completed.")

    
    # Now fetch images to test if session ID is still valid
    logging.info("Starting final session ID validation by fetching images.")
    successful_attempts = 0
    
    for attempt in range(MAX_ATTEMPTS):
        logging.info(f"Fetching image attempt {attempt + 1}...")
        if get_image(camera_id, session_id, save_path):
            successful_attempts += 1
            logging.info(f"Session ID still working after {elapsed_hours} hours, {elapsed_minutes} minutes, and {elapsed_seconds} seconds of playing video.\n\n")
            break
        time.sleep(2)  # Short pause between attempts

    if successful_attempts == 0:
        logging.info(f"Session ID expired after {elapsed_hours} hours, {elapsed_minutes} minutes, and {elapsed_seconds} seconds of playing video every 18 minutes.")
    else:
        logging.info("Session ID successfully kept alive after 24 hours of playing video every 18 minutes.")


# Example usage:
camera_id = 7  # Replace with the actual camera ID
save_path = "./images/"  # Replace with your desired save directory
os.makedirs(save_path, exist_ok=True)  # Ensure the image directory exists
test_session_id_duration(camera_id, save_path)
