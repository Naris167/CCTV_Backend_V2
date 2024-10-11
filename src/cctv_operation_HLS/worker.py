from utils.log_config import logger
from readerwriterlock import rwlock
from threading import Semaphore
import time
from typing import List, Dict, Tuple
from datetime import datetime

from utils.utils import detect_movement, select_images

# Locks for thread safety
alive_sessions_lock = rwlock.RWLockFair()
cctv_fail_lock = rwlock.RWLockFair()
cctv_working_lock = rwlock.RWLockFair()
cctv_unresponsive_lock = rwlock.RWLockFair()

def scrape_image_HLS(camera_id: str, session_id: str, semaphore: Semaphore, working_session: Dict[str, str], unresponsive_session: Dict[str, str], image_result: List[Tuple[str, List[bytes], datetime]], target_image_count: int, max_retries: int = 5, delay: int = 3) -> None:
    with semaphore:
        try:
            for retry in range(max_retries):
                initial_image = get_image(camera_id, session_id)
                if initial_image and len(initial_image) > 5120:
                    logger.info(f"[SCRAPER] Success Step 1/3: CCTV {camera_id} has image size greater than 5120 bytes.")
                    
                    image_list = [initial_image]
                    collected_images = 1
                    total_attempts = 1
                    
                    min_image_count = max(target_image_count, 7)
                    max_attempts = max(min_image_count * 2, 14)

                    while collected_images < min_image_count and total_attempts < max_attempts:
                        time.sleep(4)
                        new_image = get_image(camera_id, session_id)
                        if new_image and len(new_image) > 5120:
                            image_list.append(new_image)
                            collected_images += 1
                        logger.info(f"[SCRAPER] Processing Step 2/3: Collected {collected_images}/{min_image_count} images from CCTV {camera_id}.")
                        total_attempts += 1
                    
                    logger.info(f"[SCRAPER] Success Step 2/3: Collected {collected_images} images from CCTV {camera_id}.")

                    if detect_movement(image_list):
                        
                        if target_image_count > min_image_count:
                            image_list = select_images(image_list, min_image_count)

                        with cctv_working_lock.gen_wlock():
                            working_session[camera_id] = session_id
                            image_result.append((camera_id, image_list, datetime.now()))
                        logger.info(f"[SCRAPER] Success Step 3/3: CCTV {camera_id} has movement.")
                        return
                    else:
                        logger.warning(f"[SCRAPER] Failed Step 3/3: CCTV {camera_id} has no movement.")
                        break
                else:
                    logger.warning(f"[SCRAPER] Failed Step 1/3: Failed to retrieve valid image from CCTV {camera_id}. Attempt {retry + 1}/{max_retries}.")
                    time.sleep(delay)

            with cctv_unresponsive_lock.gen_wlock():
                unresponsive_session[camera_id] = session_id
            logger.error(f"[SCRAPER] Marked CCTV {camera_id} as unresponsive after {max_retries} failed attempts.")
        except Exception as e:
            logger.error(f"[SCRAPER] Error validating session for camera {camera_id}: {str(e)}")
        finally:
            semaphore.release()