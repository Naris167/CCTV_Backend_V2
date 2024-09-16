from readerwriterlock import rwlock
from threading import Semaphore
import time

from cam_session import get_cctv_session_id, play_video, get_image
from cam_movement import detect_movement
from log_config import logger


# Locks for thread safety
alive_sessions_lock = rwlock.RWLockFair()
cctv_fail_lock = rwlock.RWLockFair()
cctv_working_lock = rwlock.RWLockFair()
cctv_unresponsive_lock = rwlock.RWLockFair()



# Function to create session ID
def create_sessionID(camera_id: str, semaphore: Semaphore, alive_session: dict, cctv_fail: list) -> None:
    logger.info(f"[CREATOR] Preparing session for camera {camera_id}")
    try:
        
        # logging.info(f"Preparing session for camera {camera_id}")
        session_id = get_cctv_session_id(camera_id)
        if session_id:
            success = play_video(camera_id, session_id)
            if success:
                with alive_sessions_lock.gen_wlock():
                    alive_session[camera_id] = session_id
                # logging.info(f"Session ready for camera {camera_id}")
            else:
                with cctv_fail_lock.gen_wlock():
                    cctv_fail.append(camera_id)
                logger.warning(f"[CREATOR] Added failed camera (play video) to list: {camera_id}")
        else:
            with cctv_fail_lock.gen_wlock():
                cctv_fail.append(camera_id)
            logger.warning(f"[CREATOR] Added failed camera (session ID) to list: {camera_id}")


        logger.info(f"[CREATOR] Session ready for camera {camera_id}")
    finally:
        semaphore.release()


# Function to refresh session ID
def validate_sessionID(camera_id: str, session_id: str, semaphore: Semaphore, working_session: dict, unresponsive_session: dict, max_retries: int = 5, delay: int = 3) -> None:
    try:
        retries = 0
        success = False

        while retries < max_retries:  # Retry up to 5 times
            image_data_size = get_image(camera_id, session_id)

            if image_data_size and len(image_data_size) > 5120:  # If image size > 5120 bytes
                logger.info(f"[REFRESHER] Success Step 1/3: CCTV {camera_id} has image size greater than 5120 bytes.")
                
                # Collect images for movement detection
                # This part cause infinite loop
                image_list = []
                success_attemps = 0
                max_attemps = 0

                image_list.append(image_data_size)
                time.sleep(1)

                while success_attemps < 4 and max_attemps < 12:
                    # Have to add 5120 bytes filter here too
                    # Have to add the condition to prevent infinite loop if img size always less than 5120 bytes
                    image_data_movement = get_image(camera_id, session_id)
                    if len(image_data_movement) > 5120:
                        image_list.append(image_data_movement)
                        success_attemps += 1
                    logger.info(f"[REFRESHER] Processing Step 2/3: Collected {len(image_list)}/5 images from CCTV {camera_id}.")
                    max_attemps += 1
                    time.sleep(3)
                
                logger.info(f"[REFRESHER] Success Step 2/3: Collected {len(image_list)} images from CCTV {camera_id}.") 

                # Detect movement using the collected images
                # This part cause infinite loop
                if detect_movement(image_list):
                    with cctv_working_lock.gen_wlock():
                        working_session[camera_id] = session_id
                    logger.info(f"[REFRESHER] Success Step 3/3: CCTV {camera_id} has movement.")
                    success = True
                    break
                else:
                    logger.warning(f"[REFRESHER] Failed Step 3/3: CCTV {camera_id} has no movement.")
                    break
            else:
                retries += 1
                logger.warning(f"[REFRESHER] Failed Step 1/3: Failed to retrieve valid image from CCTV {camera_id}. Attempt {retries}/{max_retries}.")
                time.sleep(delay)
                

        if not success:
            with cctv_unresponsive_lock.gen_wlock():
                unresponsive_session[camera_id] = session_id
            logger.error(f"[REFRESHER] Marked CCTV {camera_id} as unresponsive after {retries} failed attempts.")

    finally:
        semaphore.release()  # Release the semaphore once the thread finishes


def quick_refresh_sessionID(camera_id: str, session_id: str, semaphore: Semaphore) -> None:
    try:
        play_video(camera_id, session_id)
    finally:
        semaphore.release() 