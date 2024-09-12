from readerwriterlock import rwlock
from threading import Semaphore
import time

from cam_session import get_cctv_session_id, play_video, get_image
from log_config import logger


# Locks for thread safety
alive_sessions_lock = rwlock.RWLockFair()
cctv_fail_lock = rwlock.RWLockFair()



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
def refresh_sessionID(camera_id: str, session_id: str, semaphore: Semaphore, alive_session: dict, offline_session: list, max_retries: int = 5, delay: int = 3) -> None:
    try:
        retries = 0
        success = False

        while retries < max_retries:  # Retry up to 5 times
            image_data = get_image(camera_id, session_id)

            if image_data and len(image_data) > 5120:  # If image size > 5120 bytes
                alive_session[camera_id] = session_id
                logger.info(f"[REFRESHER] Success: CCTV {camera_id} has image size greater than 5120 bytes.")
                success = True
                break  # No need to retry if successful
            else:
                retries += 1
                logger.warning(f"[REFRESHER] Failed to retrieve valid image from CCTV {camera_id}. Attempt {retries + 1}/{max_retries}.")
                time.sleep(delay)
                

        if not success:
            offline_session.append(camera_id)
            logger.error(f"[REFRESHER] Marked CCTV {camera_id} as offline after {retries + 1} failed attempts.")

    finally:
        semaphore.release()  # Release the semaphore once the thread finishes


