import time
from readerwriterlock import rwlock
from requests.exceptions import RequestException, Timeout
from typing import Dict, List
from threading import Semaphore
from utils.log_config import logger
from utils.scraper_config import config
from ImgSaving import save_image_to_db, save_image_to_file
from scraperBMA import get_cctv_session_id, play_video, get_image
from utils.progress_gui import get_progress_gui
from utils.utils import detect_movement


# Locks for thread safety
alive_sessions_lock = rwlock.RWLockFair()
cctv_fail_lock = rwlock.RWLockFair()
cctv_working_lock = rwlock.RWLockFair()
cctv_unresponsive_lock = rwlock.RWLockFair()
all_cctv_image_list_lock = rwlock.RWLockFair()

# def scrape(camera_id: str, semaphore):
#     with semaphore:
#         logger.info(f"Starting scrape for camera {camera_id}")
#         try:
#             logger.info(f"Getting sessionID for [{camera_id}]")
#             session_id = get_cctv_session_id(camera_id)
#             if not session_id:
#                 logger.error(f"Failed to obtain session ID [{camera_id}]")
#                 return
            
#             time.sleep(config['sleep_after_connect'])

#             play_video(camera_id,session_id)
#             loop = config['img_per_cam']
            
#             for i in range(loop):
#                 if play_video(camera_id, session_id):
#                     logger.info(f"Image saved [{camera_id}] [{i+1}/{loop}]")
#                 else:
#                     logger.error(f"Failed to play video and get image for camera {camera_id} [{i}/{loop}]")
#         finally:
#             get_progress_gui().increment_progress()
#             logger.info(f"Completed scrape for camera {camera_id}")








def create_sessionID(camera_id: str, semaphore: Semaphore, alive_session: Dict[str, str], cctv_fail: List[str]) -> None:
    with semaphore:
        try:
            logger.info(f"[CREATOR] Preparing session for camera {camera_id}")
            session_id = get_cctv_session_id(camera_id)
            if session_id and play_video(camera_id, session_id):
                with alive_sessions_lock.gen_wlock():
                    alive_session[camera_id] = session_id
                logger.info(f"[CREATOR] Session ready for camera {camera_id}")
            else:
                with cctv_fail_lock.gen_wlock():
                    cctv_fail.append(camera_id)
                logger.warning(f"[CREATOR] Added failed camera to list: {camera_id}")
        except Exception as e:
            logger.error(f"[CREATOR] Error creating session for camera {camera_id}: {str(e)}")
            with cctv_fail_lock.gen_wlock():
                cctv_fail.append(camera_id)
        finally:
            get_progress_gui().increment_progress()
            semaphore.release()

def validate_sessionID(camera_id: str, session_id: str, semaphore: Semaphore, working_session: Dict[str, str], unresponsive_session: Dict[str, str], all_cctv_image_list: Dict[str, List[bytes]], max_retries: int = 5, delay: int = 3) -> None:
    with semaphore:
        try:
            for retry in range(max_retries):
                image_data_size = get_image(camera_id, session_id)
                if image_data_size and len(image_data_size) > config['img_size']:
                    logger.info(f"[REFRESHER] Success Step 1/3: CCTV {camera_id} has image size greater than 5120 bytes.")
                    
                    image_list = [image_data_size]
                    
                    success_attempts = 0
                    max_attempts = 0

                    img_per_cam = config['img_per_cam']
                    sa = min(img_per_cam - 1, 5)
                    ma = img_per_cam + (6 if img_per_cam <= 6 else 5)

                    while success_attempts < sa and max_attempts < ma:
                        time.sleep(3)
                        image_data_movement = get_image(camera_id, session_id)
                        if image_data_movement and len(image_data_movement) > config['img_size']:
                            image_list.append(image_data_movement)
                            success_attempts += 1
                        logger.info(f"[REFRESHER] Processing Step 2/3: Collected {len(image_list)}/6 images from CCTV {camera_id}.")
                        max_attempts += 1
                    
                    logger.info(f"[REFRESHER] Success Step 2/3: Collected {len(image_list)} images from CCTV {camera_id}.")

                    if detect_movement(image_list):
                        with cctv_working_lock.gen_wlock():
                            working_session[camera_id] = session_id
                        with all_cctv_image_list_lock.gen_wlock():
                            all_cctv_image_list[camera_id] = image_list
                        logger.info(f"[REFRESHER] Success Step 3/3: CCTV {camera_id} has movement.")
                        return
                    else:
                        logger.warning(f"[REFRESHER] Failed Step 3/3: CCTV {camera_id} has no movement.")
                        break
                else:
                    logger.warning(f"[REFRESHER] Failed Step 1/3: Failed to retrieve valid image from CCTV {camera_id}. Attempt {retry + 1}/{max_retries}.")
                    time.sleep(delay)

            with cctv_unresponsive_lock.gen_wlock():
                unresponsive_session[camera_id] = session_id
            logger.error(f"[REFRESHER] Marked CCTV {camera_id} as unresponsive after {max_retries} failed attempts.")
        except Exception as e:
            logger.error(f"[REFRESHER] Error validating session for camera {camera_id}: {str(e)}")
        finally:
            get_progress_gui().increment_progress()
            semaphore.release()



