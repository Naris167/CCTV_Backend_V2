from readerwriterlock import rwlock
from threading import Semaphore
import time
from typing import List, Dict, Tuple
from datetime import datetime

from cctv_operation_BMA.getDataBMA import get_cctv_session_id, play_video, get_image
from utils.utils import detect_movement, select_images_and_datetimes
from utils.log_config import logger


# Locks for thread safety
alive_sessions_lock = rwlock.RWLockFair()
cctv_fail_lock = rwlock.RWLockFair()
cctv_working_lock = rwlock.RWLockFair()
cctv_unresponsive_lock = rwlock.RWLockFair()


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
            semaphore.release()

def validate_sessionID(camera_id: str, session_id: str, semaphore: Semaphore, working_session: Dict[str, str], unresponsive_session: Dict[str, str], max_retries: int = 5, delay: int = 3) -> None:
    with semaphore:
        try:
            for retry in range(max_retries):
                image_data_size = get_image(camera_id, session_id)
                if image_data_size and len(image_data_size) > 5120:
                    logger.info(f"[REFRESHER] Success Step 1/3: CCTV {camera_id} has image size greater than 5120 bytes.")
                    
                    image_list = [image_data_size]
                    success_attempts = 0
                    max_attempts = 0

                    while success_attempts < 5 and max_attempts < 12:
                        time.sleep(3)
                        image_data_movement = get_image(camera_id, session_id)
                        if image_data_movement and len(image_data_movement) > 5120:
                            image_list.append(image_data_movement)
                            success_attempts += 1
                        logger.info(f"[REFRESHER] Processing Step 2/3: Collected {len(image_list)}/6 images from CCTV {camera_id}.")
                        max_attempts += 1
                    
                    logger.info(f"[REFRESHER] Success Step 2/3: Collected {len(image_list)} images from CCTV {camera_id}.")

                    if detect_movement(image_list):
                        with cctv_working_lock.gen_wlock():
                            working_session[camera_id] = session_id
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
            semaphore.release()

def quick_refresh_sessionID(camera_id: str, session_id: str, semaphore: Semaphore) -> None:
    with semaphore:
        try:
            play_video(camera_id, session_id)
            logger.info(f"[QUICK_REFRESH] Successfully refreshed session for camera {camera_id}")
        except Exception as e:
            logger.error(f"[QUICK_REFRESH] Error refreshing session for camera {camera_id}: {str(e)}")
        finally:
            semaphore.release()


def scrape_image_BMA(semaphore: Semaphore,
                     camera_id: str,
                     session_id: str,
                     image_result: List[Tuple[str, Tuple[bytes, ...], Tuple[datetime, ...]]],
                     working_session: Dict[str, str],
                     unresponsive_session: Dict[str, str],
                     target_image_count: int,
                     max_retries: int = 5,
                     delay: int = 3
                     ) -> None:
    with semaphore:
        try:
            for retry in range(max_retries):
                initial_image = get_image(camera_id, session_id)
                if initial_image and len(initial_image) > 5120:
                    logger.info(f"[SCRAPER-BMA] Success Step 1/3: CCTV {camera_id} has image size greater than 5120 bytes.")
                    
                    image_list = [initial_image]
                    image_capture_time = [datetime.now()]
                    collected_images = 1
                    total_attempts = 1
                    
                    min_image_count = max(target_image_count, 7)
                    max_attempts = max(min_image_count * 2, 14)

                    while collected_images < min_image_count and total_attempts < max_attempts:
                        time.sleep(4)
                        new_image = get_image(camera_id, session_id)
                        if new_image and len(new_image) > 5120:
                            image_list.append(new_image)
                            image_capture_time.append(datetime.now())
                            collected_images += 1
                        logger.info(f"[SCRAPER-BMA] Processing Step 2/3: Collected {collected_images}/{min_image_count} images from CCTV {camera_id}.")
                        total_attempts += 1
                    
                    logger.info(f"[SCRAPER-BMA] Success Step 2/3: Collected {collected_images} images from CCTV {camera_id}.")

                    if detect_movement(image_list):
                        
                        if target_image_count < min_image_count:
                            image_list, image_capture_time = select_images_and_datetimes(image_list, image_capture_time, target_image_count)

                        with cctv_working_lock.gen_wlock():
                            working_session[camera_id] = session_id
                            image_result.append((camera_id, tuple(image_list), tuple(image_capture_time)))
                        logger.info(f"[SCRAPER-BMA] Success Step 3/3: CCTV {camera_id} has movement.")
                        return
                    else:
                        logger.warning(f"[SCRAPER-BMA] Failed Step 3/3: CCTV {camera_id} has no movement.")
                        break
                else:
                    logger.warning(f"[SCRAPER-BMA] Failed Step 1/3: Failed to retrieve valid image from CCTV {camera_id}. Attempt {retry + 1}/{max_retries}.")
                    time.sleep(delay)

            with cctv_unresponsive_lock.gen_wlock():
                unresponsive_session[camera_id] = session_id
            logger.error(f"[SCRAPER-BMA] Marked CCTV {camera_id} as unresponsive after {max_retries} failed attempts.")
        except Exception as e:
            logger.error(f"[SCRAPER-BMA] Error validating session for camera {camera_id}: {str(e)}")
        finally:
            semaphore.release()